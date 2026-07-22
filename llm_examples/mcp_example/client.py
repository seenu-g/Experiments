from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

server_params = StdioServerParameters(
    command="mcp",  # Executable
    args=["run", "server.py"],  # Optional command line arguments
    env=None,  # Optional environment variables
)

async def run():
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(
            read, write
        ) as session:
            # Initialize the connection
            await session.initialize()

            resources = await session.list_resources()
            print("LISTING RESOURCES")
            for resource in resources.resources:
                print("Resource: ", resource)

            tools = await session.list_tools()
            print("LISTING TOOLS")
            for tool in tools.tools:
                print("Tool: ", tool.name)

            print("READING RESOURCE")
            resource_result = await session.read_resource("greeting://hello")
            for item in resource_result.contents:
                print("Content: ", item.text, "MIME type: ", item.mimeType)

            print("CALL TOOL")
            result = await session.call_tool("add", arguments={"a": 1, "b": 7})
            print(result.content)


if __name__ == "__main__":
    import asyncio

    asyncio.run(run())