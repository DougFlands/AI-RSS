from flask import Blueprint, request, jsonify
import uuid
from src.core.models.chat import AIChat

chat_bp = Blueprint("chat", __name__, url_prefix="/chat")

chatSessions = {}

@chat_bp.route('/', methods=['POST'])
def post_chat():
    data = request.get_json()
    userInput = data.get('message')
    sessionId = data.get('sessionId')
    modelType = data.get('modelType')
    systemPrompt = data.get('systemPrompt')

    if not sessionId:
        sessionId = str(uuid.uuid4())

    aiChat = chatSessions.get(sessionId)
    if not aiChat:
        aiChat = AIChat(modelType, systemPrompt)
        chatSessions[sessionId] = aiChat

    try:
        aiResponse = aiChat.get_response(userInput)
        return jsonify({
            "sessionId": sessionId,
            "response": aiResponse
        })
    except Exception as e:
        return jsonify({
            "error": str(e)
        }), 500