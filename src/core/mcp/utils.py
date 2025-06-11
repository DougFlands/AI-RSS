import asyncio
import logging
from typing import Dict, Any, AsyncGenerator
from fastmcp import Client, FastMCP
from src.core.utils.config import get_env_variable

# 获取日志记录器
logger = logging.getLogger(__name__)

server_url = get_env_variable("MCP_URL")
logger.info(f"MCP服务器URL: {server_url}")

async def call_mcp_tool_streaming(tool_name: str, params: Dict[str, Any], custom_url=None) -> AsyncGenerator[str, None]:
    """
    以流式方式调用MCP服务的工具函数
    
    Args:
        tool_name: 工具名称
        params: 参数字典
        custom_url: 自定义MCP服务器URL
        
    Yields:
        工具调用的流式结果，每次产生一部分结果
    """
    url = custom_url or server_url
    logger.info(f"流式调用MCP工具: tool_name={tool_name}, url={url}")
    logger.info(f"工具参数: {params}")
    
    try:
        # 使用异步上下文管理器正确管理客户端连接
        async with Client(url) as client:
            logger.info(f"已连接到MCP服务器: {url}")
            
            logger.info(f"检查工具 {tool_name}")
            tools = await client.list_tools()
            tool_info = next((t for t in tools if t.name == tool_name), None)
            
            if not tool_info:
                logger.warning(f"工具不存在: {tool_name}")
                error_msg = f"工具 '{tool_name}' 不存在"
                yield error_msg
                return
            
            logger.info(f"尝试调用工具: {tool_name}")
            result = await client.call_tool(tool_name, params)
            
            # 处理结果，FastMCP的call_tool返回的是一个列表
            if result and isinstance(result, list) and len(result) > 0:
                # 获取第一个结果项的文本内容
                if hasattr(result[0], 'text'):
                    result_text = result[0].text
                else:
                    # 如果没有text属性，尝试转换为字符串
                    result_text = str(result[0])
                
                logger.info(f"调用成功: tool_name={tool_name}, 结果大小={len(result_text)}")
                logger.info(f"工具调用结果: {result_text[:200]}...")
                yield result_text
            else:
                logger.info(f"工具调用成功但无结果: tool_name={tool_name}")
                yield ""
    except Exception as e:
        error_msg = f"工具调用错误: {str(e)}"
        logger.error(f"工具调用失败: tool_name={tool_name}, 错误: {str(e)}", exc_info=True)
        yield error_msg

async def call_streaming_model(model_type: str, user_input: str, history=None, system_prompt=None) -> AsyncGenerator[str, None]:
    """
    调用支持流式输出的AI模型
    
    Args:
        model_type: 模型类型名称
        user_input: 用户输入文本
        history: 对话历史记录
        system_prompt: 系统提示
        
    Yields:
        AI模型的流式响应，每次产生一部分文本
    """
    logger.info(f"调用流式模型: model_type={model_type}")
    logger.info(f"用户输入: {user_input[:100]}...")
    logger.info(f"系统提示: {system_prompt[:100] if system_prompt else 'None'}")
    logger.info(f"历史记录: {len(history) if history else 0} 条消息")
    
    # 这里需要实现具体模型的流式API调用
    # 以下是示例实现，实际需要根据您使用的模型进行适配
    try:
        # 检查模型类型并使用相应的API
        if model_type.lower() == 'deepseek':
            # 使用DeepSeek模型API
            from src.core.models.deepseek import get_deepseek_streaming_response
            
            logger.info("使用DeepSeek模型进行流式响应")
            
            # 确保历史记录格式正确
            formatted_history = history
            if history and isinstance(history, list):
                # 已经是正确格式，无需转换
                pass
            
            # 直接传递所有参数
            chunk_count = 0
            total_size = 0
            
            try:
                async for chunk in get_deepseek_streaming_response(user_input, formatted_history, system_prompt):
                    if chunk and chunk.strip():  # 确保不返回空块
                        chunk_count += 1
                        total_size += len(chunk)
                        yield chunk
                
                logger.info(f"DeepSeek流式响应完成: 共返回{chunk_count}个块, 总大小={total_size}字节")
            except Exception as e:
                error = f"DeepSeek流式处理错误: {str(e)}"
                logger.error(f"DeepSeek流式处理失败: {str(e)}", exc_info=True)
                yield error
                
        elif model_type.lower() == 'openai':
            # 示例：使用OpenAI API
            from openai import AsyncOpenAI
            
            logger.info("使用OpenAI模型进行流式响应")
            
            client = AsyncOpenAI(api_key=get_env_variable("OPENAI_API_KEY"))
            
            # 格式化历史记录
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            
            if history:
                for msg in history:
                    if msg["role"] in ["user", "assistant", "system"]:
                        messages.append({"role": msg["role"], "content": msg["content"]})
            
            messages.append({"role": "user", "content": user_input})
            
            logger.info(f"OpenAI请求消息数量: {len(messages)}")
            
            # 创建流式完成
            logger.info("开始创建OpenAI流式完成")
            stream = await client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                stream=True
            )
            
            # 返回流式响应
            chunk_count = 0
            total_size = 0
            
            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    chunk_count += 1
                    total_size += len(content)
                    logger.info(f"收到OpenAI响应块 #{chunk_count}: 大小={len(content)}, 内容={content}")
                    yield content
            
            logger.info(f"OpenAI流式响应完成: 共返回{chunk_count}个块, 总大小={total_size}字节")
        else:
            # 不支持的模型类型
            logger.warning(f"不支持的模型类型: {model_type}")
            yield f"不支持的模型类型: {model_type}，请使用 deepseek 或 openai"
    except Exception as e:
        error_message = f"流式模型调用错误: {str(e)}"
        logger.error(f"流式模型调用失败: {str(e)}", exc_info=True)
        yield error_message

async def list_mcp_tools(custom_url=None):
    """
    列出MCP服务可用的工具
    
    Args:
        custom_url: 自定义MCP服务器URL
        
    Returns:
        可用工具列表
    """
    url = custom_url or server_url
    logger.info(f"列出MCP可用工具: url={url}")
    
    try:
        async with Client(url) as client:
            logger.info(f"已连接到MCP服务器: {url}")
            tools = await client.list_tools()
            tool_names = [tool.name for tool in tools]
            logger.info(f"获取到{len(tool_names)}个可用工具: {', '.join(tool_names)}")
            return tool_names
    except Exception as e:
        logger.error(f"获取MCP工具列表失败: {str(e)}", exc_info=True)
        return []

def run_async(coroutine):
    """
    在同步代码中运行异步函数的辅助方法
    
    Args:
        coroutine: 异步协程
        
    Returns:
        协程执行结果
    """
    try:
        return asyncio.run(coroutine)
    except Exception as e:
        logger.error(f"异步执行失败: {str(e)}", exc_info=True)
        raise 