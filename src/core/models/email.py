from flask_mail import Message
from app.extensions import mail
from src.core.utils.config import get_env_variable

def send_email(subject, recipients,  html):
    msg = Message(
        subject=subject,
        recipients=recipients,
        sender=get_env_variable("MAIL_USERNAME"),
        html=html
    )
    try:
        mail.send(msg)
        return '邮件发送成功！'
    except Exception as e:
        return f'邮件发送失败：{str(e)}'
