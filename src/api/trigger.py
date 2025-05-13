from flask import Blueprint, request, jsonify
from src.core.utils.config import RSS_SYSTEM_PROMPT
from src.core.models.chat import AIChat
from src.core.models.email import SendEmail
from src.core.models.rss import OutputRss

trigger_bp = Blueprint("trigger", __name__, url_prefix="/trigger")

@trigger_bp.route('/', methods=['POST'])
def GetTrigger():
    data = request.get_json()
    
    outputRss = OutputRss()
    
    body = ""
    
    for value in outputRss.values():
        modelType = data.get('modelType')
        aiChat = AIChat(modelType, system_prompt=RSS_SYSTEM_PROMPT)
        s = str(value)
        aiResponse = aiChat.getResponse(s)
        
        recipients = data.get("recipients")  
        subject =data.get("subject")       
        body = body + aiResponse.get("response")
        
        
        if not recipients or not subject or not body:
            return jsonify({"error": "Missing recipients, subject, or body"}), 400

    SendEmail(subject, recipients, body)
    
    return jsonify({"message": "success"})
