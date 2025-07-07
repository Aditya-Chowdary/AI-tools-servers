from mcp.server.fastmcp import FastMCP
from dataclasses import dataclass

mcp = FastMCP("CRMFollowUpServer")

@dataclass
class EmailDraft:
    draft: str

@mcp.tool()
def draft_follow_up_email(customer_name: str, last_interaction: str) -> EmailDraft:
    """Drafts a personalized follow-up email for a customer based on their last interaction in the CRM."""
    draft = (
        f"**Subject:** Following Up\n\n"
        f"Hi {customer_name},\n\n"
        f"Just wanted to follow up on our last conversation about **{last_interaction}**.\n\n"
        f"Do you have any further questions? Let me know how I can help.\n\n"
        f"Best regards,\nVishesh AI Agent"
    )
    return EmailDraft(draft=draft)