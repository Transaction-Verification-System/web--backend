from celery import Celery, shared_task,Task,chain
from celery.exceptions import Retry
import time, logging ,json
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import *
from rest_framework.response import Response
from .rules import calculate_reputation_score,calculate_ecommerce_rules_score,banking_fraud_model_check,aml_model,credit_card_model,ecommerce_model
from .serializers import *
from django.utils import timezone
from .utility import ISocketResponse
from geopy.geocoders import Nominatim
from .email import send_fail_mail
import redis

app = Celery('my_site')
logger = logging.getLogger(__name__)

redis_client = redis.StrictRedis(host='localhost',port=6379,db=0)


def error_list(x,user_id,task_name,type):
    logger.info('I am in Error Log Model.')

    match type:

        case 'banking':
            serializer = ErrorSerializer(data=x)

            x['user'] = user_id
            x['reason'] = f'Transaction Failed due to System Failure in Banking {task_name}.'
            x['timestamp'] = timezone.now()
            x['verified'] = False

            if serializer.is_valid():
                serializer.save(user_id=user_id)
                logger.info(f'Error task saved successfully for Banking task: {task_name}')
            else:
                logger.error(f'Banking Serializer Error: {serializer.errors}')
                logger.error(f'Error task failed to save for Banking task: {task_name}')
                
        case 'credit_card':
            serializer = CreditCardErrorLogSerializer(data=x)

            x['user'] = user_id
            x['reason'] = f'Transaction Failed due to System Failure in Credit Card {task_name}.'
            x['verified'] = False

            if serializer.is_valid():
                serializer.save(user_id=user_id)
                logger.info(f'Error task saved successfully for Credit Card task: {task_name}')
            else:
                logger.error(f'Credit Card Serializer Error: {serializer.errors}')
                logger.error(f'Error task failed to save for Credit Card task: {task_name}')     

        case 'ecom':
            serializer = EcommerceErrorSerializer(data=x)

            x['user'] = user_id
            x['reason'] = f'Transaction Failed due to System Failure in Ecommerce {task_name}.'
            x['verified'] = False

            if serializer.is_valid():
                serializer.save(user_id=user_id)
                logger.info(f'Error task saved successfully for Ecommerce task: {task_name}')
            else:
                logger.error(f'Ecommerce Serializer Error: {serializer.errors}')
                logger.error(f'Error task failed to save for Ecommerce task: {task_name}')           

def handle_retry_and_proceed(task_name, exc, task_instance, x, index, data_list, accepted_data, rejected_data, user_id,type):
    logger.error(f'{task_name} handle failed: {exc}')
    
    if exc:
        error_list(x,user_id,task_name,type)
        
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


def ecommerce_engine(data,user_id):
    try:
        score = calculate_ecommerce_rules_score(data)

        if score < 50:
            logger.info('Ecommerce engine score less than 50')
            return 1
        
        
        else:
            logger.info('Ecommerce Customer data saved.')
            return 0
        
    except Exception as exc:
        logger.error(f'Error in Ecommerce rules_engine: {exc}')
        raise exc

def rules_engine(data,user_id):
    try:
        score = calculate_reputation_score(data)
        if score < 30:
            return 1
        else:
            
            logger.info('Banking Customer data saved.')
            return 0
            
    except Exception as exc:
        logger.error(f'Error in rules_engine: {exc}')
        raise exc

def ai_prediction(data,user_id):
    try:
        result = banking_fraud_model_check(data)
        aml_result = False if aml_model(data)==0 else True

        data['user'] = user_id

        passed_serializer = PassedCustomerDataSerializer(data=data)
        failed_serializer = FailedCustomerDataSerializer(data=data)


        geolocator = Nominatim(user_agent='tivs_app')
        location = geolocator.geocode(data['Sender_bank_location'])

        if location:
            data['latitude'] = location.latitude
            data['longitude'] = location.longitude

        if result == True:
            data['verified'] = False
            data['reason'] = 'Transaction Failed due to Banking AI model prediction.'
            logger.info('Transaction failed due to Banking AI model prediction.')  
            if failed_serializer.is_valid():
                failed_serializer.save(user_id=user_id)
            else:
                errors = failed_serializer.errors
                logger.error(f'Banking Failed Serializer errors: {errors}')
                return {'errors': errors, 'AI Score': result}    
            return 1,False
        else:
            data['aml_risk'] = aml_result
            data['verified'] = True
            data['reason'] = 'Banking Transaction Successful.'
            logger.info('Banking Customer data saved.')
            if passed_serializer.is_valid():
                passed_serializer.save(user_id=user_id)
            else:
                errors = passed_serializer.errors
                logger.error(f'Banking Passed Serializer errors: {errors}')
                return {'errors': errors, 'AI Score': result}    

            return 0,aml_result
        
    except Exception as exc:
        logger.error(f'Error in AI prediction: {exc}')
        raise exc        


def credit_card_prediction(data,user_id):
    try:
        result = credit_card_model(data)
        print('Credit Result:',result)
        aml_result = False if aml_model(data) == 0 else True
        print('AML Result:',aml_result)

        data['user'] = user_id

        passed_serializer =  CreditCardPassedSerializer(data=data)
        failed_serializer = CreditCardFailedSerializer(data=data)


        geolocator = Nominatim(user_agent='tivs_app')
        location = geolocator.geocode(data['Sender_bank_location'])

        if location:
            data['latitude'] = location.latitude
            data['longitude'] = location.longitude

        if result == True:
            data['verified'] = False
            data['reason'] = 'Transaction Failed due to Credit Card AI model prediction.'
            logger.info('Transaction failed due to Credit Card AI model prediction.')  
            if failed_serializer.is_valid():
                failed_serializer.save(user_id=user_id)
            else:
                errors = failed_serializer.errors
                logger.error(f'Credit Card Failed Serializer errors: {errors}')
                return {'errors': errors, 'AI Score': result}    
            return 1,False
        else:
            data['aml_risk'] = aml_result
            data['verified'] = True
            data['reason'] = 'Transaction Successful.'
            logger.info('Customer data saved.')
            if passed_serializer.is_valid():
                passed_serializer.save(user_id=user_id)
            else:
                errors = passed_serializer.errors
                logger.error(f'Credit Credit Passed Serializer errors: {errors}')
                return {'errors': errors, 'AI Score': result}    

            return 0,aml_result
        
    except Exception as exc:
        logger.error(f'Error in Credit Card AI prediction: {exc}')
        raise exc       


def ecommerce_prediction(data,user_id):
    try:
        result = ecommerce_model(data)
        aml_result = False if aml_model(data)==0 else True

        data['user'] = user_id
        print('USer Ecom:',user_id)
        print('USer Data:',data['user'])


        passed_serializer =  EcommercePassedSerializer(data=data)
        failed_serializer = EcommerceFailedSerializer(data=data)

        geolocator = Nominatim(user_agent='tivs_app')
        location = geolocator.geocode(data['Sender_bank_location'])

        if location:
            data['latitude'] = location.latitude
            data['longitude'] = location.longitude

        if result == True:
            data['verified'] = False
            data['reason'] = 'Transaction Failed due to Ecommerce AI model prediction.'
            logger.info('Transaction failed due to Ecommerce AI model prediction.')  
            if failed_serializer.is_valid():
                failed_serializer.save(user_id=user_id)
            else:
                errors = failed_serializer.errors
                logger.error(f'Ecommerce Failed Serializer errors: {errors}')
                return {'errors': errors, 'AI Score': result}    
            return 1,False
        else:
            data['aml_risk'] = aml_result
            data['verified'] = True
            data['reason'] = 'Transaction Successful.'
            logger.info('Ecommerce Customer data saved.')
            if passed_serializer.is_valid():
                passed_serializer.save(user_id=user_id)
            else:
                errors = passed_serializer.errors
                logger.error(f'Ecommerce Passed Serializer errors: {errors}')
                return {'errors': errors, 'AI Score': result}    

            return 0,aml_result
        
    except Exception as exc:
        logger.error(f'Error in AI prediction: {exc}')
        raise exc     
    

@shared_task(queue='queue_1')
def chain_task(x, index, data_list, accepted_data, rejected_data,user_id,type):
    logger.info('Task 1')
    
    match type:
        
        case "banking":
            try:
                transaction_count = redis_client.incr(f'transaction_count_{user_id}')
                mail_transaction_id = 'txn'+str(transaction_count)
                result = blacklist_task(x,user_id)
                logger.info(f'Result: {result}')
                logger.info(f'Index Task1: {index}')

                is_last_transaction = index+1 == len(data_list) 

                if result == 0:
                    send_message_channel(result, 'black_list', transaction_count, accepted_data, data_list, rejected_data,index,is_last_transaction,aml_result=False,type='banking')
                    time.sleep(3)

                    chain(chain_task2.s(x, index, data_list, accepted_data, rejected_data,user_id,type)).apply_async(queue='queue_2')
                if result == 1:
                    rejected_data += 1

                    serializer = FailedCustomerDataSerializer(data=x)
                    x['user'] = user_id
                    reason = 'Transaction Failed due to blacklist check.'
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

                    send_message_channel(result, 'black_list', transaction_count, accepted_data, data_list, rejected_data,index+1,is_last_transaction,aml_result=False,type='banking')
                    time.sleep(3)

                    send_fail_mail(user_id,reason,mail_transaction_id)

                    if index + 1 < len(data_list):
                        next_data = data_list[index + 1]
                        index += 1
                        type = next_data['type']
                        chain(chain_task.s(next_data, index, data_list, accepted_data, rejected_data,user_id,type)).apply_async(queue='queue_1')
                    else:
                        return 'Black List Engine Completed successfully.'
            except Exception as exc:
                logger.error(f'KeyError in chain_task: {exc}')
                handle_retry_and_proceed('BlackList', exc, chain_task, x, index, data_list, accepted_data, rejected_data, user_id,type)
        
        
        case "credit_card":
            try:
                transaction_count = redis_client.incr(f'transaction_count_{user_id}')
                mail_transaction_id = 'txn'+str(transaction_count)
                result = blacklist_task(x,user_id)
                logger.info(f'Result: {result}')
                logger.info(f'Index Task1: {index}')

                is_last_transaction = index+1 == len(data_list) 

                if result == 0:
                    send_message_channel(result, 'black_list', transaction_count, accepted_data, data_list, rejected_data,index,is_last_transaction,aml_result=False,type='credit_card')
                    time.sleep(3)

                    chain(chain_task2.s(x, index, data_list, accepted_data, rejected_data,user_id,type)).apply_async(queue='queue_2')
                if result == 1:
                    rejected_data += 1

                    serializer = CreditCardFailedSerializer(data=x)
                    x['user'] = user_id
                    reason = 'Transaction Failed due to blacklist check.'
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

                    send_message_channel(result, 'black_list', transaction_count, accepted_data, data_list, rejected_data,index+1,is_last_transaction,aml_result=False,type='credit_card')
                    time.sleep(3)

                    send_fail_mail(user_id,reason,mail_transaction_id)

                    if index + 1 < len(data_list):
                        next_data = data_list[index + 1]
                        index += 1
                        type = next_data['type']
                        chain(chain_task.s(next_data, index, data_list, accepted_data, rejected_data,user_id,type)).apply_async(queue='queue_1')
                    else:
                        return 'Black List Engine Completed successfully.'
            except Exception as exc:
                logger.error(f'KeyError in chain_task: {exc}')
                handle_retry_and_proceed('BlackList', exc, chain_task, x, index, data_list, accepted_data, rejected_data, user_id,type)
        
        case 'ecom':
            try:
                transaction_count = redis_client.incr(f'transaction_count_{user_id}')
                mail_transaction_id = 'txn'+str(transaction_count)
                result = blacklist_task(x,user_id)
                logger.info(f'Result: {result}')
                logger.info(f'Index Task1: {index}')

                is_last_transaction = index+1 == len(data_list) 

                if result == 0:
                    send_message_channel(result, 'black_list', transaction_count, accepted_data, data_list, rejected_data,index,is_last_transaction,aml_result=False,type='ecom')
                    time.sleep(3)

                    chain(chain_task2.s(x, index, data_list, accepted_data, rejected_data,user_id,type)).apply_async(queue='queue_2')
                if result == 1:
                    rejected_data += 1

                    serializer = EcommerceFailedSerializer(data=x)
                    x['user'] = user_id
                    reason = 'Transaction Failed due to blacklist check.'
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

                    send_message_channel(result, 'black_list', transaction_count, accepted_data, data_list, rejected_data,index+1,is_last_transaction,aml_result=False,type='ecom')
                    time.sleep(3)

                    send_fail_mail(user_id,reason,mail_transaction_id)

                    if index + 1 < len(data_list):
                        next_data = data_list[index + 1]
                        index += 1
                        type = next_data['type']
                        chain(chain_task.s(next_data, index, data_list, accepted_data, rejected_data,user_id,type)).apply_async(queue='queue_1')
                    else:
                        return 'Black List Engine Completed successfully.'
            except Exception as exc:
                logger.error(f'KeyError in chain_task: {exc}')
                handle_retry_and_proceed('BlackList', exc, chain_task, x, index, data_list, accepted_data, rejected_data, user_id,type)        
@shared_task( queue='queue_2')
def chain_task2(x, index, data_list, accepted_data, rejected_data,user_id,type):
    logger.info('Task 2')

    match type:
        
        case "banking":
            try:
                transaction_count = redis_client.incr(f'transaction_count_{user_id}')
                mail_transaction_id = 'txn'+str(transaction_count)
                result = rules_engine(x,user_id)
                logger.info(f'Index Task2: {index}')
                is_last_transaction = index+1 == len(data_list)
                
                if result == 0:
                    send_message_channel(result, 'rules_engine', transaction_count, accepted_data, data_list, rejected_data,index,is_last_transaction,aml_result=False,type='banking')
                    time.sleep(3)

                    chain(chain_task3.s(x, index, data_list, accepted_data, rejected_data,user_id,type)).apply_async(queue='queue_3')
                
                if result == 1:

                    serializer = FailedCustomerDataSerializer(data=x)
                    x['user'] = user_id
                    reason = 'Transaction Failed due to Reputation List check.'
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

                    send_message_channel(result, 'rules_engine', transaction_count, accepted_data, data_list, rejected_data,index+1,is_last_transaction,aml_result=False,type='banking')
                    time.sleep(3)

                    send_fail_mail(user_id,reason,mail_transaction_id)

                    if index + 1 < len(data_list):
                        next_data = data_list[index + 1]
                        index += 1
                        type = next_data['type']
                        chain(chain_task.s(next_data, index, data_list, accepted_data, rejected_data,user_id,type)).apply_async(queue='queue_1')
                    else:
                        return 'Rules Engine completed successfully.'
            except Exception as exc:
                logger.error(f'KeyError in chain_task: {exc}')
                handle_retry_and_proceed('RulesEngine', exc, chain_task2, x, index, data_list, accepted_data, rejected_data, user_id,type)
        
        
        case "credit_card":
            try:
                transaction_count = redis_client.incr(f'transaction_count_{user_id}')
                mail_transaction_id = 'txn'+str(transaction_count)
                result = 0
                logger.info(f'Index Task2: {index}')
                is_last_transaction = index+1 == len(data_list)
                
                if result == 0:
                    send_message_channel(result, 'rules_engine', transaction_count, accepted_data, data_list, rejected_data,index,is_last_transaction,aml_result=False,type='credit_card')
                    time.sleep(3)

                    chain(chain_task3.s(x, index, data_list, accepted_data, rejected_data,user_id,type)).apply_async(queue='queue_3')
                
            #     if result == 1:

            #         serializer = FailedCustomerDataSerializer(data=x)
            #         x['user'] = user_id
            #         x['reason'] = 'Transaction Failed due to Reputation List check.'
            #         x['verified'] = False

            #         geolocator = Nominatim(user_agent='tivs_app')
            #         location = geolocator.geocode(x['Sender_bank_location'])

            #         if location:
            #             x['latitude'] = location.latitude
            #             x['longitude'] = location.longitude

            #         if serializer.is_valid():
            #             print('Transaction Valid')
            #             serializer.save()
            #             logger.info('Customer data saved.')
            #         else:
            #             logger.info('Invalid Serilializer')
            #             logger.error(f'Serializer errors: {serializer.errors}')

            #         send_message_channel(result, 'rules_engine', transaction_count, accepted_data, data_list, rejected_data,index+1,is_last_transaction,aml_result=False)
            #         time.sleep(3)

            #         send_fail_mail(user_id,x['reason'],mail_transaction_id)

            #         if index + 1 < len(data_list):
            #             next_data = data_list[index + 1]
            #             index += 1
            #             chain(chain_task.s(next_data, index, data_list, accepted_data, rejected_data,user_id,type)).apply_async(queue='queue_1')
            #         else:
            #             return 'Rules Engine completed successfully.'
            except Exception as exc:
                logger.error(f'KeyError in chain_task: {exc}')
                handle_retry_and_proceed('RulesEngine', exc, chain_task2, x, index, data_list, accepted_data, rejected_data, user_id,type)

        
        case "ecom":
            try:
                transaction_count = redis_client.incr(f'transaction_count_{user_id}')
                mail_transaction_id = 'txn'+str(transaction_count)
                result = ecommerce_engine(x,user_id)
                logger.info(f'Index Task2: {index}')
                is_last_transaction = index+1 == len(data_list)
                
                if result == 0:
                    send_message_channel(result, 'rules_engine', transaction_count, accepted_data, data_list, rejected_data,index,is_last_transaction,aml_result=False,type='ecom')
                    time.sleep(3)

                    chain(chain_task3.s(x, index, data_list, accepted_data, rejected_data,user_id,type)).apply_async(queue='queue_3')
                
                if result == 1:

                    serializer = EcommerceFailedSerializer(data=x)
                    x['user'] = user_id
                    reason = 'Transaction Failed due to Reputation List check.'
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
                        logger.info('Ecommerce Customer data saved.')
                    else:
                        logger.info('Invalid Serilializer')
                        logger.error(f'Ecommerce Serializer errors: {serializer.errors}')

                    send_message_channel(result, 'rules_engine', transaction_count, accepted_data, data_list, rejected_data,index+1,is_last_transaction,aml_result=False,type='ecom')
                    time.sleep(3)

                    send_fail_mail(user_id,reason,mail_transaction_id)

                    if index + 1 < len(data_list):
                        next_data = data_list[index + 1]
                        index += 1
                        type = next_data['type']
                        chain(chain_task.s(next_data, index, data_list, accepted_data, rejected_data,user_id,type)).apply_async(queue='queue_1')
                    else:
                        return 'Ecommerce Rules Engine completed successfully.'
            except Exception as exc:
                logger.error(f'KeyError in chain_task: {exc}')
                handle_retry_and_proceed('RulesEngine', exc, chain_task2, x, index, data_list, accepted_data, rejected_data, user_id,type)



@shared_task(queue='queue_3')
def chain_task3(x, index, data_list, accepted_data, rejected_data,user_id,type):
    logger.info('Task 1')

    match type:

        case "banking":

            try:
                transaction_count = redis_client.incr(f'transaction_count_{user_id}')
                mail_transaction_id = 'txn'+str(transaction_count)
                result,aml_result = ai_prediction(x,user_id)
                
                logger.info(f'Index Task3: {index}')
                is_last_transaction = index+1 == len(data_list)
                
                if result == 0:
                    
                    accepted_data += 1
                    send_message_channel(result, 'ai_model', transaction_count, accepted_data, data_list, rejected_data,index+1,is_last_transaction,aml_result,type='banking')
                    time.sleep(3)

                    if index + 1 < len(data_list):
                        next_data = data_list[index + 1]
                        index += 1
                        type = next_data['type']
                        chain(chain_task.s(next_data, index, data_list, accepted_data, rejected_data,user_id,type)).apply_async(queue='queue_1')
                    else:
                        return 'Rules Engine completed successfully.'
                
                if result == 1:
                    rejected_data += 1
                    reason = 'Transaction Failed due to AI check.'

                    send_message_channel(result, 'ai_model', transaction_count, accepted_data, data_list, rejected_data,index+1,is_last_transaction,aml_result,type='banking')
                    time.sleep(3)

                    send_fail_mail(user_id,reason,mail_transaction_id)

                    if index + 1 < len(data_list):
                        next_data = data_list[index + 1]
                        index += 1
                        type = next_data['type']
                        chain(chain_task.s(next_data, index, data_list, accepted_data, rejected_data,user_id,type)).apply_async(queue='queue_1')
                    else:
                        return 'AI Prediction completed successfully.'
            except Exception as exc:
                logger.error(f'KeyError in chain_task: {exc}')
                handle_retry_and_proceed('AI', exc, chain_task3, x, index, data_list, accepted_data, rejected_data, user_id,type)
        

        case "credit_card":
            try:
                transaction_count = redis_client.incr(f'transaction_count_{user_id}')
                mail_transaction_id = 'txn'+str(transaction_count)
                result,aml_result = credit_card_prediction(x,user_id)
                
                logger.info(f'Index Task3: {index}')
                is_last_transaction = index+1 == len(data_list)
                
                if result == 0:
                    
                    accepted_data += 1
                    send_message_channel(result, 'ai_model', transaction_count, accepted_data, data_list, rejected_data,index+1,is_last_transaction,aml_result,type='credit_card')
                    time.sleep(3)

                    if index + 1 < len(data_list):
                        next_data = data_list[index + 1]
                        index += 1
                        type = next_data['type']
                        chain(chain_task.s(next_data, index, data_list, accepted_data, rejected_data,user_id,type)).apply_async(queue='queue_1')
                    else:
                        return 'Credit Card Prediction completed successfully.'
                
                if result == 1:
                    rejected_data += 1
                    reason = 'Transaction Failed due to AI check.'

                    send_message_channel(result, 'ai_model', transaction_count, accepted_data, data_list, rejected_data,index+1,is_last_transaction,aml_result,type='credit_card')
                    time.sleep(3)

                    send_fail_mail(user_id,reason,mail_transaction_id)

                    if index + 1 < len(data_list):
                        next_data = data_list[index + 1]
                        index += 1
                        type = next_data['type']
                        chain(chain_task.s(next_data, index, data_list, accepted_data, rejected_data,user_id,type)).apply_async(queue='queue_1')
                    else:
                        return 'AI Prediction completed successfully.'
            except Exception as exc:
                logger.error(f'KeyError in chain_task: {exc}')
                handle_retry_and_proceed('AI', exc, chain_task3, x, index, data_list, accepted_data, rejected_data, user_id,type)

        case "ecom":
            try:
                transaction_count = redis_client.incr(f'transaction_count_{user_id}')
                mail_transaction_id = 'txn'+str(transaction_count)
                result,aml_result = ecommerce_prediction(x,user_id)
                
                logger.info(f'Index Task3: {index}')
                is_last_transaction = index+1 == len(data_list)
                
                if result == 0:
                    
                    accepted_data += 1
                    send_message_channel(result, 'ai_model', transaction_count, accepted_data, data_list, rejected_data,index+1,is_last_transaction,aml_result,type='ecom')
                    time.sleep(3)

                    if index + 1 < len(data_list):
                        next_data = data_list[index + 1]
                        index += 1
                        type = next_data['type']
                        chain(chain_task.s(next_data, index, data_list, accepted_data, rejected_data,user_id,type)).apply_async(queue='queue_1')
                    else:
                        return 'Ecommerce Prediction completed successfully.'
                
                if result == 1:
                    rejected_data += 1
                    reason = 'Transaction Failed due to AI check.'

                    send_message_channel(result, 'ai_model', transaction_count, accepted_data, data_list, rejected_data,index+1,is_last_transaction,aml_result,type='ecom')
                    time.sleep(3)

                    send_fail_mail(user_id,reason,mail_transaction_id)

                    if index + 1 < len(data_list):
                        next_data = data_list[index + 1]
                        index += 1
                        type = next_data['type']
                        chain(chain_task.s(next_data, index, data_list, accepted_data, rejected_data,user_id,type)).apply_async(queue='queue_1')
                    else:
                        return 'Ecommerce AI Prediction completed successfully.'
            except Exception as exc:
                logger.error(f'KeyError in chain_task: {exc}')
                handle_retry_and_proceed('AI', exc, chain_task3, x, index, data_list, accepted_data, rejected_data, user_id,type)        

def send_message_channel(result,task_name,transaction_count,accepted_data,data_list,rejected_data,index,is_last_transaction=False,aml_result=False,type='banking'):
    
    match type:


        case 'banking':
            if task_name == 'rules_engine':
                response = ISocketResponse(
                    verified=result == 0,
                    message = f'Rules Engine check succeeded in Banking Transaction' if result == 0 else f'Rules Engine check failed due to Banking Weight Calculation Rules.',
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
                    message=f'Black List check succeeded in Banking Transaction' if result == 0 else f'Black List check failed because the user has been blacklisted.',
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
                    message=f'AI check in Banking Transaction succeded' if result == 0 else f'AI check failed due to Banking Fraud Detection Model.',
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

        case 'credit_card':

            if task_name == 'rules_engine':
                response = ISocketResponse(
                    verified=result == 0,
                    message = f'Rules Engine check succeeded in Credit Card' if result == 0 else f'Rules Engine check failed due to Credit Card Weight Calculation Rules.',
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
                    message=f'Black List check succeeded in Credit Card Transaction' if result == 0 else f'Black List check failed because the user has been blacklisted.',
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
                    message=f'AI check in Credit Card Detection succeded' if result == 0 else f'AI check failed due to Credit Card Fraud Detection Model.',
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

        case 'ecom':

            if task_name == 'rules_engine':
                response = ISocketResponse(
                    verified=result == 0,
                    message = f'Rules Engine check succeeded in Ecommerce Fraud Detection' if result == 0 else f'Rules Engine check failed due to Ecommerce Weight Calculation Rules.',
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
                    message=f'Black List check succeeded in Ecommerce Transaction' if result == 0 else f'Black List check failed because the user has been blacklisted.',
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
                    message=f'AI check passed in Ecommerce Transaction Detection' if result == 0 else f'AI check failed due to Ecommerce Fraud Detection Model.',
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

