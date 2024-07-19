from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth import get_user_model

User = get_user_model()
def send_fail_mail(user,reason,transaction):
    root_user = User.objects.get(id=user)
    subject = f'Failed Transaction Alert - {transaction}'
    message = f'Hello {root_user},\n\nTransaction ID: {transaction}\nFailed Reason: {reason}\n\nPlease review the transaction and take necessary action.'
    from_email = settings.EMAIL_HOST_USER
    recipient_list = [root_user.email]
    send_mail(subject, message, from_email, recipient_list)