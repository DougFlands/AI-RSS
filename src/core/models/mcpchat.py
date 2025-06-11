import re
import json
import asyncio
import logging
from typing import Dict, List, Any, Optional, AsyncGenerator, Callable

from src.core.models.chat import AIChat
from src.core.mcp.utils import run_async, list_mcp_tools, call_mcp_tool_streaming
from src.core.utils.config import get_env_variable

# 获取日志记录器
logger = logging.getLogger(__name__)

class MCPChat(AIChat):
    """支持MCP工具调用的聊天模型类"""
    
    def __init__(self, modelType, system_prompt=""):
        mcp_url = get_env_variable("MCP_URL")
        super().__init__(modelType, system_prompt)
        self.mcp_url = mcp_url
        self.conversation_history = []  # 存储完整对话历史
        logger.info(f"初始化MCPChat实例: modelType={modelType}, mcp_url={mcp_url}")
        self.available_tools = self._get_available_tools()
        logger.info(f"可用工具列表: {self.available_tools}")
        
        # 扩展系统提示，包含可用工具信息
        if self.available_tools:
            tool_descriptions = "\n".join([f"- {tool}" for tool in self.available_tools])
            self.system_prompt += f"\n\n可用的MCP工具:\n{tool_descriptions}\n\n你可以通过回复格式为 ```mcp\n{{\"tool\": \"工具名\", \"params\": {{参数字典}}}}\n```的内容来调用工具。"
            logger.info(f"扩展系统提示，添加工具信息: {tool_descriptions}")
    
    def _get_available_tools(self) -> List[str]:
        """获取MCP服务可用的工具列表"""
        try:
            logger.info(f"开始获取MCP可用工具列表: mcp_url={self.mcp_url}")
            tools = run_async(list_mcp_tools())
            logger.info(f"成功获取MCP工具列表: {tools}")
            return tools
        except Exception as e:
            logger.error(f"获取MCP工具列表失败: {str(e)}", exc_info=True)
            return []
    
    def add_message(self, role: str, content: str) -> None:
        """添加消息到对话历史"""
        self.conversation_history.append({"role": role, "content": content})
        logger.info(f"添加消息到历史: role={role}, content={content[:50]}...")
    
    def get_conversation_history(self) -> List[Dict[str, str]]:
        """获取完整对话历史"""
        return self.conversation_history
    
    def get_response(self, user_input: str) -> Dict[str, Any]:
        """处理用户输入并返回响应，支持MCP工具调用"""
        # 添加用户消息到历史
        self.add_message("user", user_input)
        logger.info(f"处理用户输入: {user_input[:50]}...")
        
        # 获取AI响应
        ai_response = super().get_response(user_input)
        response_text = ai_response.get("response", "") if isinstance(ai_response, dict) else ai_response
        logger.info(f"获取到AI响应: {response_text[:100]}...")
        
        self.add_message("assistant", response_text)
        return {"response": response_text, "has_tool_call": False}
    
    async def get_streaming_response(self, user_input: str, callback: Callable[[str, bool], None]) -> None:
        """处理用户输入并以流式方式返回响应
        
        Args:
            user_input: 用户输入文本
            callback: 回调函数，接收部分响应和是否完成的标志
        """
        # 添加用户消息到历史
        self.add_message("user", user_input)
        logger.info(f"开始处理流式响应: {user_input[:50]}...")
        
        # 初始完整响应和当前响应缓冲
        complete_response = ""
        current_buffer = ""
        
        # 获取AI流式响应
        logger.info("开始获取AI流式响应")
        async for chunk in self._get_ai_streaming_response(user_input):
            # 更新完整响应
            complete_response += chunk
            current_buffer += chunk
            
            if current_buffer:
                callback(current_buffer, False)
                current_buffer = ""
        
        # 添加完整响应到对话历史
        self.add_message("assistant", complete_response)
        logger.info("流式响应完成，已添加到对话历史")
        
        # 发送完成信号
        callback("", True)
    
    async def _call_tool_streaming(self, tool_name: str, params: Dict[str, Any]) -> AsyncGenerator[str, None]:
        """调用MCP工具
        
        Args:
            tool_name: 工具名称
            params: 工具参数
            
        Yields:
            工具调用结果的输出
        """
        logger.info(f"开始调用工具: tool_name={tool_name}, params={params}")
        
        # 设置最大尝试次数
        MAX_ATTEMPTS = 5
        attempt = 1
        
        if not tool_name:
            error_msg = "❌ 工具名称不能为空"
            logger.error(error_msg)
            yield error_msg
            return
            
        if tool_name not in self.available_tools:
            available_tools_str = ", ".join(self.available_tools) if self.available_tools else "无可用工具"
            error_msg = f"⚠️ 工具 '{tool_name}' 不可用。可用工具: {available_tools_str}"
            logger.warning(f"工具不可用: {tool_name}, 可用工具: {self.available_tools}")
            yield error_msg
            return
        
        # 记录参数历史，以便检测AI是否修改了参数
        params_history = []
        
        # 重试循环
        while attempt <= MAX_ATTEMPTS:
            logger.info(f"尝试 #{attempt}/{MAX_ATTEMPTS} 调用工具: {tool_name}")
            
            # 记录本次参数
            params_str = json.dumps(params, ensure_ascii=False)
            params_history.append(params_str)
            
            # 初始化错误标志
            has_error = False
            error_message = ""
            
            try:
                # 记录开始调用工具的时间
                start_time = asyncio.get_event_loop().time()
                
                # 流式调用MCP工具并实时返回结果
                logger.info(f"开始调用MCP工具 (尝试 #{attempt}): tool_name={tool_name}, mcp_url={self.mcp_url}")
                yield f"✅ 工具 '{tool_name}' 调用中 (尝试 #{attempt}/{MAX_ATTEMPTS})...\n"
                
                # 调用工具并流式返回结果
                result_count = 0
                total_size = 0
                result_chunks = []  # 收集所有结果块
                
                try:
                    async for result_chunk in call_mcp_tool_streaming(tool_name, params, self.mcp_url):
                        result_count += 1
                        total_size += len(result_chunk)
                        result_chunks.append(result_chunk)
                        
                        logger.info(f"工具调用返回结果块 #{result_count}: 大小={len(result_chunk)}, 内容={result_chunk[:50]}...")
                        
                        # 检查是否为错误消息
                        if result_chunk.startswith("工具调用错误:"):
                            has_error = True
                            error_message = result_chunk
                            logger.warning(f"工具调用返回错误: {error_message}")
                        
                        # 正常返回结果块
                        yield result_chunk
                    
                    # 记录工具调用完成的时间和统计信息
                    end_time = asyncio.get_event_loop().time()
                    duration = end_time - start_time
                    logger.info(f"工具调用完成 (尝试 #{attempt}): tool_name={tool_name}, 用时={duration:.2f}秒, 返回了{result_count}个结果块, 总大小={total_size}字节")
                    
                    if result_count == 0:
                        logger.warning(f"工具调用没有返回任何结果: {tool_name}")
                        yield "工具调用没有返回任何结果"
                        has_error = True
                        error_message = "工具调用没有返回任何结果"
                except Exception as e:
                    logger.error(f"工具调用过程中发生错误: {str(e)}", exc_info=True)
                    error_msg = f"工具调用过程中发生错误: {str(e)}"
                    yield error_msg
                    has_error = True
                    error_message = error_msg
                
                # 结束当前调用的结果块
                yield "\n"
                
                # 如果调用成功或已达到最大尝试次数，则退出循环
                if not has_error or attempt >= MAX_ATTEMPTS:
                    if has_error and attempt >= MAX_ATTEMPTS:
                        logger.warning(f"工具 {tool_name} 调用在 {MAX_ATTEMPTS} 次尝试后仍然失败")
                        yield f"\n已达到最大尝试次数 ({MAX_ATTEMPTS})，工具调用仍然失败。"
                    break
                
                # 否则，准备重试
                retry_prompt = f"\n工具调用失败: {error_message}\n\n请修正参数并重新尝试。这是第 {attempt}/{MAX_ATTEMPTS} 次尝试。"
                yield retry_prompt
                
                # 生成AI响应以获取修正后的参数
                try:
                    # 构造简单的提示，让AI提供修正后的参数
                    ai_prompt = f"工具 '{tool_name}' 调用失败: {error_message}\n请提供修正后的参数。只需要回复JSON格式的参数部分，不要包含其他内容。"
                    
                    # 标记是否接收到了新参数
                    received_new_params = False
                    
                    # 使用流式响应获取AI的建议
                    ai_response = ""
                    logger.info(f"请求AI提供修正后的参数 (尝试 #{attempt})")
                    
                    yield "\n等待AI修正参数...\n"
                    
                    # 使用_get_ai_streaming_response获取AI响应
                    async for ai_chunk in self._get_ai_streaming_response(ai_prompt):
                        ai_response += ai_chunk
                        
                        # 尝试从响应中提取JSON参数
                        json_match = re.search(r'({[\s\S]*?})', ai_response)
                        if json_match and not received_new_params:
                            try:
                                json_str = json_match.group(1)
                                new_params = json.loads(json_str)
                                
                                # 检查是否与之前的参数相同
                                new_params_str = json.dumps(new_params, ensure_ascii=False)
                                if new_params_str not in params_history:
                                    logger.info(f"AI提供了新的参数: {new_params_str}")
                                    params = new_params  # 更新参数
                                    received_new_params = True
                                    yield f"\nAI提供了新的参数: json\n{json.dumps(new_params, indent=2, ensure_ascii=False)}\n"
                                else:
                                    logger.warning("AI提供的参数与之前尝试的参数相同")
                                    yield "\nAI提供的参数与之前尝试的相同，仍将重试...\n"
                            except json.JSONDecodeError:
                                # 继续收集更多响应，可能JSON尚未完整
                                pass
                    
                    # 如果没有成功提取到新参数，记录警告
                    if not received_new_params:
                        logger.warning(f"无法从AI响应中提取有效的JSON参数: {ai_response}")
                        yield "\n无法获取有效的参数修正，将使用原参数重试...\n"
                    
                except Exception as e:
                    logger.error(f"获取AI参数修正时出错: {str(e)}", exc_info=True)
                    yield f"\n获取参数修正失败: {str(e)}，将使用原参数重试...\n"
                
                # 增加尝试次数
                attempt += 1
                
            except Exception as e:
                error_msg = f"❌ 工具 '{tool_name}' 调用失败: {str(e)}"
                logger.error(f"工具调用异常: {error_msg}", exc_info=True)
                yield error_msg
                
                # 如果未达到最大尝试次数，准备重试
                if attempt < MAX_ATTEMPTS:
                    retry_prompt = f"\n工具调用异常: {str(e)}\n\n请修正参数并重新尝试。这是第 {attempt}/{MAX_ATTEMPTS} 次尝试。"
                    yield retry_prompt
                    attempt += 1
                else:
                    logger.warning(f"工具 {tool_name} 调用在 {MAX_ATTEMPTS} 次尝试后仍然失败")
                    yield f"\n已达到最大尝试次数 ({MAX_ATTEMPTS})，工具调用仍然失败。"
                    break
    
    async def _get_ai_streaming_response(self, user_input: str) -> AsyncGenerator[str, None]:
        """获取AI模型的流式响应"""
        # 此处需要实现具体模型的流式响应API调用
        # 以下是示例实现，实际需要根据您使用的AI模型API进行适配
        try:
            # 示例：使用您现有的聊天模型进行流式响应
            # 实际实现中需要替换为调用模型的流式API
            from src.core.mcp.utils import call_streaming_model
            
            logger.info(f"开始调用流式模型: modelType={self.modelType}")
            chunk_count = 0
            async for chunk in call_streaming_model(
                self.modelType,
                user_input,
                self.conversation_history,
                self.system_prompt
            ):
                chunk_count += 1
                yield chunk
            logger.info(f"流式模型调用完成: 共返回{chunk_count}个响应块")
        except Exception as e:
            logger.error(f"流式响应发生错误: {str(e)}", exc_info=True)
            yield f"获取响应时发生错误: {str(e)}"
    
    def _extract_tool_calls(self, text: str) -> List[Dict[str, Any]]:
        """从响应文本中提取MCP工具调用"""
        tool_calls = []
        # 使用正则表达式匹配 ```mcp ... ``` 代码块
        pattern = r"```mcp\s*([\s\S]*?)\s*```"
        matches = re.finditer(pattern, text)
        
        match_count = 0
        for match in matches:
            match_count += 1
            try:
                tool_call_json = match.group(1).strip()
                logger.info(f"提取到工具调用JSON文本: {tool_call_json}")
                
                # 尝试解析JSON
                try:
                    tool_call = json.loads(tool_call_json)
                    
                    # 验证工具调用格式
                    if "tool" in tool_call and "params" in tool_call:
                        tool_name = tool_call["tool"]
                        params = tool_call["params"]
                        logger.info(f"成功解析工具调用: tool={tool_name}, params={params}")
                        
                        # 检查工具是否可用
                        if tool_name in self.available_tools:
                            tool_calls.append(tool_call)
                            logger.info(f"添加有效工具调用: tool={tool_name}")
                        else:
                            logger.warning(f"工具不可用: {tool_name}, 可用工具: {self.available_tools}")
                    else:
                        missing_fields = []
                        if "tool" not in tool_call:
                            missing_fields.append("tool")
                        if "params" not in tool_call:
                            missing_fields.append("params")
                        logger.warning(f"工具调用格式不完整，缺少字段: {', '.join(missing_fields)}, 原始JSON: {tool_call_json}")
                except json.JSONDecodeError as e:
                    logger.error(f"工具调用JSON解析错误: {str(e)}, 位置: {e.pos}, 行: {e.lineno}, 列: {e.colno}, 原始文本: {tool_call_json}")
                    continue
            except Exception as e:
                logger.error(f"处理工具调用时发生未知错误: {str(e)}, 原始匹配: {match.group(0)[:100]}...", exc_info=True)
                continue
                
        logger.info(f"从文本中提取到{len(tool_calls)}/{match_count}个有效工具调用")
        return tool_calls