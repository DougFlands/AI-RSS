from datetime import datetime
import time
from flask import Flask
from flask_mail import Mail
import requests
from app.extensions import mail
from src.core.utils.config import getEnvVariable

def create_app():
    app = Flask(__name__)
    
    app.config.from_pyfile("../instance/config.py") 
    mail.init_app(app)
    
    from src.api.rss import rss_bp
    app.register_blueprint(rss_bp)
    
    from src.api.email import email_bp
    app.register_blueprint(email_bp)
    
    from src.api.chat import chat_bp
    app.register_blueprint(chat_bp)
    
    from src.api.trigger import trigger_bp
    app.register_blueprint(trigger_bp)

    return app

def call_api_on_start():
    if getEnvVariable("START_SERVER_SEND_MAIL") == "True" and getEnvVariable("DEBUG_MODE") == "False":
        print("开始发送测试邮件")
        url = "http://localhost:5000/mail/send" 
        requests.post(url, json={"recipients":[getEnvVariable("MAIL_RECIPIENTS")], "subject":"项目的测试邮件", "body":"<h1>测试邮件</h1>"})

def call_api_timed():
    print("定时任务启动")
    while True:
        now = datetime.now()
        url = "http://localhost:5000/trigger" 
        current_time = datetime.now()
        formatted_time = current_time.strftime("%Y-%m-%d %H:%M")
        if now.hour == 9 or now.hour == 18:
            print("开始发送 RSS 邮件 " + formatted_time)
            requests.post(url, json={"modelType": "coze", "recipients":[getEnvVariable("MAIL_RECIPIENTS")], "subject":formatted_time + " RSS"})
        time.sleep(1800)

