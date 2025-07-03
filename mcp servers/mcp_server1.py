# dummy_server.py
from mcp.server.fastmcp import FastMCP
from dataclasses import dataclass
from typing import List

# --- Data Structures (can be shared across tools) ---
@dataclass
class UserProfile:
    user_id: str
    name: str
    email: str
    role: str

# --- MCP Server Setup ---
mcp = FastMCP("DummyToolDemo")

# --- Dummy Tools ---

@mcp.tool()
def get_user_profile(user_id: str) -> UserProfile:
    """
    Retrieves a dummy user profile based on a user ID.
    In a real application, this would query a database.
    """
    print(f"INFO: Fetching profile for user_id: {user_id}")
    # Dummy implementation: return a hardcoded profile
    return UserProfile(
        user_id=user_id,
        name="Alex Ray",
        email="alex.ray@example.com",
        role="Administrator"
    )

@mcp.tool()
def send_notification(user_id: str, message: str) -> dict:
    """
    Sends a notification to a user.
    This dummy version just prints to the console and returns a success status.
    """
    print(f"--- NOTIFICATION ---")
    print(f"To: {user_id}")
    print(f"Message: {message}")
    print(f"--------------------")
    # Dummy implementation: return a status dictionary
    return {"status": "success", "message_sent": True}

@mcp.tool()
def check_inventory(product_id: str, quantity: int) -> dict:
    """
    Checks if a certain quantity of a product is available in the inventory.
    """
    print(f"INFO: Checking inventory for {quantity} of {product_id}")
    # Dummy logic: any quantity over 10 is "out of stock"
    if quantity > 10:
        return {"product_id": product_id, "available": False, "stock": 5}
    else:
        return {"product_id": product_id, "available": True, "stock": 100}

@mcp.tool()
def schedule_meeting(title: str, attendees: List[str], time: str) -> dict:
    """
    Schedules a new meeting with a list of attendees.
    The list of attendees should be provided as email addresses.
    """
    print(f"INFO: Scheduling meeting '{title}' at {time}")
    print(f"INFO: Inviting attendees: {', '.join(attendees)}")
    # Dummy implementation: return a confirmation
    meeting_id = f"meet_{product_id[:4]}" # A simple, predictable ID
    return {
        "status": "scheduled",
        "meeting_id": meeting_id,
        "title": title,
        "attendees": attendees
    }