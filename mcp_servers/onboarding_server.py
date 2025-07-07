from mcp.server.fastmcp import FastMCP
from dataclasses import dataclass

mcp = FastMCP("ClientOnboardingServer")

@dataclass
class OnboardingChecklist:
    checklist: str

@mcp.tool()
def generate_onboarding_checklist(client_name: str, service_type: str) -> OnboardingChecklist:
    """Generates a step-by-step onboarding checklist for a new client."""
    checklist = (
        f"**Onboarding Checklist for {client_name} ({service_type} Service)**\n\n"
        f"- [ ] Welcome email sent.\n"
        f"- [ ] Schedule kick-off call.\n"
        f"- [ ] Grant access to project management tool.\n"
        f"- [ ] Collect necessary documents and assets.\n"
        f"- [ ] First check-in call completed."
    )
    return OnboardingChecklist(checklist=checklist)