from datetime import datetime
import time
import os
from flask import Flask, request, jsonify
import requests
from flask_cors import CORS
from app.extensions import mail
from src.core.utils.config import get_env_variable

def create_app():
    app = Flask(__name__,  static_folder='../web/dist', static_url_path='/')
    
    # 启用CORS
    CORS(app)
    
    mail.init_app(app)
    
    from src.api.rss import rss_bp
    app.register_blueprint(rss_bp)
    
    from src.api.email import email_bp
    app.register_blueprint(email_bp)
    
    from src.api.chat import chat_bp
    app.register_blueprint(chat_bp)
    
    from src.api.trigger import trigger_bp
    app.register_blueprint(trigger_bp)
    
    # 注册推荐系统蓝图
    from src.api.recommendation import recommendation_bp
    app.register_blueprint(recommendation_bp)
    
    # 添加 API 代理路由
    @app.route('/api/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
    def api_proxy(path):
        # 本地服务器地址
        server_url = f"http://localhost:5000/{path}"
        
        # 获取完整的查询参数
        query_string = request.query_string.decode('utf-8')
        if query_string:
            server_url += f"?{query_string}"
            
        # 根据请求方法转发请求
        if request.method == 'GET':
            resp = requests.get(server_url, headers=dict(request.headers))
        elif request.method == 'POST':
            resp = requests.post(server_url, json=request.get_json(), headers=dict(request.headers))
        elif request.method == 'PUT':
            resp = requests.put(server_url, json=request.get_json(), headers=dict(request.headers))
        elif request.method == 'DELETE':
            resp = requests.delete(server_url, headers=dict(request.headers))
        else:
            return jsonify({"error": "Method not supported"}), 405
            
        return resp.content, resp.status_code, resp.headers.items()
    
    @app.route('/')
    def index():
        return app.send_static_file('index.html')

    return app

def call_api_on_start():
    if get_env_variable("START_SERVER_SEND_MAIL") == "True" and get_env_variable("DEBUG_MODE") == "False":
        print("开始发送测试邮件")
        url = "http://localhost:5000/mail/send" 
        requests.post(url, json={"recipients":[get_env_variable("MAIL_RECIPIENTS")], "subject":"项目的测试邮件", "body":"<h1>测试邮件</h1>"})

def call_api_timed():
    if get_env_variable("TIMED_SEND_MAIL") == "False": 
        return
    print("定时任务启动")
    while True:
        now = datetime.now()
        url = "http://localhost:5000/trigger" 
        current_time = datetime.now()
        formatted_time = current_time.strftime("%Y-%m-%d %H:%M")
        if now.hour == 9 or now.hour == 18:
            print("开始发送 RSS 邮件 " + formatted_time)
            requests.post(url, json={"modelType": "coze", "recipients":[get_env_variable("MAIL_RECIPIENTS")], "subject":formatted_time + " RSS"})
        time.sleep(1800)

