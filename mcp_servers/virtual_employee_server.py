from mcp.server.fastmcp import FastMCP
from dataclasses import dataclass
from typing import List

mcp = FastMCP("VirtualEmployeeServer")

@dataclass
class MeetingConfirmation:
    status: str
    topic: str
    attendees: List[str]
    time: str

@mcp.tool()
def schedule_appointment(topic: str, attendees: List[str], date_time: str) -> MeetingConfirmation:
    """Schedules an appointment or meeting with a given topic, list of attendees, and time."""
    print(f"Scheduling meeting '{topic}' for {', '.join(attendees)} at {date_time}")
    return MeetingConfirmation(
        status="Scheduled",
        topic=topic,
        attendees=attendees,
        time=date_time
    )