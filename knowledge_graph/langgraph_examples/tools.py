import datetime
import os

import requests
from dotenv import load_dotenv
from langchain.tools import tool
from langchain_community.tools import DuckDuckGoSearchResults, WikipediaQueryRun
from langchain_community.utilities import DuckDuckGoSearchAPIWrapper, WikipediaAPIWrapper
from langchain_core.tools import Tool
from simpleeval import simple_eval

load_dotenv()

FILE_BASE_PATH = os.getenv("FILE_BASE_PATH", "")

_ddg_wrapper = DuckDuckGoSearchAPIWrapper(region="de-de", time="d", max_results=2)
_ddg_search = DuckDuckGoSearchResults(api_wrapper=_ddg_wrapper)


@tool
def multiply(a: int, b: int) -> int:
    """Multiply `a` and `b`.

    Args:
        a: First int
        b: Second int
    """
    return a * b


@tool
def add(a: int, b: int) -> int:
    """Adds `a` and `b`.

    Args:
        a: First int
        b: Second int
    """
    return a + b


@tool
def divide(a: int, b: int) -> float:
    """Divide `a` and `b`.

    Args:
        a: First int
        b: Second int
    """
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b


@tool
def square(a: int) -> int:
    """Returns the square of a number."""
    return a * a


@tool
def get_current_time(_input=None):
    """Returns the current time in H:MM AM/PM format."""
    now = datetime.datetime.now()
    return now.strftime("%I:%M %p")


@tool
def calc_tool(expression: str) -> str:
    """A simple calculator tool that evaluates mathematical expressions."""
    try:
        result = simple_eval(expression)
        return str(result)
    except Exception as e:
        return f"Error: {str(e)}"


@tool
def read_file(file_name: str) -> str:
    """
    Reads the contents of a file given its file path.
    Returns the file content as a string.
    """
    try:
        full_path = FILE_BASE_PATH + file_name
        if not os.path.exists(full_path):
            return f"Error: The file '{full_path}' does not exist."
        with open(full_path, "r", encoding="utf-8") as file:
            return file.read()
    except Exception as e:
        return f"Error reading file: {str(e)}"


@tool
def ddg_search_tool(query: str) -> str:
    """Search for real-time information from DuckDuckGo."""
    return _ddg_search.run(query)


@tool
def get_weather(city: str) -> str:
    """Provides real-time weather updates for a given city."""
    try:
        api_key = os.getenv("WEATHER_API_KEY")
        if not api_key:
            return "Error: WEATHER_API_KEY is not set."
        url = f"http://api.weatherapi.com/v1/current.json?key={api_key}&q={city}"
        response = requests.get(url)
        response.raise_for_status()
        return str(response.json())
    except requests.RequestException as e:
        return f"Error fetching weather: {str(e)}"


wiki_tool = WikipediaQueryRun(api_wrapper=WikipediaAPIWrapper())


def _google_search_func(query: str) -> str:
    google_api_key = os.getenv("GOOGLE_API_KEY")
    google_cse_id = os.getenv("GOOGLE_CSE_ID")
    if not google_api_key or not google_cse_id:
        return "Error: GOOGLE_API_KEY or GOOGLE_CSE_ID is not set."
    try:
        from langchain_google_community import GoogleSearchAPIWrapper
        return GoogleSearchAPIWrapper().run(query)
    except ImportError:
        return "Error: langchain-google-community is not installed. Run: pip install langchain-google-community"
    except Exception as e:
        return f"Error fetching Google search results: {str(e)}"


google_search_tool = Tool(
    name="Google Search",
    func=_google_search_func,
    description="Use this tool when you need to search for real-time information from Google."
)


def _web_search_with_fallback(query: str) -> str:
    try:
        result = _ddg_search.run(query)
        if result and result.strip() and "No good DuckDuckGo Search Result" not in result:
            return result
    except Exception:
        pass
    return _google_search_func(query)


web_search_tool = Tool(
    name="Web Search",
    func=_web_search_with_fallback,
    description="Search the web. Tries DuckDuckGo first, falls back to Google if no results found."
)


@tool
def negative_customer() -> str:
    """End the conversation when the customer is hostile or abusive."""
    return "Conversation ended."


TOOLS = [
    add,
    multiply,
    divide,
    square,
    get_current_time,
    calc_tool,
    read_file,
    ddg_search_tool,
    get_weather,
    wiki_tool,
    google_search_tool,
    web_search_tool,
    negative_customer,
]
TOOLS_BY_NAME = {t.name: t for t in TOOLS}
