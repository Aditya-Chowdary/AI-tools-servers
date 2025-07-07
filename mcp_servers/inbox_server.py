from mcp.server.fastmcp import FastMCP
from dataclasses import dataclass

mcp = FastMCP("InboxZeroServer")

@dataclass
class EmailCategory:
    category: str
    priority: str

@mcp.tool()
def categorize_email(subject: str, sender: str) -> EmailCategory:
    """Categorizes an incoming email as Important, Promotion, or Spam."""
    subject = subject.lower()
    sender = sender.lower()
    if "invoice" in subject or "meeting" in subject or "urgent" in subject:
        return EmailCategory(category="Important", priority="High")
    elif "sale" in subject or "discount" in subject or "newsletter" in subject:
        return EmailCategory(category="Promotions", priority="Low")
    else:
        return EmailCategory(category="General", priority="Medium")