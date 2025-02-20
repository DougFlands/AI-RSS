from flask import Blueprint, request, jsonify
from src.core.models.chat import AIChat
from src.core.models.email import SendEmail
from src.core.models.rss import OutputRss

trigger_bp = Blueprint("trigger", __name__, url_prefix="/trigger")

@trigger_bp.route('/', methods=['POST'])
def GetTrigger():
    data = request.get_json()
    
    outputRss = OutputRss()
    
    body = ""
    system_prompt="这是一段 RSS 信息，请将里面的信息过滤，按照你认为的重要程度排序并分类。最后输出一个 Email 的 HTML 正文。注意：邮件的正文需要包含标题和内容，标题需要包含日期，内容需要包含标题和链接，只输出 带HTML标签 的正文即可。不要输出 markdown "
    
    for value in outputRss.values():
        modelType = data.get('modelType')
        aiChat = AIChat(modelType, system_prompt=system_prompt)
        s = str(value)
        aiResponse = aiChat.getResponse(s)
        
        recipients = data.get("recipients")  
        subject =data.get("subject")       
        body = body + aiResponse.get("response")
        
        
        if not recipients or not subject or not body:
            return jsonify({"error": "Missing recipients, subject, or body"}), 400

    SendEmail(subject, recipients, body)
    
    return jsonify({"message": "success"})
