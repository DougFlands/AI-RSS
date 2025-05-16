from flask import Blueprint, request, jsonify
from src.core.utils.config import RSS_SYSTEM_PROMPT, get_env_variable
from src.core.models.chat import AIChat
from src.core.models.email import send_email
from src.core.models.rss import output_rss

trigger_bp = Blueprint("trigger", __name__, url_prefix="/trigger")

@trigger_bp.route('/', methods=['POST'])
def get_trigger():
    data = request.get_json()
    
    outputRss = output_rss()
    
    body = ""
    
    for value in outputRss.values():
        modelType = data.get('modelType')
        aiChat = AIChat(modelType, system_prompt=RSS_SYSTEM_PROMPT)
        s = str(value)
        aiResponse = aiChat.get_response(s)
        
        recipients = data.get("recipients")  
        subject =data.get("subject")       
        body = body + aiResponse.get("response")
        
        
        if not recipients or not subject or not body:
            return jsonify({"error": "Missing recipients, subject, or body"}), 400

    if get_env_variable("TIMED_SEND_MAIL") == "True": 
        send_email(subject, recipients, body)
    
    return jsonify({"message": "success"})
