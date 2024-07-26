from typing import Literal

class ISocketResponse:
    def __init__(self,verified:bool ,message:str , current_transaction_id: str, next_transaction_id: str, total_transactions_checked: int,
                 total_transactions_left: int, total_transactions_accepted: int, total_transactions_rejected: int,
                 percentage_of_transactions_processed: float, current_process: Literal['BlackList', 'RulesEngine', 'AI'],aml_risk:bool):
        self.verified = verified
        self.message = message
        self.current_transaction_id = current_transaction_id
        self.next_transaction_id = next_transaction_id
        self.total_transactions_checked = total_transactions_checked
        self.total_transactions_left = total_transactions_left
        self.total_transactions_accepted = total_transactions_accepted
        self.total_transactions_rejected = total_transactions_rejected
        self.percentage_of_transactions_processed = percentage_of_transactions_processed
        self.current_process = current_process
        self.aml_risk = aml_risk 


    def to_dict(self):
        responseObj = {
            "currentTransactionId": self.current_transaction_id,
            "nextTransactionId": self.next_transaction_id,
            "totalTransactionsChecked": self.total_transactions_checked,
            "totalTransactionsLeft": self.total_transactions_left,
            "totalTransactionsAccepted": self.total_transactions_accepted,
            "totalTransactionsRejected": self.total_transactions_rejected,
            "percentageOfTransactionsProcessed": self.percentage_of_transactions_processed,
            "currentProcess": self.current_process,
            "aml_risk":self.aml_risk
        }
        return {
            "verified": self.verified,
            "message": self.message,
            "response": responseObj 
           
        }