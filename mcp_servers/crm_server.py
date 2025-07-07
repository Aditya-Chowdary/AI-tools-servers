# mcp_servers/crm_server.py (Upgraded)
from mcp.server.fastmcp import FastMCP
from dataclasses import dataclass
import datetime

mcp = FastMCP("CRMFollowUpServer")

@dataclass
class EmailDraft:
    recipient: str
    subject: str
    body: str

@mcp.tool()
def draft_follow_up_email(customer_name: str, last_interaction: str, days_since_interaction: int) -> EmailDraft:
    """Drafts a personalized follow-up email, mentioning the time since the last interaction."""
    
    today = datetime.date.today()
    interaction_date = today - datetime.timedelta(days=days_since_interaction)
    
    subject = f"Following up on our conversation"
    
    body = (
        f"Hi {customer_name},\n\n"
        f"I hope you're having a great week.\n\n"
        f"I'm just following up on our conversation from {interaction_date.strftime('%B %d')} about **{last_interaction}**. "
        f"Has there been any new development on your end? I'm here to help if you have any further questions.\n\n"
        f"Looking forward to hearing from you.\n\n"
        f"Best regards,\nVishesh AI Agent"
    )
    return EmailDraft(
        recipient=f"{customer_name.lower().replace(' ', '.')}@example.com",
        subject=subject,
        body=body
    )