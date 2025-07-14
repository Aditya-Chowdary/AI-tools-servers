from pydantic import BaseModel, Field
from typing import List

class MeetingConfirmation(BaseModel):
    status: str
    topic: str
    attendees: List[str]
    time: str

def schedule_meeting(topic: str, attendees: List[str], date_time: str) -> MeetingConfirmation:
    """Schedules a meeting and sends a confirmation."""
    print(f"SCHEDULING: Meeting '{topic}' for {', '.join(attendees)} at {date_time}")
    return MeetingConfirmation(status="Scheduled", topic=topic, attendees=attendees, time=date_time)