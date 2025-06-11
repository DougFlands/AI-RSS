"""
DeepSeek模型的实现，支持流式输出
"""
import os
import asyncio
from typing import List, Dict, Any, AsyncGenerator, Optional
from src.core.utils.config import get_env_variable
from openai import OpenAI

async def get_deepseek_streaming_response(
    user_input: str, 
    history: Optional[List[Dict[str, str]]] = None, 
    system_prompt: Optional[str] = None
) -> AsyncGenerator[str, None]:
    """
    调用DeepSeek模型的流式响应API
    
    Args:
        user_input: 用户输入文本
        history: 对话历史
        system_prompt: 系统提示
        
    Yields:
        模型生成的文本片段
    """
    try:
        # 转换历史记录格式
        messages = []
        
        # 添加系统提示
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        # 添加历史记录
        if history:
            for msg in history:
                if msg["role"] in ["user", "assistant"]:
                    messages.append({"role": msg["role"], "content": msg["content"]})
        
        # 添加当前用户输入
        messages.append({"role": "user", "content": user_input})
        
        # 创建DeepSeek客户端
        api_key = get_env_variable("DEEPSEEK_KEY")
        if not api_key:
            yield "错误: 未设置DEEPSEEK_KEY环境变量"
            return
            
        client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com/v1")
        
        # 使用流式API获取响应
        try:
            model_name = "deepseek-chat"  # 默认使用deepseek-chat模型
            
            # 获取流式响应
            stream = client.chat.completions.create(
                model=model_name,
                messages=messages,
                stream=True
            )
            
            # 正确处理OpenAI流式响应 - Stream对象不支持async for
            # 使用迭代器协议手动处理
            for chunk in stream:
                # 从OpenAI流式响应中提取内容
                if hasattr(chunk.choices[0].delta, 'content') and chunk.choices[0].delta.content is not None:
                    content = chunk.choices[0].delta.content
                    if content and content.strip():  # 只返回非空内容
                        yield content
                # 适当延迟以允许事件循环处理其他任务
                await asyncio.sleep(0)
        
        except Exception as e:
            error_msg = f"{model_name} API错误: {str(e)}"
            print(error_msg)  # 打印详细错误信息到控制台
            yield error_msg
    
    except Exception as e:
        error_msg = f"DeepSeek流式响应错误: {str(e)}"
        print(error_msg)  # 打印详细错误信息到控制台
        yield error_msg 