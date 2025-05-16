from datetime import datetime, timedelta
import time
import os
import hashlib
from flask import Flask, request, jsonify, send_from_directory
import requests
from flask_cors import CORS
from app.extensions import mail
from src.core.utils.config import get_env_variable

def create_app():
    # 使用绝对路径，适配Docker和开发环境
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    static_folder = os.path.join(project_root, 'web', 'dist')
    
    # 检查路径是否存在，如果不存在则尝试Docker中的路径
    if not os.path.exists(static_folder):
        static_folder = '/app/web/dist'
    
    print(f"静态文件路径: {static_folder}")
        
    app = Flask(__name__, static_folder=static_folder, static_url_path='/')
    
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
    
    # 添加自定义静态文件处理，为所有非index.html文件添加15天协商缓存
    @app.route('/<path:filename>')
    def custom_static(filename):
        cache_timeout = None
        if filename != 'index.html':
            # 为非index.html文件设置15天的协商缓存
            cache_timeout = 60 * 60 * 24 * 15  # 15天的秒数
        
        response = send_from_directory(app.static_folder, filename, cache_timeout=cache_timeout)
        
        if filename != 'index.html':
            # 添加协商缓存相关的头信息
            # 本地服务器部分，根据需要使用协商缓存验证
            max_age = 60 * 60 * 24 * 15  # 15天的秒数
            response.headers['Cache-Control'] = f'public, max-age={max_age}, must-revalidate'
            expires = datetime.now() + timedelta(days=15)
            response.headers['Expires'] = expires.strftime('%a, %d %b %Y %H:%M:%S GMT')
            # 添加ETag或Last-Modified头，使浏览器能够进行协商缓存
            if 'ETag' not in response.headers:
                # 生成ETag
                file_path = os.path.join(app.static_folder, filename)
                etag_content = f"{filename}:{os.path.getmtime(file_path)}"
                etag_hash = hashlib.md5(etag_content.encode()).hexdigest()
                response.headers['ETag'] = f'W/"{etag_hash}"'
            
            # 设置Last-Modified如果不存在
            if 'Last-Modified' not in response.headers:
                file_path = os.path.join(app.static_folder, filename)
                last_modified = datetime.fromtimestamp(os.path.getmtime(file_path)).strftime('%a, %d %b %Y %H:%M:%S GMT')
                response.headers['Last-Modified'] = last_modified
        else:
            # index.html不缓存
            response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
            response.headers['Pragma'] = 'no-cache'
            response.headers['Expires'] = '0'
            
        return response
    
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

