import logging
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
import re

# 配置日志记录
logging.basicConfig(
    level=logging.DEBUG,
    format='[%(asctime)s] [%(levelname)s] [%(module)s:%(lineno)d] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

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
        logger.error(f"处理聊天请求时出错: {str(e)}", exc_info=True)
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
        logger.info(f"收到POST流式请求: sessionId={sessionId}, createStream={create_new_stream}")
    else:
        sessionId = request.args.get('sessionId')
        create_new_stream = False
        logger.info(f"收到GET流式请求: sessionId={sessionId}")
        
    # 如果没有会话ID，创建一个新的
    if not sessionId:
        sessionId = str(uuid.uuid4())
        logger.info(f"生成新的会话ID: {sessionId}")
    
    # 如果是GET请求或者POST请求带有createStream=True参数，创建新的SSE流
    if request.method == 'GET' or create_new_stream:
        def generate_session():
            logger.debug(f"开始生成SSE会话: sessionId={sessionId}")
            yield f"data: {json.dumps({'type': 'session_id', 'session_id': sessionId})}\n\n"
            logger.debug(f"已发送会话ID: {sessionId}")
            
            # 创建响应队列
            response_queue = queue.Queue()
            active_streams[sessionId] = response_queue
            logger.debug(f"已创建响应队列: sessionId={sessionId}")
            
            # 如果是POST请求且带有消息，则处理消息
            if request.method == 'POST' and create_new_stream:
                userInput = data.get('message')
                if userInput:
                    logger.info(f"处理POST流式请求中的消息: sessionId={sessionId}, message={userInput[:50]}...")
                    # 获取或创建聊天会话
                    modelType = data.get('modelType', 'deepseek')
                    systemPrompt = data.get('systemPrompt', '')
                    mcp_url = data.get('mcpUrl') or get_env_variable("MCP_URL")
                    
                    mcpChat = mcpChatSessions.get(sessionId)
                    if not mcpChat:
                        logger.info(f"创建新的MCP聊天会话: sessionId={sessionId}, modelType={modelType}")
                        mcpChat = MCPChat(modelType, systemPrompt)
                        mcpChatSessions[sessionId] = mcpChat
                        
                        # 如果提供了自定义MCP URL，设置它
                        if mcp_url and mcp_url != mcpChat.mcp_url:
                            logger.info(f"设置自定义MCP URL: {mcp_url}")
                            mcpChat.mcp_url = mcp_url
                    
                    # 定义回调函数和工具调用标志
                    has_tool_call_flag = [False]
                    
                    # 在单独的线程中处理消息
                    logger.debug(f"启动异步处理线程: sessionId={sessionId}")
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
                            logger.debug(f"收到结束信号: sessionId={sessionId}")
                            yield f"data: {json.dumps({'type': 'end'})}\n\n"
                            break
                        else:
                            logger.debug(f"发送SSE数据: {item[:100]}...")
                            yield item
                    except queue.Empty:
                        # 等待一段时间后再次检查
                        time.sleep(0.1)
            finally:
                # 清理
                if sessionId in active_streams:
                    logger.debug(f"清理响应队列: sessionId={sessionId}")
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
        logger.info(f"创建新的MCP聊天会话: sessionId={sessionId}, modelType={modelType}")
        mcpChat = MCPChat(modelType, systemPrompt)
        mcpChatSessions[sessionId] = mcpChat
        
        # 如果提供了自定义MCP URL，设置它
        if mcp_url and mcp_url != mcpChat.mcp_url:
            logger.info(f"设置自定义MCP URL: {mcp_url}")
            mcpChat.mcp_url = mcp_url
            
    # 检查是否有活动的流
    if sessionId not in active_streams:
        logger.warning(f"未找到活动的流连接: sessionId={sessionId}")
        return jsonify({
            "error": "没有找到活动的流连接，请先建立GET连接或使用createStream=true",
            "sessionId": sessionId
        }), 400
    
    # 获取响应队列
    response_queue = active_streams[sessionId]
    has_tool_call_flag = [False]  # 用于跟踪是否有工具调用
    
    # 启动处理线程
    logger.debug(f"启动异步处理线程: sessionId={sessionId}")
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
    
    # 用于收集完整的AI响应
    complete_response = ""
    
    # 定义两参数的回调函数
    def simple_callback(chunk, is_complete):
        nonlocal complete_response
        
        # 记录接收到的AI输出
        logger.debug(f"AI输出: sessionId={sessionId}, chunk={chunk}, is_complete={is_complete}")
        
        # 添加到完整响应
        complete_response += chunk
        
        # 发送原始块给客户端
        if chunk and chunk.strip():  # 确保只有非空内容才发送
            response_queue.put(f"data: {json.dumps({'type': 'chunk', 'content': chunk})}\n\n")
        
        if is_complete:
            # AI响应完成，处理完整响应
            logger.info(f"AI响应完成: sessionId={sessionId}")
            logger.info(f"完整响应: {complete_response}")
            
            # 检测并处理工具调用
            process_complete_response(complete_response, response_queue)
            
            # 发送结束信号
            response_queue.put(None)
    
    # 处理完整响应中的工具调用
    def process_complete_response(response_text, response_queue):
        """处理完整响应中的工具调用"""
        # 使用正则表达式匹配所有 ```mcp ... ``` 代码块
        pattern = r"```mcp\s*([\s\S]*?)\s*```"
        matches = re.finditer(pattern, response_text)
        
        tool_calls_found = False
        
        for match in matches:
            tool_call_text = match.group(1).strip()
            logger.info(f"检测到工具调用: {tool_call_text}")
            tool_calls_found = True
            has_tool_call_flag[0] = True
            
            # 处理工具调用
            process_tool_call(tool_call_text, response_queue)
        
        if not tool_calls_found:
            logger.info("未检测到工具调用")
    
    # 处理单个工具调用
    def process_tool_call(tool_call_text, response_queue):
        """处理工具调用"""
        try:
            # 解析工具调用JSON
            tool_call = json.loads(tool_call_text)
            tool_name = tool_call.get("tool")
            params = tool_call.get("params", {})
            
            logger.info(f"解析工具调用: tool_name={tool_name}, params={params}")
            
            # 通知前端有工具调用
            response_queue.put(f"data: {json.dumps({'type': 'tool_call'})}\n\n")
            
            # 创建新的事件循环来执行工具调用
            tool_loop = asyncio.new_event_loop()
            
            def run_tool_call():
                asyncio.set_event_loop(tool_loop)
                try:
                    # 在新事件循环中执行工具调用
                    tool_loop.run_until_complete(execute_tool_and_send_results(tool_name, params, response_queue))
                finally:
                    tool_loop.close()
            
            # 创建并启动线程来执行工具调用
            tool_thread = threading.Thread(target=run_tool_call)
            tool_thread.daemon = True
            tool_thread.start()
            
            # 等待工具调用线程完成
            logger.info(f"等待工具调用完成: tool_name={tool_name}")
            tool_thread.join()
            logger.info(f"工具调用线程已完成: tool_name={tool_name}")
            
        except json.JSONDecodeError as e:
            error_msg = f"❌ 工具调用格式错误: {tool_call_text}, 错误: {str(e)}"
            logger.error(f"工具调用JSON解析错误: {error_msg}")
            response_queue.put(f"data: {json.dumps({'type': 'chunk', 'content': error_msg})}\n\n")
        except Exception as e:
            error_msg = f"❌ 工具调用处理失败: {str(e)}"
            logger.error(f"工具调用处理异常: {error_msg}", exc_info=True)
            response_queue.put(f"data: {json.dumps({'type': 'chunk', 'content': error_msg})}\n\n")
    
    # 异步执行工具调用并发送结果
    async def execute_tool_and_send_results(tool_name, params, response_queue):
        """异步执行工具调用并发送结果"""
        try:
            # 调用工具并获取结果
            logger.debug(f"开始流式调用工具: tool_name={tool_name}")
            tool_responses = []
            async for result_chunk in mcpChat._call_tool_streaming(tool_name, params):
                # 发送工具调用结果给客户端
                logger.debug(f"工具调用结果: {result_chunk[:100]}...")
                response_queue.put(f"data: {json.dumps({'type': 'chunk', 'content': result_chunk})}\n\n")
                tool_responses.append(result_chunk)
            
            logger.info(f"工具调用完成，共发送了 {len(tool_responses)} 个结果块")
        except Exception as e:
            error_msg = f"❌ 工具 '{tool_name}' 调用失败: {str(e)}"
            logger.error(f"工具调用失败: {error_msg}", exc_info=True)
            response_queue.put(f"data: {json.dumps({'type': 'chunk', 'content': error_msg})}\n\n")
    
    # 创建新的事件循环
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        # 启动异步流式响应，直接使用符合参数要求的回调函数
        logger.info(f"开始获取流式响应: sessionId={sessionId}, userInput={userInput[:50]}...")
        async def run_streaming():
            # 直接传递callback参数
            await mcpChat.get_streaming_response(userInput, simple_callback)
            
        loop.run_until_complete(run_streaming())
    except Exception as e:
        error_message = str(e)
        logger.error(f"流式处理错误: {error_message}", exc_info=True)
        response_queue.put(f"data: {json.dumps({'type': 'error', 'error': error_message})}\n\n")
        response_queue.put(None)  # 发送结束信号
    finally:
        loop.close()

# 存储活动的流连接
active_streams = {}