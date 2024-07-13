from celery import Celery, shared_task,Task,chain
from celery.exceptions import Retry
import time, logging
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import *
from rest_framework.response import Response
from .rules import calculate_reputation_score
from .serializers import *
from django.utils import timezone

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

def error_list(task_name,data,exc):
    retries = CustomRetry.retry_kwargs['max_retires']
    if retries > 0:
        retries -= 1

        raise CustomRetry.retry(exc=exc)
    else:
        ErrorLogsModel.objects.create(
            task_name=task_name,
            data=data,
            error=str(exc),
            timestamp=timezone.now()
        )


# def add(x, y):
#     time.sleep(5)
#     result = x + y
#     logger.info('Addition Result: %s', result)
#     return result

# def multiply(x, y):
#     time.sleep(5)
#     result = x * y
#     logger.info('Multiplication Result: %s', result)
#     return result

# def substract(x, y):
#     time.sleep(5)
#     result = x - y
#     logger.info('Substraction Result: %s', result)
#     return result

# def divide(x, y):
#     time.sleep(5)
#     result = x / y
#     logger.info('Division Result: %s', result)
#     return result

def blacklist_task(data):
    try:
        phone = data['phone']
        logger.info('Phone number:', phone)
        
        blacklist_check = BlackListModel.objects.filter(phone=phone).exists()
        logger.info('Checking blacklist:', blacklist_check) 
        
        if blacklist_check:
            logger.info('Phone number is blacklisted. Skipping further processing.')
            return 1
        else:
            return 0
    except Exception as exc:
        logger.error(f'Error in blacklist_task: {exc}')
        raise exc

def rules_engine(data):
    try:
        score = calculate_reputation_score(data)
        serializer = CustomerDataSerializer(data=data)
        
        if serializer.is_valid():
            if score < 30:
                BlackListModel.objects.create(phone=data['phone'])
                logger.info('Transaction failed due to reputation list.')
                return 1
            else:
                serializer.save()
                logger.info('Customer data saved.')
                return 0
        else:
            errors = serializer.errors
            logger.error(f'Serializer errors: {errors}')
            return {'errors': errors, 'reputation_score': score}
    except Exception as exc:
        logger.error(f'Error in rules_engine: {exc}')
        raise exc



@shared_task(base = CustomRetry,queue = 'queue_1')
def chain_task(x,index,data_list):
    try:
        transaction_count = index+1
        result = blacklist_task(x)
        print('Result:',result)

        send_message_channel(result,'BlackList',transaction_count)
        if result == 0:
            chain(chain_task2.s(x,index,data_list)).apply_async(queue='queue_2')   
        if result == 1:
            #notification
            if index+1 < len(data_list):
                next_data = data_list[index+1] 
                index+=1
                chain(chain_task.s(next_data,index,data_list)).apply_async(queue='queue_1')  
            else:
                return 'Black List Engine Completed sucessfully.'
    except Exception as exc:
        logger.error(f'Task 1 failed:{exc}')
        error_list('BlackList',x,exc)
        raise exc

@shared_task(base = CustomRetry,queue = 'queue_2')
def chain_task2(x, index, data_list):
    try:
        transaction_count = index+1
        result = rules_engine(x)
        send_message_channel(result, 'RulesEngine',transaction_count)

        if result == 0:
            if index + 1 < len(data_list):
                next_data = data_list[index + 1]
                index += 1
                chain(chain_task.s(next_data, index, data_list)).apply_async(queue='queue_1')
            else:
                return 'Rules Engine completed successfully.'
        
        if result == 1:
            # notification
            if index + 1 < len(data_list):
                next_data = data_list[index + 1]
                index += 1
                chain(chain_task.s(next_data, index, data_list)).apply_async(queue='queue_1')
            else:
                return 'Rules Engine completed successfully.'
    
    except Exception as exc:
        logger.error(f'Task 2 failed: {exc}')
        error_list('Rules_Engine', x, exc)
        raise exc
    

def send_message_channel(result,task_name,transaction_count):
    channel_layer = get_channel_layer()
    if task_name == 'RulesEngine':
        async_to_sync(channel_layer.group_send)(
            'auth_group',
            {
                'type': 'send_message',
                'message': {
                    'Rules Engine Check': result,
                    'Task':task_name,
                    'Transaction id':transaction_count
                }
            }
        )

    elif task_name == 'BlackList':
        async_to_sync(channel_layer.group_send)(
            'auth_group',
            {
                'type':'send_message',
                'message': {
                    'Black List Check': result,
                    'Task': task_name,
                    'Transaction id':transaction_count
                }
            }
        )    
    else:
        async_to_sync(channel_layer.group_send)(
            'auth_group',
            {
               'type':'send_message',
               'message': {
                    'Model Check': result,
                    'Task':task_name
                }
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