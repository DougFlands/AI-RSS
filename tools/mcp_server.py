from fastmcp import FastMCP

# 启动一个 mcp server 服务，用于测试
mcp = FastMCP(name="MyServer", port="8080")

@mcp.tool
def greet(name: str) -> str:
    """Greet a user by name."""
    return f"Hello, {name}!"

mcp.run(transport="streamable-http")