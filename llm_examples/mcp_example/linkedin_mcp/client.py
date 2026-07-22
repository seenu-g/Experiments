from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

server_params = StdioServerParameters(
    command="mcp",
    args=["run", "server.py"],
    env=None,
)


async def run():
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            tools = await session.list_tools()
            print("LISTING TOOLS")
            for tool in tools.tools:
                print("Tool: ", tool.name)

            print("\nCALL TOOL: get_my_profile")
            result = await session.call_tool("get_my_profile", arguments={})
            for item in result.content:
                print(item.text)

            if post_text:
                post_args = {"text": post_text}
                if link_url:
                    post_args["link_url"] = link_url
                    if link_title:
                        post_args["link_title"] = link_title
                print(f"\nCALL TOOL: create_post({post_args!r})")
                result = await session.call_tool("create_post", arguments=post_args)
                for item in result.content:
                    print(item.text)
                    if item.text.startswith("published: "):
                        post_urn = item.text.removeprefix("published: ")
                        print(f"\nCALL TOOL: get_post(post_urn={post_urn!r})")
                        result = await session.call_tool("get_post", arguments={"post_urn": post_urn})
                        for item in result.content:
                            print(item.text)

            if get_urn:
                print(f"\nCALL TOOL: get_post(post_urn={get_urn!r})")
                result = await session.call_tool("get_post", arguments={"post_urn": get_urn})
                for item in result.content:
                    print(item.text)


if __name__ == "__main__":
    import argparse
    import asyncio

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--post",
        metavar="TEXT",
        help="Actually publish a LinkedIn post with this text (omit to skip -- posting is real and public).",
    )
    parser.add_argument(
        "--get-post",
        metavar="URN",
        help="Fetch an existing post by URN instead of/in addition to creating one.",
    )
    parser.add_argument(
        "--link",
        metavar="URL",
        help="Attach this URL as an article link card to the --post (ignored without --post).",
    )
    parser.add_argument(
        "--link-title",
        metavar="TITLE",
        help="Title for the --link card (ignored without --link; defaults to the URL itself).",
    )
    args = parser.parse_args()

    post_text = args.post
    get_urn = args.get_post
    link_url = args.link
    link_title = args.link_title
    asyncio.run(run())
