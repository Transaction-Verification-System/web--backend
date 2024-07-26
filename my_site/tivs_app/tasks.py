from celery import Celery, shared_task,Task,chain
from celery.exceptions import Retry
import time, logging ,json
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import *
from rest_framework.response import Response
from .rules import calculate_reputation_score,banking_fraud_model_check,aml_model
from .serializers import *
from django.utils import timezone
from .utility import ISocketResponse
from geopy.geocoders import Nominatim
from .email import send_fail_mail
import redis

app = Celery('my_site')
logger = logging.getLogger(__name__)

redis_client = redis.StrictRedis(host='localhost',port=6379,db=0)


def error_list(x,user_id,task_name):
    logger.info('I am in Error Log Model.')
    serializer = ErrorSerializer(data=x)

    x['user'] = user_id
    x['reason'] = f'Transaction Failed due to System Failure in {task_name}.'
    x['timestamp'] = timezone.now()
    x['verified'] = False

    if serializer.is_valid():
        serializer.save(user_id=user_id)
        logger.info(f'Error task saved successfully for task: {task_name}')
    else:
        logger.error(f'Serializer Error: {serializer.errors}')
        logger.error(f'Error task failed to save for task: {task_name}')

def handle_retry_and_proceed(task_name, exc, task_instance, x, index, data_list, accepted_data, rejected_data, user_id, num):
    logger.error(f'{task_name} handle failed: {exc}')
    
    if exc:
        error_list(x,user_id,task_name)
        
        if index + 1 < len(data_list):
            next_data = data_list[index + 1]
            index += 1
            chain(chain_task.s(next_data, index, data_list, accepted_data, rejected_data, user_id)).apply_async(queue='queue_1')
        else:
            return f'{task_name} Engine Completed successfully.'


def blacklist_task(data,user_id):
    try:
        phone = data['phone']
        logger.info('Phone number:', phone)
        
        
        blacklist_check = BlackListModel.objects.filter(phone=phone,user_id = user_id).exists()
        logger.info('Checking blacklist:', blacklist_check) 
        
        if blacklist_check:
            
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
        
        
        if score < 30:
            BlackListModel.objects.create(phone=data['phone'],user_id=user_id)
            logger.info('Transaction failed due to reputation list.')
            return 1
            
        else:
            
            logger.info('Customer data saved.')
            return 0
            
    except Exception as exc:
        logger.error(f'Error in rules_engine: {exc}')
        raise exc

def ai_prediction(data,user_id):
    try:
        result = banking_fraud_model_check(data)

        data['user'] = user_id

        passed_serializer = PassedCustomerDataSerializer(data=data)
        failed_serializer = FailedCustomerDataSerializer(data=data)

        data['user'] = user_id
        data['reason'] = 'Transaction Failed due to blacklist check.'
        data['verified'] = False

        geolocator = Nominatim(user_agent='tivs_app')
        location = geolocator.geocode(data['Sender_bank_location'])

        if location:
            data['latitude'] = location.latitude
            data['longitude'] = location.longitude

        if result == 0:
            data['verified'] = False
            data['reason'] = 'Transaction Failed due to AI model prediction.'
            logger.info('Transaction failed due to AI model prediction.')        

        else:
            data['verified'] = True
            data['reason'] = 'Transaction Successful.'
            logger.info('Customer data saved.')


        if result == False:
            if failed_serializer.is_valid():
                failed_serializer.save(user_id=user_id)
            else:
                errors = failed_serializer.errors
                logger.error(f'Failed Serializer errors: {errors}')
                return {'errors': errors, 'AI Score': result}    
            return 1
        else:
            if passed_serializer.is_valid():
                passed_serializer.save(user_id=user_id)
            else:
                errors = passed_serializer.errors
                logger.error(f'Passed Serializer errors: {errors}')
                return {'errors': errors, 'AI Score': result}    

            return 0
        
    except Exception as exc:
        logger.error(f'Error in AI prediction: {exc}')
        raise exc    

def aml_prediction(data,user_id):
    try:
        result = aml_model(data)

        data['user'] = user_id

        passed_serializer = PassedCustomerDataSerializer(data=data)


        if result == 0:
            data['aml_risk'] = False
            if passed_serializer.is_valid():
                passed_serializer.save(user_id = user_id)
            logger.info('Transaction failed due to AI model prediction.') 

            return True       

        else:
            data['aml_risk'] = True
            if passed_serializer.is_valid():
                passed_serializer.save(user_id = user_id)
            logger.info('Transaction failed due to AI model prediction.') 

            return False   
    except Exception as exc:
        raise exc    




@shared_task(queue='queue_1')
def chain_task(x, index, data_list, accepted_data, rejected_data,user_id):
    logger.info('Task 1')
    
    try:
        # transaction_count = index + 1
        transaction_count = redis_client.incr(f'transaction_count_{user_id}')
        mail_transaction_id = 'txn'+str(transaction_count)
        result = blacklist_task(x,user_id)
        logger.info(f'Result: {result}')
        logger.info(f'Index Task1: {index}')

        is_last_transaction = index+1 == len(data_list) 

        if result == 0:
            send_message_channel(result, 'black_list', transaction_count, accepted_data, data_list, rejected_data,index,is_last_transaction,aml_result=False)
            time.sleep(3)

            chain(chain_task2.s(x, index, data_list, accepted_data, rejected_data,user_id)).apply_async(queue='queue_2')
        if result == 1:
            #notification
            rejected_data += 1

            serializer = FailedCustomerDataSerializer(data=x)
            x['user'] = user_id
            x['reason'] = 'Transaction Failed due to blacklist check.'
            x['verified'] = False

            geolocator = Nominatim(user_agent='tivs_app')
            location = geolocator.geocode(x['Sender_bank_location'])

            if location:
                x['latitude'] = location.latitude
                x['longitude'] = location.longitude

            if serializer.is_valid():
                print('Transaction Valid')
                serializer.save()
                logger.info('Customer data saved.')
            else:
                logger.info('Invalid Serilializer')
                logger.error(f'Serializer errors: {serializer.errors}')

            send_message_channel(result, 'black_list', transaction_count, accepted_data, data_list, rejected_data,index+1,is_last_transaction,aml_result=False)
            time.sleep(3)

            send_fail_mail(user_id,x['reason'],mail_transaction_id)

            if index + 1 < len(data_list):
                next_data = data_list[index + 1]
                index += 1
                chain(chain_task.s(next_data, index, data_list, accepted_data, rejected_data,user_id)).apply_async(queue='queue_1')
            else:
                return 'Black List Engine Completed successfully.'
    except Exception as exc:
        logger.error(f'KeyError in chain_task: {exc}')
        handle_retry_and_proceed('BlackList', exc, chain_task, x, index, data_list, accepted_data, rejected_data, user_id,1)
        # raise exc

@shared_task( queue='queue_2')
def chain_task2(x, index, data_list, accepted_data, rejected_data,user_id):
    logger.info('Task 2')
    try:
        # transaction_count = index + 1
        transaction_count = redis_client.incr(f'transaction_count_{user_id}')
        mail_transaction_id = 'txn'+str(transaction_count)
        result = rules_engine(x,user_id)
        logger.info(f'Index Task2: {index}')
        is_last_transaction = index+1 == len(data_list)
        
        if result == 0:
            send_message_channel(result, 'rules_engine', transaction_count, accepted_data, data_list, rejected_data,index,is_last_transaction,aml_result=False)
            time.sleep(3)

            chain(chain_task3.s(x, index, data_list, accepted_data, rejected_data,user_id)).apply_async(queue='queue_3')
        
        if result == 1:

            serializer = FailedCustomerDataSerializer(data=x)
            x['user'] = user_id
            x['reason'] = 'Transaction Failed due to Reputation List check.'
            x['verified'] = False

            geolocator = Nominatim(user_agent='tivs_app')
            location = geolocator.geocode(x['Sender_bank_location'])

            if location:
                x['latitude'] = location.latitude
                x['longitude'] = location.longitude

            if serializer.is_valid():
                print('Transaction Valid')
                serializer.save()
                logger.info('Customer data saved.')
            else:
                logger.info('Invalid Serilializer')
                logger.error(f'Serializer errors: {serializer.errors}')

            send_message_channel(result, 'rules_engine', transaction_count, accepted_data, data_list, rejected_data,index+1,is_last_transaction,aml_result=False)
            time.sleep(3)

            send_fail_mail(user_id,x['reason'],mail_transaction_id)

            if index + 1 < len(data_list):
                next_data = data_list[index + 1]
                index += 1
                chain(chain_task.s(next_data, index, data_list, accepted_data, rejected_data,user_id)).apply_async(queue='queue_1')
            else:
                return 'Rules Engine completed successfully.'
    except Exception as exc:
        logger.error(f'KeyError in chain_task: {exc}')
        handle_retry_and_proceed('RulesEngine', exc, chain_task2, x, index, data_list, accepted_data, rejected_data, user_id,2)
        # raise exc


@shared_task(queue='queue_3')
def chain_task3(x, index, data_list, accepted_data, rejected_data,user_id):
    logger.info('Task 1')
    try:
        
        # transaction_count = index + 1
        transaction_count = redis_client.incr(f'transaction_count_{user_id}')
        mail_transaction_id = 'txn'+str(transaction_count)
        result = ai_prediction(x,user_id)
        aml_result = aml_prediction(x,user_id)
        logger.info(f'Index Task3: {index}')
        is_last_transaction = index+1 == len(data_list)
        
        if result == 0:
            accepted_data += 1
            send_message_channel(result, 'ai_model', transaction_count, accepted_data, data_list, rejected_data,index+1,is_last_transaction,aml_result)
            time.sleep(3)

            if index + 1 < len(data_list):
                next_data = data_list[index + 1]
                index += 1
                chain(chain_task.s(next_data, index, data_list, accepted_data, rejected_data,user_id)).apply_async(queue='queue_1')
            else:
                return 'Rules Engine completed successfully.'
        
        if result == 1:
            rejected_data += 1

            send_message_channel(result, 'ai_model', transaction_count, accepted_data, data_list, rejected_data,index+1,is_last_transaction,aml_result)
            time.sleep(3)

            send_fail_mail(user_id,x['reason'],mail_transaction_id)

            if index + 1 < len(data_list):
                next_data = data_list[index + 1]
                index += 1
                chain(chain_task.s(next_data, index, data_list, accepted_data, rejected_data,user_id)).apply_async(queue='queue_1')
            else:
                return 'AI Prediction completed successfully.'
    except Exception as exc:
        logger.error(f'KeyError in chain_task: {exc}')
        handle_retry_and_proceed('AI', exc, chain_task3, x, index, data_list, accepted_data, rejected_data, user_id,2)
        # raise exc

def send_message_channel(result,task_name,transaction_count,accepted_data,data_list,rejected_data,index,is_last_transaction=False,aml_result=False):
    if task_name == 'rules_engine':
        response = ISocketResponse(
            verified=result == 0,
            message = f'{task_name} check succeeded' if result == 0 else f'{task_name} check failed due to weight calculation rules.',
            current_transaction_id = "txn"+str(transaction_count), 
            next_transaction_id = 'None' if is_last_transaction else "txn"+str(transaction_count+1), 
            total_transactions_checked = index,  
            total_transactions_left = len(data_list)-index,   
            total_transactions_accepted = accepted_data,  
            total_transactions_rejected = rejected_data,  
            percentage_of_transactions_processed = round((index/len(data_list))*100),  
            aml_risk=aml_result,
            current_process = "ai_model"
        )
    elif task_name == 'black_list':
        response = ISocketResponse(
            verified=result == 0,
            message=f'{task_name} check succeeded' if result == 0 else f'{task_name} check failed due to blaclisted rules.',
            current_transaction_id="txn"+str(transaction_count), 
            next_transaction_id='None' if is_last_transaction else "txn"+str(transaction_count+1), 
            total_transactions_checked = index,  
            total_transactions_left = len(data_list)-index,   
            total_transactions_accepted = accepted_data,  
            total_transactions_rejected = rejected_data,  
            percentage_of_transactions_processed = round((index/len(data_list))*100),  
            aml_risk=aml_result,
            current_process="rules_engine"
        )
    else:
        response = ISocketResponse(
            verified=result == 0,
            message=f'{task_name} check succeeded' if result == 0 else f'{task_name} check failed due to model fraud detection.',
            current_transaction_id="txn"+str(transaction_count), 
            next_transaction_id='None' if is_last_transaction else "txn"+str(transaction_count+1), 
            total_transactions_checked = index,  
            total_transactions_left = len(data_list)-index,  
            total_transactions_accepted = accepted_data,  
            total_transactions_rejected = rejected_data,  
            percentage_of_transactions_processed = round((index/len(data_list))*100),  
            aml_risk = aml_result,
            current_process="black_list"
        )

    logger.info('Response:',response)    

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