import requests

data = {
    "type": "credit_card",
    "time": 9876543210.0,
    "amount": 2000,
    "v1": 0.2,
    "v2": 0.3,
    "v3": 0.4,
    "v4": 0.5,
    "v5": 0.6,
    "v6": 0.7,
    "v7": 0.8,
    "v8": 0.9,
    "v9": 1.0,
    "v10": 1.1,
    "v11": 1.2,
    "v12": 1.3,
    "v13": 1.4,
    "v14": 1.5,
    "v15": 1.6,
    "v16": 1.7,
    "v17": 1.8,
    "v18": 1.9,
    "v19": 2.0,
    "v20": 2.1,
    "v21": 2.2,
    "v22": 2.3,
    "v23": 2.4,
    "v24": 2.5,
    "v25": 2.6,
    "v26": 2.7,
    "v27": 2.8,
    "v28": 2.9,
    "phone":"1231414",
    "Time": "11:00:00",
    "Date": "2024-07-25",
    "Sender_account": 7777777777,
    "Receiver_account": 8888888888,
    "Amount": 500.50,
    "Payment_currency": "EUR",
    "Received_currency": "USD",
    "Sender_bank_location": "London",
    "Receiver_bank_location": "Toronto",
    "Laundering_type": "Smurfing",
    "Payment_type":"Bank Transfer"
}

def aml_model(data):
    required_fields = ["Time","Date","Payment_type","Sender_account","Receiver_account","Amount","Payment_currency","Received_currency","Sender_bank_location","Receiver_bank_location","Laundering_type"
    ]

    filtered_data = {key: data[key] for key in required_fields if key in data}


    url = 'https://model-backend-qys8.onrender.com/aml/predict'

    response = requests.post(url, json=filtered_data)

    data = response.json()
    print("Status Code:", response.status_code)
    print("Response Body:", response.json())

    print('Status:',data["isLaundering"])

    return data["isLaundering"]

a = aml_model(data)