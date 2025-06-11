from flask import Blueprint, request, jsonify, Response, stream_with_context
import uuid
import json
import asyncio
import threading
import queue
import time
from src.core.utils.config import get_env_variable
from src.core.models.chat import AIChat
from src.core.models.mcpchat import MCPChat
from functools import partial

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
    mcp_url = data.get('mcpUrl') or get_env_variable("MCP_URL")  # MCP服务URL

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

@chat_bp.route('/stream', methods=['GET', 'POST'])
def stream_chat():
    """流式聊天接口 - 支持SSE事件流和MCP工具调用
    
    两种使用模式:
    1. 双阶段模式：先通过GET请求建立连接，获取sessionId，再通过POST请求发送消息
    2. 单阶段模式：直接通过POST请求发送消息并返回流式响应
    """
    
    # 获取会话ID (共同处理GET和POST请求)
    if request.method == 'POST':
        data = request.get_json()
        sessionId = data.get('sessionId')
        create_new_stream = data.get('createStream', False)  # 新增参数，指示是否创建新的流连接
    else:
        sessionId = request.args.get('sessionId')
        create_new_stream = False
        
    # 如果没有会话ID，创建一个新的
    if not sessionId:
        sessionId = str(uuid.uuid4())
    
    # 如果是GET请求或者POST请求带有createStream=True参数，创建新的SSE流
    if request.method == 'GET' or create_new_stream:
        def generate_session():
            yield f"data: {json.dumps({'type': 'session_id', 'session_id': sessionId})}\n\n"
            
            # 创建响应队列
            response_queue = queue.Queue()
            active_streams[sessionId] = response_queue
            
            # 如果是POST请求且带有消息，则处理消息
            if request.method == 'POST' and create_new_stream:
                userInput = data.get('message')
                if userInput:
                    # 获取或创建聊天会话
                    modelType = data.get('modelType', 'deepseek')
                    systemPrompt = data.get('systemPrompt', '')
                    mcp_url = data.get('mcpUrl') or get_env_variable("MCP_URL")
                    
                    mcpChat = mcpChatSessions.get(sessionId)
                    if not mcpChat:
                        mcpChat = MCPChat(modelType, systemPrompt)
                        mcpChatSessions[sessionId] = mcpChat
                        
                        # 如果提供了自定义MCP URL，设置它
                        if mcp_url and mcp_url != mcpChat.mcp_url:
                            mcpChat.mcp_url = mcp_url
                    
                    # 定义回调函数和工具调用标志
                    has_tool_call_flag = [False]
                    
                    # 在单独的线程中处理消息
                    thread = threading.Thread(
                        target=process_async_response,
                        args=(sessionId, mcpChat, userInput, response_queue, has_tool_call_flag)
                    )
                    thread.daemon = True
                    thread.start()
            
            try:
                while True:
                    try:
                        # 非阻塞方式获取响应，如果没有则短暂休眠
                        item = response_queue.get(block=False)
                        if item is None:  # 结束信号
                            yield f"data: {json.dumps({'type': 'end'})}\n\n"
                            break
                        else:
                            yield item
                    except queue.Empty:
                        # 等待一段时间后再次检查
                        time.sleep(0.1)
            finally:
                # 清理
                if sessionId in active_streams:
                    del active_streams[sessionId]
                    
        return Response(
            stream_with_context(generate_session()),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'X-Accel-Buffering': 'no',
                'Connection': 'keep-alive'
            }
        )
    
    # 处理常规的POST请求 - 接收用户消息并生成响应
    userInput = data.get('message')
    modelType = data.get('modelType', 'deepseek')
    systemPrompt = data.get('systemPrompt', '')
    mcp_url = data.get('mcpUrl') or get_env_variable("MCP_URL")
    
    if not userInput:
        return jsonify({"error": "消息内容不能为空"}), 400
    
    # 获取或创建聊天会话
    mcpChat = mcpChatSessions.get(sessionId)
    if not mcpChat:
        mcpChat = MCPChat(modelType, systemPrompt)
        mcpChatSessions[sessionId] = mcpChat
        
        # 如果提供了自定义MCP URL，设置它
        if mcp_url and mcp_url != mcpChat.mcp_url:
            mcpChat.mcp_url = mcp_url
            
    # 检查是否有活动的流
    if sessionId not in active_streams:
        return jsonify({
            "error": "没有找到活动的流连接，请先建立GET连接或使用createStream=true",
            "sessionId": sessionId
        }), 400
    
    # 获取响应队列
    response_queue = active_streams[sessionId]
    has_tool_call_flag = [False]  # 用于跟踪是否有工具调用
    
    # 启动处理线程
    thread = threading.Thread(
        target=process_async_response,
        args=(sessionId, mcpChat, userInput, response_queue, has_tool_call_flag)
    )
    thread.daemon = True
    thread.start()
    
    return jsonify({"status": "processing", "sessionId": sessionId})

# 将异步处理逻辑抽取为单独的函数，便于重用
def process_async_response(sessionId, mcpChat, userInput, response_queue, has_tool_call_flag):
    """在单独的线程中处理异步模型调用"""
    
    # 定义两参数的回调函数
    def simple_callback(chunk, is_complete):
        # 检测工具调用
        if chunk and "```mcp" in chunk and not has_tool_call_flag[0]:
            has_tool_call_flag[0] = True
            response_queue.put(f"data: {json.dumps({'type': 'tool_call'})}\n\n")
        
        if chunk and chunk.strip():  # 确保只有非空内容才发送
            response_queue.put(f"data: {json.dumps({'type': 'chunk', 'content': chunk})}\n\n")
        
        if is_complete:
            # 发送结束信号
            response_queue.put(None)
    
    # 创建新的事件循环
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        # 启动异步流式响应，直接使用符合参数要求的回调函数
        async def run_streaming():
            # 直接传递callback参数
            await mcpChat.get_streaming_response(userInput, simple_callback)
            
        loop.run_until_complete(run_streaming())
    except Exception as e:
        error_message = str(e)
        print(f"流式处理错误: {error_message}")
        response_queue.put(f"data: {json.dumps({'type': 'error', 'error': error_message})}\n\n")
        response_queue.put(None)  # 发送结束信号
    finally:
        loop.close()

# 存储活动的流连接
active_streams = {}