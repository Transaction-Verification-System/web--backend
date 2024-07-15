from django.core.mail import EmailMessage
from django.conf import settings
from django.http import HttpResponse

def send_email(subject, recipient_list,body):
    from_email = settings.DEFAULT_FROM_EMAIL
    reply_to = [settings.DEFAULT_FROM_EMAIL]
    email = EmailMessage(subject, body, from_email, recipient_list,reply_to=reply_to)
    email.send()

