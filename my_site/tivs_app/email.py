from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth import get_user_model
from django.template.loader import render_to_string

User = get_user_model()
def send_fail_mail(user,reason,transaction):
    root_user = User.objects.get(id=user)
    subject = f'Failed Transaction Alert - {transaction}'
    print('Reason:',reason)
    statement = f'{reason}' 
    # message = f'Hello {root_user},\n\nTransaction ID: {transaction}\nFailed Reason: {reason}\n\nPlease review the transaction and take necessary action.'
    from_email = settings.EMAIL_HOST_USER
    recipient_list = [root_user.email]

    html_message = render_to_string('tivs_app/email.html', {
        'user': root_user,
        'statement': statement,
        'transaction': transaction
    })
    send_mail(subject, '', from_email, recipient_list, html_message=html_message)