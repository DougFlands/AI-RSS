#!/usr/bin/env python
import asyncio
from fastmcp import Client

# 
async def test_mcp_server(server_url: str):
    async with Client(server_url) as client:
        tools = await client.list_tools()
        print(tools)


server_url = "http://10.11.12.10:8089/mcp"

print(f"Testing MCP server at: {server_url}")

asyncio.run(test_mcp_server(server_url))
