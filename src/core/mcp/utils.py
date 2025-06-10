import asyncio
from fastmcp import Client,FastMCP
from src.core.utils.config import get_env_variable

server_url = get_env_variable("MCP_URL")

async def call_mcp_tool(tool_name, params):
    """
    调用MCP服务的工具函数
    
    Args:
        tool_name: 工具名称
        params: 参数字典
        server_url: MCP服务器URL
        
    Returns:
        工具调用结果
    """
    async with Client(server_url) as client:
        result = await client.call_tool(tool_name, params)
        return result.text

async def list_mcp_tools():
    """
    列出MCP服务可用的工具
    
    Args:
        server_url: MCP服务器URL
        
    Returns:
        可用工具列表
    """
    server_instance = FastMCP(name="TestServer") # In-memory server
    http_url = server_url       # HTTP server URL

    # Client automatically infers the transport type
    client_in_memory = Client(server_instance)
    client_http = Client(http_url)

    print(client_in_memory.transport)
    print(client_http.transport)

    print(server_url)
    async with Client(server_url) as client:
        tools = await client.list_tools()
        return tools

def run_async(coroutine):
    """
    在同步代码中运行异步函数的辅助方法
    
    Args:
        coroutine: 异步协程
        
    Returns:
        协程执行结果
    """
    return asyncio.run(coroutine) 