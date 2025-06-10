import re
import json
from typing import Dict, List, Any, Optional

from src.core.models.chat import AIChat
from src.core.mcp.utils import run_async, call_mcp_tool, list_mcp_tools
from src.core.utils.config import get_env_variable

class MCPChat(AIChat):
    """支持MCP工具调用的聊天模型类"""
    
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