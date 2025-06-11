import asyncio
from typing import Dict, Any, AsyncGenerator
from fastmcp import Client, FastMCP
from src.core.utils.config import get_env_variable

server_url = get_env_variable("MCP_URL")

async def call_mcp_tool(tool_name, params, custom_url=None):
    """
    调用MCP服务的工具函数
    
    Args:
        tool_name: 工具名称
        params: 参数字典
        custom_url: 自定义MCP服务器URL，如果提供则使用该URL
        
    Returns:
        工具调用结果
    """
    url = custom_url or server_url
    async with Client(url) as client:
        result = await client.call_tool(tool_name, params)
        return result.text

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
    async with Client(url) as client:
        try:
            # 检查工具是否支持流式输出
            tools = await client.list_tools()
            tool_info = next((t for t in tools if t.name == tool_name), None)
            
            if tool_info and getattr(tool_info, 'streaming', False):
                # 使用流式方式调用
                async for chunk in client.call_tool_streaming(tool_name, params):
                    yield chunk.text
            else:
                # 工具不支持流式输出，一次性返回结果
                result = await client.call_tool(tool_name, params)
                yield result.text
        except Exception as e:
            yield f"流式工具调用错误: {str(e)}"

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
    # 这里需要实现具体模型的流式API调用
    # 以下是示例实现，实际需要根据您使用的模型进行适配
    try:
        # 检查模型类型并使用相应的API
        if model_type.lower() == 'deepseek':
            # 使用DeepSeek模型API
            from src.core.models.deepseek import get_deepseek_streaming_response
            
            # 确保历史记录格式正确
            formatted_history = history
            if history and isinstance(history, list):
                # 已经是正确格式，无需转换
                pass
            
            # 直接传递所有参数
            try:
                async for chunk in get_deepseek_streaming_response(user_input, formatted_history, system_prompt):
                    if chunk and chunk.strip():  # 确保不返回空块
                        yield chunk
            except Exception as e:
                error = f"DeepSeek流式处理错误: {str(e)}"
                print(error)  # 详细错误打印到控制台
                yield error
                
        elif model_type.lower() == 'openai':
            # 示例：使用OpenAI API
            from openai import AsyncOpenAI
            
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
            
            # 创建流式完成
            stream = await client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                stream=True
            )
            
            # 返回流式响应
            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        else:
            # 不支持的模型类型
            yield f"不支持的模型类型: {model_type}，请使用 deepseek 或 openai"
    except Exception as e:
        error_message = f"流式模型调用错误: {str(e)}"
        print(error_message)  # 打印到控制台以便调试
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
    async with Client(url) as client:
        tools = await client.list_tools()
        return [tool.name for tool in tools]

def run_async(coroutine):
    """
    在同步代码中运行异步函数的辅助方法
    
    Args:
        coroutine: 异步协程
        
    Returns:
        协程执行结果
    """
    return asyncio.run(coroutine) 