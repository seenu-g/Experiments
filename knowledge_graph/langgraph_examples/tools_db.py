from dotenv import load_dotenv
from langchain_core.tools import tool
from db_orders import get_orders, get_order_by_number

load_dotenv()


@tool
def tool_get_orders(limit: int = 10) -> str:
    """Fetch a list of orders from the database. Returns order details including order number, amount, email, name, mobile, taxes, total and date."""
    orders = get_orders(limit=limit)
    if not orders:
        return "No orders found or database unavailable."
    return "\n".join(str(order) for order in orders)


@tool
def tool_get_order_by_number(order_number: str) -> str:
    """Fetch a single order from the database by its order number (e.g. ORD-001)."""
    order = get_order_by_number(order_number)
    if order is None:
        return f"No order found with order number '{order_number}'."
    return str(order)
