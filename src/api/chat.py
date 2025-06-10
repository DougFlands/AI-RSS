from flask import Blueprint, request, jsonify
import uuid
from src.core.utils.config import get_env_variable
from src.core.models.chat import AIChat
from src.core.models.mcpchat import MCPChat

chat_bp = Blueprint("chat", __name__, url_prefix="/chat")

chatSessions = {}
mcpChatSessions = {}  # 用于存储支持MCP工具调用的会话

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

@chat_bp.route('/msg', methods=['POST'])
def post_chat_msg():
    """支持多轮对话和MCP工具调用的聊天接口"""
    data = request.get_json()
    userInput = data.get('message')
    sessionId = data.get('sessionId')
    modelType = data.get('modelType', 'deepseek')  # 默认使用 deepseek 模型
    systemPrompt = data.get('systemPrompt', '')
    mcp_url = get_env_variable("MCP_URL")  # MCP服务URL

    if not userInput:
        return jsonify({
            "error": "消息内容不能为空"
        }), 400

    # 生成新会话ID（如果未提供）
    if not sessionId:
        sessionId = str(uuid.uuid4())
    
    # 获取或创建聊天会话
    mcpChat = mcpChatSessions.get(sessionId)
    if not mcpChat:
        mcpChat = MCPChat(modelType, systemPrompt)
        mcpChatSessions[sessionId] = mcpChat
        
        # 如果提供了自定义MCP URL，设置它
        if mcp_url and mcp_url != mcpChat.mcp_url:
            mcpChat.mcp_url = mcp_url
    
    try:
        # 获取响应
        aiResponse = mcpChat.get_response(userInput)
        
        # 构建响应数据
        response_data = {
            "sessionId": sessionId,
            "response": aiResponse.get("response", "") if isinstance(aiResponse, dict) else aiResponse,
            "history": mcpChat.get_conversation_history()
        }
        
        # 如果响应中包含工具调用信息，添加到响应中
        if isinstance(aiResponse, dict) and "has_tool_call" in aiResponse:
            response_data["has_tool_call"] = aiResponse["has_tool_call"]
        
        return jsonify(response_data)
    except Exception as e:
        return jsonify({
            "error": str(e)
        }), 500