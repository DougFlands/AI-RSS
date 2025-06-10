import asyncio
import pytest
from unittest.mock import AsyncMock, patch

from src.core.mcp import run_basic_client, run_advanced_client, run_multi_server_client

@pytest.mark.asyncio
async def test_basic_client():
    """测试基本客户端功能"""
    with patch('fastmcp.Client') as mock_client:
        # 设置模拟客户端的行为
        mock_instance = AsyncMock()
        mock_instance.list_tools.return_value = ["tool1", "tool2"]
        mock_instance.call_tool.return_value.text = "工具调用结果"
        mock_instance.read_resource.return_value.content = "资源内容"
        mock_instance.sample.return_value.text = "采样结果"
        
        # 设置上下文管理器返回模拟实例
        mock_client.return_value.__aenter__.return_value = mock_instance
        
        # 调用要测试的函数
        with patch('builtins.print') as mock_print:
            await run_basic_client()
        
        # 验证调用
        mock_client.assert_called_once()
        mock_instance.list_tools.assert_called_once()
        mock_instance.call_tool.assert_called_once()
        mock_instance.read_resource.assert_called_once()
        mock_instance.sample.assert_called_once()
        
        # 验证打印输出
        assert mock_print.call_count >= 4  # 至少有4次打印输出

@pytest.mark.asyncio
async def test_advanced_client():
    """测试高级客户端功能，包括认证和采样处理"""
    with patch('fastmcp.Client') as mock_client:
        # 设置模拟客户端的行为
        mock_instance = AsyncMock()
        mock_instance.list_tools.return_value = ["secure_tool1", "secure_tool2"]
        mock_instance.call_tool.return_value.text = "安全工具调用结果"
        mock_instance.read_resource.return_value.content = "安全资源内容"
        
        # 设置上下文管理器返回模拟实例
        mock_client.return_value.__aenter__.return_value = mock_instance
        
        # 调用要测试的函数
        with patch('builtins.print') as mock_print:
            await run_advanced_client()
        
        # 验证调用
        mock_client.assert_called_once()
        mock_instance.list_tools.assert_called_once()
        mock_instance.call_tool.assert_called_once()
        mock_instance.read_resource.assert_called_once()
        
        # 验证打印输出
        assert mock_print.call_count >= 3  # 至少有3次打印输出

@pytest.mark.asyncio
async def test_multi_server_client():
    """测试多服务器客户端功能"""
    with patch('fastmcp.Client') as mock_client:
        # 设置模拟客户端的行为
        mock_instance = AsyncMock()
        mock_instance.call_tool.side_effect = [
            AsyncMock(text="数据服务器结果"),
            AsyncMock(text="AI服务器结果")
        ]
        mock_instance.read_resource.side_effect = [
            AsyncMock(content="数据资源内容"),
            AsyncMock(content="AI资源内容")
        ]
        
        # 设置上下文管理器返回模拟实例
        mock_client.return_value.__aenter__.return_value = mock_instance
        
        # 调用要测试的函数
        with patch('builtins.print') as mock_print:
            await run_multi_server_client()
        
        # 验证调用
        mock_client.assert_called_once()
        assert mock_instance.call_tool.call_count == 2
        assert mock_instance.read_resource.call_count == 2
        
        # 验证打印输出
        assert mock_print.call_count >= 4  # 至少有4次打印输出 