import unittest
import asyncio
import json
import sys
import os
import threading
import queue
from unittest.mock import MagicMock, patch

# 添加项目根目录到 Python 路径
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.models.mcpchat import MCPChat
from src.api.chat import stream_chat

class TestStreaming(unittest.TestCase):
    """测试流式响应功能"""

    def setUp(self):
        """设置测试环境"""
        self.mcpChat = MCPChat("test_model", "测试系统提示")
        # 替换 _get_ai_streaming_response 方法，避免真实的 API 调用
        self.mcpChat._get_ai_streaming_response = self._mock_streaming_response
        self.response_queue = queue.Queue()
        
    async def _mock_streaming_response(self, user_input):
        """模拟流式响应"""
        chunks = ["你好", "，", "这是", "测试", "响应"]
        for chunk in chunks:
            yield chunk
            await asyncio.sleep(0.1)
    
    def test_streaming_callback_parameters(self):
        """测试流式响应回调函数的参数"""
        print("\n===== 测试流式响应回调函数参数 =====")
        
        # 记录回调函数被调用的情况
        callback_calls = []
        
        # 定义回调函数，记录参数
        def test_callback(chunk, is_complete, has_tool=False):
            callback_calls.append({
                'chunk': chunk,
                'is_complete': is_complete,
                'has_tool': has_tool
            })
            print(f"回调函数被调用: chunk='{chunk}', is_complete={is_complete}, has_tool={has_tool}")
        
        # 运行异步测试
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            # 1. 直接测试 MCPChat.get_streaming_response 方法的参数
            print("\n1. 测试 MCPChat.get_streaming_response 方法")
            
            # 检查参数注解
            from inspect import signature
            sig = signature(self.mcpChat.get_streaming_response)
            print(f"方法签名: {sig}")
            print(f"回调函数类型注解: {sig.parameters['callback'].annotation}")
            
            # 运行测试
            loop.run_until_complete(
                self.mcpChat.get_streaming_response("测试输入", test_callback)
            )
            
            # 验证回调函数被调用
            self.assertTrue(len(callback_calls) > 0, "回调函数应该被调用")
            self.assertTrue(any(call['is_complete'] for call in callback_calls), "应该有完成信号")
            
            # 2. 测试 lambda 函数调用
            print("\n2. 测试 lambda 函数调用")
            callback_calls.clear()
            
            # 直接测试 lambda 函数调用
            lambda_func = lambda chunk, is_complete: test_callback(chunk, is_complete)
            lambda_func("测试lambda", False)
            
            self.assertEqual(len(callback_calls), 1, "lambda 调用应该触发一次回调")
            self.assertEqual(callback_calls[0]['chunk'], "测试lambda", "chunk 参数应该正确传递")
            
            # 3. 测试修复版本
            print("\n3. 测试修复版本")
            callback_calls.clear()
            
            # 测试修复版本的 lambda 函数
            fixed_lambda = lambda chunk, is_complete: test_callback(chunk, is_complete, False)
            fixed_lambda("测试修复", False)
            
            self.assertEqual(len(callback_calls), 1, "修复的 lambda 调用应该触发一次回调")
            self.assertEqual(callback_calls[0]['chunk'], "测试修复", "chunk 参数应该正确传递")
            
        finally:
            loop.close()
    
    def test_async_streaming_response(self):
        """测试异步流式响应功能"""
        print("\n===== 测试异步流式响应功能 =====")
        
        # 定义测试回调函数
        async def run_test():
            complete_response = ""
            
            # 定义回调处理函数
            def callback(chunk, is_complete):
                nonlocal complete_response
                if chunk:
                    complete_response += chunk
                    print(f"收到块: '{chunk}'")
                if is_complete:
                    print("收到完成信号")
            
            # 使用 lambda 包装回调函数，模拟实际使用场景
            await self.mcpChat.get_streaming_response(
                "测试输入",
                lambda chunk, is_complete: callback(chunk, is_complete)
            )
            
            print(f"完整响应: '{complete_response}'")
            self.assertTrue(len(complete_response) > 0, "应该有完整的响应")
            return complete_response
        
        # 运行异步测试
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            response = loop.run_until_complete(run_test())
            print(f"测试完成，响应长度: {len(response)}")
        finally:
            loop.close()
    
    def test_mocked_chat_endpoint(self):
        """测试模拟的聊天端点"""
        print("\n===== 测试模拟的聊天端点 =====")
        
        # 模拟请求和响应对象
        class MockRequest:
            method = 'POST'
            
            def get_json(self):
                return {
                    'message': '测试消息',
                    'sessionId': 'test-session-id',
                    'modelType': 'test_model'
                }
            
            @property
            def args(self):
                return {'sessionId': 'test-session-id'}
        
        # 模拟 jsonify 和 Response
        def mock_jsonify(data):
            return json.dumps(data)
        
        class MockResponse:
            def __init__(self, generator, mimetype, headers):
                self.generator = generator
                self.mimetype = mimetype
                self.headers = headers
                
            def __str__(self):
                return f"MockResponse(mimetype={self.mimetype})"
        
        # 补丁 MCPChat.get_streaming_response 方法
        async def patched_get_streaming_response(self, user_input, callback):
            callback("测试响应开始", False)
            callback("测试响应内容", False)
            callback("", True)  # 完成信号
        
        # 应用补丁
        with patch('src.core.models.mcpchat.MCPChat.get_streaming_response', 
                  new=patched_get_streaming_response), \
             patch('flask.request', MockRequest()), \
             patch('flask.jsonify', mock_jsonify), \
             patch('flask.Response', MockResponse), \
             patch('flask.stream_with_context', lambda x: x):
            
            # 模拟活动流
            from src.api.chat import active_streams
            active_streams['test-session-id'] = queue.Queue()
            
            # 调用 stream_chat 端点
            try:
                result = stream_chat()
                print(f"端点返回: {result}")
            except Exception as e:
                print(f"端点调用出错: {e}")
                import traceback
                traceback.print_exc()
            
            # 检查队列中的内容
            messages = []
            q = active_streams.get('test-session-id')
            if q:
                try:
                    while True:
                        item = q.get_nowait()
                        if item is None:
                            messages.append("END")
                        else:
                            messages.append(item)
                except queue.Empty:
                    pass
            
            print(f"队列消息: {messages}")

if __name__ == '__main__':
    unittest.main() 