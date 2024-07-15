from celery import Celery, shared_task,Task,chain
from celery.exceptions import Retry
import time, logging ,json
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import *
from rest_framework.response import Response
from .rules import calculate_reputation_score
from .serializers import *
from django.utils import timezone
from .utility import ISocketResponse

app = Celery('my_site')
logger = logging.getLogger(__name__)


class CustomRetry(Task):
    autoretry_for = (Exception,)
    retry_kwargs = {'max_retries':3}
    retry_backoff = True
    retry_backoff_max = 60
    retry_jitter = True
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        logger.error(f'Task {task_id} failed: {exc}')
        current_queue = self.request.delivery_info.get('routing_key')
        if current_queue == 'queue_1':
            new_queue = 'queue_2'
        elif current_queue == 'queue_2':
            new_queue = 'queue_1'
        else:
            logger.error(f'Unknown Task {task_id} retrying in queue. Skipping.')
            return None

        if self.request.retries < self.retry_kwargs['max_retries']:
            logger.warning(f'Task {task_id} retrying in {new_queue}')
            raise self.retry(exc=exc, queue=new_queue)
        else:
            logger.error(f'Task {task_id} has exceeded max retries. Giving up.')

app.Task = CustomRetry

def error_list(task_name,data,exc,user_id):
    retries = CustomRetry.retry_kwargs['max_retires']
    if retries > 0:
        retries -= 1

        raise CustomRetry.retry(exc=exc)
    else:
        ErrorLogsModel.objects.create(
            task_name=task_name,
            data=data,
            error=str(exc),
            timestamp=timezone.now(),
            user_id=user_id
        )

def blacklist_task(data,user_id):
    try:
        phone = data['phone']
        logger.info('Phone number:', phone)
        
        
        blacklist_instance = BlackListModel.objects.get(phone=phone, user_id=user_id)
        logger.info('Checking blacklist:', blacklist_instance is not None) 
        
        if blacklist_instance:
            data['failed_reason'] = 'Transaction Failed due to blacklist check.'
            
            serializer = CustomerDataSerializer(data=data)

            if serializer.is_valid():
                print('Transaction Valid')
                serializer.save()
                logger.info('Customer data saved.')
            else:
                logger.error(f'Serializer errors: {serializer.errors}')
            
            logger.info('Phone number is blacklisted. Skipping further processing.')
            return 1
        else:
            return 0
    except Exception as exc:
        logger.error(f'Error in blacklist_task: {exc}')
        raise exc

def rules_engine(data,user_id):
    try:
        score = calculate_reputation_score(data)
        data['user'] = user_id
        serializer = CustomerDataSerializer(data=data)
        
        
        if score < 30:
            data['verified'] = False
            data['failed_reason'] = 'Transaction Failed due to reputation score.'
            BlackListModel.objects.create(phone=data['phone'],user_id=user_id)
            logger.info('Transaction failed due to reputation list.')
            
        else:
            data['verified'] = True
            data['failed_reason'] = 'Transaction Successful.'
            logger.info('Customer data saved.')
            
        
        if serializer.is_valid():
            serializer.save(user_id=user_id)
            
            if score < 30:
                return 1
            else:
                return 0
        else:
            errors = serializer.errors
            logger.error(f'Serializer errors: {errors}')
            return {'errors': errors, 'reputation_score': score}
    except Exception as exc:
        logger.error(f'Error in rules_engine: {exc}')
        raise exc



@shared_task(base=CustomRetry, queue='queue_1')
def chain_task(x, index, data_list, accepted_data, rejected_data,user_id):
    try:
        transaction_count = index + 1
        result = blacklist_task(x,user_id)
        logger.info(f'Result: {result}')
        logger.info(f'Index Task1: {index}')

        is_last_transaction = index+1 == len(data_list) 

        if result == 0:
            send_message_channel(result, 'black_list', transaction_count, accepted_data, data_list, rejected_data,index,is_last_transaction)
            chain(chain_task2.s(x, index, data_list, accepted_data, rejected_data,user_id)).apply_async(queue='queue_2')
        if result == 1:
            #notification
            rejected_data += 1
            send_message_channel(result, 'black_list', transaction_count, accepted_data, data_list, rejected_data,index+1,is_last_transaction)
            if index + 1 < len(data_list):
                next_data = data_list[index + 1]
                index += 1
                chain(chain_task.s(next_data, index, data_list, accepted_data, rejected_data,user_id)).apply_async(queue='queue_1')
            else:
                return 'Black List Engine Completed successfully.'
    except Exception as exc:
        logger.error(f'Task 1 failed: {exc}')
        error_list('BlackList', x, exc,user_id)
        raise exc

@shared_task(base=CustomRetry, queue='queue_2')
def chain_task2(x, index, data_list, accepted_data, rejected_data,user_id):
    try:
        transaction_count = index + 1
        result = rules_engine(x,user_id)
        logger.info(f'Index Task2: {index}')
        is_last_transaction = index+1 == len(data_list)
        
        if result == 0:
            accepted_data += 1
            send_message_channel(result, 'rules_engine', transaction_count, accepted_data, data_list, rejected_data,index+1,is_last_transaction)
            if index + 1 < len(data_list):
                next_data = data_list[index + 1]
                index += 1
                chain(chain_task.s(next_data, index, data_list, accepted_data, rejected_data,user_id)).apply_async(queue='queue_1')
            else:
                return 'Rules Engine completed successfully.'
        
        if result == 1:
            #notification
            rejected_data += 1
            send_message_channel(result, 'rules_engine', transaction_count, accepted_data, data_list, rejected_data,index+1,is_last_transaction)
            if index + 1 < len(data_list):
                next_data = data_list[index + 1]
                index += 1
                chain(chain_task.s(next_data, index, data_list, accepted_data, rejected_data,user_id)).apply_async(queue='queue_1')
            else:
                return 'Rules Engine completed successfully.'
    except Exception as exc:
        logger.error(f'Task 2 failed: {exc}')
        error_list('Rules_Engine', x, exc,user_id)
        raise exc
    

def send_message_channel(result,task_name,transaction_count,accepted_data,data_list,rejected_data,index,is_last_transaction=False):
    if task_name == 'rules_engine':
        response = ISocketResponse(
            verified=result == 0,
            message = f'{task_name} check succeeded' if result == 0 else f'{task_name} check failed due to weight calculation rules.',
            current_transaction_id = "txn"+str(transaction_count), 
            next_transaction_id = 'None' if is_last_transaction else "txn"+str(transaction_count+1), 
            total_transactions_checked = index,  
            total_transactions_left = len(data_list)-transaction_count,  
            total_transactions_accepted = accepted_data,  
            total_transactions_rejected = rejected_data,  
            percentage_of_transactions_processed = round((transaction_count/len(data_list))*100),  
            current_process = "rules_engine"
        )
    elif task_name == 'black_list':
        response = ISocketResponse(
            verified=result == 0,
            message=f'{task_name} check succeeded' if result == 0 else f'{task_name} check failed due to blaclisted rules.',
            current_transaction_id="txn"+str(transaction_count), 
            next_transaction_id='None' if is_last_transaction else "txn"+str(transaction_count+1), 
            total_transactions_checked = index,  
            total_transactions_left = len(data_list)-transaction_count,  
            total_transactions_accepted = accepted_data,  
            total_transactions_rejected = rejected_data,  
            percentage_of_transactions_processed = 0 if result == 0 else round((transaction_count/len(data_list))*100),  
            current_process="black_list"
        )
    else:
        response = ISocketResponse(
            verified=result == 0,
            message=f'{task_name} check succeeded' if result == 0 else f'{task_name} check failed due to model fraud detection.',
            current_transaction_id="txn"+str(transaction_count), 
            next_transaction_id='None' if is_last_transaction else "txn"+str(transaction_count+1), 
            total_transactions_checked = index,  
            total_transactions_left = len(data_list)-transaction_count,  
            total_transactions_accepted = accepted_data,  
            total_transactions_rejected = rejected_data,  
            percentage_of_transactions_processed = round((transaction_count/len(data_list))*100),  
            current_process="AI"
        )

    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        'auth_group',
        {
            'type': 'send_message',
            'message': json.dumps(response.to_dict())
        }
    ) 

# @shared_task(base = CustomRetry,queue = 'queue_1')
# def chain_task(x,y,index,data_list):
#     try:
#         add_result = add(x, y)

#         multiply_result = multiply(x, y)

#         send_message_channel(multiply_result, add_result,'Task 1')
#         if add_result and multiply_result:
#             chain(chain_task2.s(x, y,index,data_list)).apply_async(queue='queue_2')
#         else:
#             #Notification
#             if index+1 < len(data_list):
#                 next_data = data_list[index+1] 
#                 index+=1
#                 chain(chain_task.s(next_data['number1'],next_data['number2'],index,data_list)).apply_async(queue='queue_1')  
#             else:
#                 return f'Task 1 completed successfully.'
#         return f'Task 1 completed successfully. Addition:{add_result},MultiplyResult:{multiply_result}'
#     except Exception as exc:
#         logger.error(f'Task 1 failed:{exc}')
#         raise exc 

# @shared_task(base = CustomRetry,queue = 'queue_2')
# def chain_task2(x,y,index,data_list):
#     try:
#         substract_result = substract(x, y)


    #     divide_result = divide(x, y)
    #     send_message_channel(substract_result,divide_result,'Task 2')

    #     if substract_result and divide_result:
    #         if index+1 < len(data_list):  
    #             next_number = data_list[index+1]
    #             index+=1
    #             chain(chain_task.s(next_number['number1'], next_number['number2'],index, data_list)).apply_async(queue='queue_1')
    #         else:
    #             return f'Task 2 completed successfully.'    
    #     else:
    #         #Notification
    #         if index+1 < len(data_list):
    #             next_data = data_list[index+1] 
    #             index+=1
    #             chain(chain_task.s(next_data['number1'],next_data['number2'],index,data_list)).apply_async(queue='queue_1')    
    #         else:
    #             return f'Task 2 completed successfully.'        
    #     return f'Task 2 Completed Successfully.Substraction:{substract_result},Divison:{divide_result}'
        
    # except Exception as exc:
    #     logger.error(f'Task 2 failed:{exc}')
    #     raise exc


# def send_message_channel(result1, result2,task_name):
#     channel_layer = get_channel_layer()
#     if task_name == 'Task 2':
#         async_to_sync(channel_layer.group_send)(
#             'auth_group',
#             {
#                 'type': 'send_message',
#                 'message': {
#                     'Substraction': result1,
#                     'Divison': result2,
#                     'Task':task_name
#                 }
#             }
#         )
#     else:
#         async_to_sync(channel_layer.group_send)(
#             'auth_group',
#             {
#                'type':'send_message',
#                'message': {
#                     'Addition': result2,
#                     'Multiplication': result1,
#                     'Task':task_name
#                 }
#             }
#         )