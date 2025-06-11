import re
import json
import asyncio
from typing import Dict, List, Any, Optional, AsyncGenerator, Callable, Union

from src.core.models.chat import AIChat
from src.core.mcp.utils import run_async, call_mcp_tool, list_mcp_tools, call_mcp_tool_streaming
from src.core.utils.config import get_env_variable

class MCPChatFixed(AIChat):
    """支持MCP工具调用的聊天模型类 - 修复版本"""
    
    def __init__(self, modelType, system_prompt=""):
        mcp_url = get_env_variable("MCP_URL")
        super().__init__(modelType, system_prompt)
        self.mcp_url = mcp_url
        self.conversation_history = []  # 存储完整对话历史
        self.available_tools = self._get_available_tools()
        
        # 扩展系统提示，包含可用工具信息
        if self.available_tools:
            tool_descriptions = "\n".join([f"- {tool}" for tool in self.available_tools])
            self.system_prompt += f"\n\n可用的MCP工具:\n{tool_descriptions}\n\n你可以通过回复格式为 ```mcp\n{{\"tool\": \"工具名\", \"params\": {{参数字典}}}}\n```的内容来调用工具。"
    
    def _get_available_tools(self) -> List[str]:
        """获取MCP服务可用的工具列表"""
        try:
            return run_async(list_mcp_tools())
        except Exception as e:
            print(f"获取MCP工具列表失败: {str(e)}")
            return []
    
    def add_message(self, role: str, content: str) -> None:
        """添加消息到对话历史"""
        self.conversation_history.append({"role": role, "content": content})
    
    def get_conversation_history(self) -> List[Dict[str, str]]:
        """获取完整对话历史"""
        return self.conversation_history
    
    def get_response(self, user_input: str) -> Dict[str, Any]:
        """处理用户输入并返回响应，支持MCP工具调用"""
        # 添加用户消息到历史
        self.add_message("user", user_input)
        
        # 获取AI响应
        ai_response = super().get_response(user_input)
        response_text = ai_response.get("response", "") if isinstance(ai_response, dict) else ai_response
        
        # 检查响应是否包含MCP工具调用
        tool_calls = self._extract_tool_calls(response_text)
        
        if tool_calls:
            # 处理工具调用
            final_response = self._process_tool_calls(response_text, tool_calls)
            # 添加处理后的响应到历史
            self.add_message("assistant", final_response)
            return {"response": final_response, "has_tool_call": True}
        else:
            # 没有工具调用，直接返回原始响应
            self.add_message("assistant", response_text)
            return {"response": response_text, "has_tool_call": False}
    
    # 修复版本 - 修改回调函数类型注解并处理可变参数
    async def get_streaming_response(self, user_input: str, callback: Callable[[str, bool, Optional[bool]], None]) -> None:
        """处理用户输入并以流式方式返回响应
        
        Args:
            user_input: 用户输入文本
            callback: 回调函数，接收部分响应、是否完成的标志，以及可选的工具调用标志
        """
        # 添加用户消息到历史
        self.add_message("user", user_input)
        
        # 初始完整响应和当前响应缓冲
        complete_response = ""
        current_buffer = ""
        has_tool_call = False
        
        # 获取AI流式响应
        async for chunk in self._get_ai_streaming_response(user_input):
            # 更新完整响应
            complete_response += chunk
            current_buffer += chunk
            
            # 检查是否有完整的工具调用代码块
            if "```mcp" in current_buffer and "```" in current_buffer[current_buffer.find("```mcp"):]:
                # 发送当前缓冲区内容给前端
                callback(current_buffer, False, has_tool_call)
                current_buffer = ""
                
                # 提取最新的工具调用
                tool_calls = self._extract_tool_calls(complete_response)
                if tool_calls:
                    has_tool_call = True  # 标记有工具调用
                    latest_tool_call = tool_calls[-1]
                    tool_name = latest_tool_call.get("tool")
                    params = latest_tool_call.get("params", {})
                    
                    # 处理工具调用
                    try:
                        if tool_name not in self.available_tools:
                            tool_result = f"⚠️ 工具 '{tool_name}' 不可用。可用工具: {', '.join(self.available_tools)}"
                            callback(tool_result, False, has_tool_call)
                        else:
                            # 流式调用MCP工具并实时返回结果
                            callback(f"✅ 工具 '{tool_name}' 调用中...\n```\n", False, has_tool_call)
                            async for result_chunk in call_mcp_tool_streaming(tool_name, params, self.mcp_url):
                                callback(result_chunk, False, has_tool_call)
                            callback("\n```", False, has_tool_call)
                    except Exception as e:
                        error_msg = f"❌ 工具 '{tool_name}' 调用失败: {str(e)}"
                        callback(error_msg, False, has_tool_call)
            else:
                # 发送当前缓冲区内容给前端
                if current_buffer:
                    callback(current_buffer, False, has_tool_call)
                    current_buffer = ""
        
        # 添加完整响应到对话历史
        self.add_message("assistant", complete_response)
        
        # 发送完成信号
        callback("", True, has_tool_call)
    
    async def _get_ai_streaming_response(self, user_input: str) -> AsyncGenerator[str, None]:
        """获取AI模型的流式响应"""
        # 此处需要实现具体模型的流式响应API调用
        # 以下是示例实现，实际需要根据您使用的AI模型API进行适配
        try:
            # 示例：使用您现有的聊天模型进行流式响应
            # 实际实现中需要替换为调用模型的流式API
            from src.core.mcp.utils import call_streaming_model
            
            async for chunk in call_streaming_model(
                self.modelType,
                user_input,
                self.conversation_history,
                self.system_prompt
            ):
                yield chunk
        except Exception as e:
            print(f"流式响应发生错误: {str(e)}")
            yield f"获取响应时发生错误: {str(e)}"
    
    def _extract_tool_calls(self, text: str) -> List[Dict[str, Any]]:
        """从响应文本中提取MCP工具调用"""
        tool_calls = []
        # 使用正则表达式匹配 ```mcp ... ``` 代码块
        pattern = r"```mcp\s*([\s\S]*?)\s*```"
        matches = re.finditer(pattern, text)
        for match in matches:
            try:
                tool_call_json = match.group(1).strip()
                tool_call = json.loads(tool_call_json)
                if "tool" in tool_call and "params" in tool_call:
                    tool_calls.append(tool_call)
            except json.JSONDecodeError:
                continue
                
        return tool_calls
    
    def _process_tool_calls(self, original_response: str, tool_calls: List[Dict[str, Any]]) -> str:
        """处理工具调用并生成最终响应"""
        result = original_response
        
        for tool_call in tool_calls:
            tool_name = tool_call.get("tool")
            params = tool_call.get("params", {})
            
            # 检查工具是否可用
            if tool_name not in self.available_tools:
                replacement = f"⚠️ 工具 '{tool_name}' 不可用。可用工具: {', '.join(self.available_tools)}"
            else:
                try:
                    # 调用MCP工具
                    tool_result = run_async(call_mcp_tool(tool_name, params, self.mcp_url))
                    replacement = f"✅ 工具 '{tool_name}' 调用结果:\n```\n{tool_result}\n```"
                except Exception as e:
                    replacement = f"❌ 工具 '{tool_name}' 调用失败: {str(e)}"
            
            # 替换原始响应中的工具调用部分
            pattern = r"```mcp\s*" + re.escape(json.dumps(tool_call, ensure_ascii=False)) + r"\s*```"
            result = re.sub(pattern, replacement, result, flags=re.DOTALL)
        
        return result 