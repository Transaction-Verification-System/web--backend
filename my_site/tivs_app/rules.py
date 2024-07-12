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