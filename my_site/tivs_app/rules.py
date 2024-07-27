import requests
import json,os
from dotenv import load_dotenv

load_dotenv

def calculate_reputation_score(data):
    score = 0

    # Positive Indicators
    if int(data["income"]) > 50000:    #higher income results less risk
        score += 10
    if int(data["current_address_months_count"]) > 12:  #fixed address results less risk
        score += 5
    if int(data["prev_address_months_count"]) > 24:
        score += 5
    if 25 < int(data["customer_age"]) < 60:    #less ages risky
        score += 10
    if int(data["velocity_6h"]) < 5:   #less transaction frequency results less risk
        score += 10
    if int(data["velocity_24h"]) < 10:
        score += 10
    if int(data["velocity_4w"]) < 50:
        score += 10
    if data["employment_status"] == "employed":  #good
        score += 10
    if int(data["credit_risk_score"]) > 650:  #more credit score less risk
        score += 20
    if int(data["bank_months_count"]) > 36:   #stable reln with bank 
        score += 10
    if data["phone_home_valid"] == "1":       #valid num
        score += 5
    if data["phone_mobile_valid"] == "1":
        score += 5
    if int(data["device_fraud_count"]) == 0:   
        score += 10
    if int(data["device_distinct_emails_8w"]) < 2: #fewer distinct emails defines single users most of the time
        score += 5

    # Negative Indicators
    if float(data["name_email_similarity"]) > 0.7:  #indicates high similarity and fraud
        score -= 10
    if int(data["current_address_months_count"]) < 6: 
        score -= 5
    if int(data["prev_address_months_count"]) < 12:
        score -= 5
    if int(data["days_since_request"]) < 7: #urgency shows unusual behaviour
        score -= 5
    if int(data["velocity_6h"]) > 10:
        score -= 10
    if int(data["velocity_24h"]) > 20:
        score -= 10
    if int(data["velocity_4w"]) > 100:
        score -= 10
    if int(data["zip_count_4w"]) > 3:  #multiple zip code suspect
        score -= 5
    if int(data["bank_branch_count_8w"]) > 2: #multiple bank branch is suspicious
        score -= 5
    if int(data["date_of_birth_distinct_emails_4w"]) > 1: #multiple distinct email suspicious
        score -= 5
    if data["email_is_free"] == "1":  #free email provider is less trustworthy
        score -= 5
    if data["foreign_request"] == "1": 
        score -= 10

    return score

def calculate_ecommerce_rules_score(data):
    score = 0

    # Positive Indicators
    if data['No_Transactions'] > 50:
        score += 10
    if data['No_Orders'] > 40:
        score += 10
    if data['No_Payments'] > 30:
        score += 10
    if data['Total_transaction_amt'] > 10000:
        score += 20
    if data['No_transactionsFail'] < 5:
        score += 5
    if data['PaymentRegFail'] < 2:
        score += 5
    if data['OrdersFulfilled'] > 50:
        score += 10
    if data['OrdersPending'] < 10:
        score += 5
    if data['OrdersFailed'] < 5:
        score += 5
    if data['Duplicate_IP'] == 0:
        score += 5
    if data['Duplicate_Address'] == 0:
        score += 5

    # Negative Indicators
    if data['No_Transactions'] < 10:
        score -= 10
    if data['No_Orders'] < 10:
        score -= 10
    if data['No_Payments'] < 10:
        score -= 10
    if data['Total_transaction_amt'] < 1000:
        score -= 20
    if data['No_transactionsFail'] > 10:
        score -= 10
    if data['PaymentRegFail'] > 5:
        score -= 10
    if data['OrdersFulfilled'] < 20:
        score -= 10
    if data['OrdersPending'] > 20:
        score -= 5
    if data['OrdersFailed'] > 20:
        score -= 10
    if data['Duplicate_IP'] > 1:
        score -= 5
    if data['Duplicate_Address'] > 1:
        score -= 5
    if data['JCB_16'] > 10:
        score -= 5
    if data['AmericanExp'] > 5:
        score -= 5
    if data['VISA_16'] > 30:
        score -= 5
    if data['Discover'] > 3:
        score -= 5
    if data['Voyager'] > 0:
        score -= 5
    if data['VISA_13'] > 10:
        score -= 5
    if data['Maestro'] > 5:
        score -= 5
    if data['Mastercard'] > 20:
        score -= 5
    if data['DC_CB'] > 3:
        score -= 5
    if data['JCB_15'] > 1:
        score -= 5

    # Additional indicators
    if data.get('verified', False):
        score += 10
    if "suspicious" in data.get('reason', '').lower():
        score -= 10

    return score

def banking_fraud_model_check(data):

    required_fields = [
        "income", "name_email_similarity", "prev_address_months_count",
        "current_address_months_count", "customer_age", "days_since_request",
        "intended_balcon_amount", "payment_type", "zip_count_4w", "velocity_6h",
        "velocity_24h", "velocity_4w", "bank_branch_count_8w",
        "date_of_birth_distinct_emails_4w", "employment_status",
        "credit_risk_score", "email_is_free", "housing_status", "phone_home_valid",
        "phone_mobile_valid", "bank_months_count", "has_other_cards",
        "proposed_credit_limit", "foreign_request", "source",
        "session_length_in_minutes", "device_os", "keep_alive_session",
        "device_distinct_emails_8w", "device_fraud_count", "month"
    ]
    
    filtered_data = {key: data[key] for key in required_fields if key in data}

    url = os.getenv('banking_fraud_url')

    response = requests.post(url, json=filtered_data)

    data = response.json()
    print("Status Code:", response.status_code)
    print("Response Body:", response.json())

    print('Status:',data['isFraud'])

    return data['isFraud']

def aml_model(data):
    required_fields = ["Time","Date","Payment_type","Sender_account","Receiver_account","Amount","Payment_currency","Received_currency","Sender_bank_location","Receiver_bank_location","Laundering_type"
    ]

    filtered_data = {key: data[key] for key in required_fields if key in data}


    url = os.getenv('aml_url')

    response = requests.post(url, json=filtered_data)

    data = response.json()
    print("Status Code:", response.status_code)
    print("Response Body:", response.json())

    print('Status:',data['isLaundering'])

    return data['isLaundering']


def credit_card_model(data):
    required_fields = ["time","amount","v1","v2","v3","v4","v5","v6","v7","v8","v9","v10","v11","v12","v13","v14","v15","v16","v17","v18","v19","v20","v21","v22","v23","v24","v25","v26","v27","v28"]


    filtered_data = {key: data[key] for key in required_fields if key in data}


    url = os.getenv('credit_card_url')



    response = requests.post(url, json=filtered_data)

    data = response.json()
    print("Status Code:", response.status_code)
    print("Response Body:", response.json())

    print('Status:',data["isFraud"])

    return data["isFraud"]

def ecommerce_model(data):
    required_fields = [
    "No_Transactions",
    "No_Orders",
    "No_Payments",
    "Total_transaction_amt",
    "No_transactionsFail",
    "PaymentRegFail",
    "PaypalPayments",
    "ApplePayments",
    "CardPayments",
    "BitcoinPayments",
    "OrdersFulfilled",
    "OrdersPending",
    "OrdersFailed",
    "Trns_fail_order_fulfilled",
    "Duplicate_IP",
    "Duplicate_Address",
    "JCB_16",
    "AmericanExp",
    "VISA_16",
    "Discover",
    "Voyager",
    "VISA_13",
    "Maestro",
    "Mastercard",
    "DC_CB",
    "JCB_15"
]
    filtered_data = {key: data[key] for key in required_fields if key in data}


    url = os.getenv('ecommerce_url')

    response = requests.post(url, json=filtered_data)

    data = response.json()
    print("Status Code:", response.status_code)
    print("Response Body:", response.json())

    print('Status:',data["isFraud"])


    return data["isFraud"]

