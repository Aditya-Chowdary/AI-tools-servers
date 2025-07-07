from mcp.server.fastmcp import FastMCP
from dataclasses import dataclass

mcp = FastMCP("MeetingSummarizerServer")

@dataclass
class MeetingSummary:
    summary_text: str

@mcp.tool()
def summarize_meeting_transcript(transcript_text: str) -> MeetingSummary:
    """Summarizes a long meeting transcript into key points and action items."""
    # Dummy summarization logic
    key_points = "1. Discussed Q3 financial results.\n2. Agreed on the new marketing strategy."
    action_items = "- [ ] Alex to finalize the budget report by EOD Friday.\n- [ ] Sarah to draft the client follow-up email."
    summary = f"**Meeting Summary**\n\n**Key Points:**\n{key_points}\n\n**Action Items:**\n{action_items}"
    return MeetingSummary(summary_text=summary)