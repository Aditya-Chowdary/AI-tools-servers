# mcp_servers/all_tools_server.py

from mcp.server.fastmcp import FastMCP
# Import everything you need for all tools
from dataclasses import dataclass
from typing import List, Optional
import os
import random
import datetime
from calendar import month_name
import requests
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import pandas as pd
import numpy as np
from statsmodels.tsa.statespace.sarimax import SARIMAX


# Give the consolidated server a single name
mcp = FastMCP("AllToolsServer")

# --- From freelance_server.py ---
@dataclass
class StructuredProposal:
    # ... (dataclass definition)
    client_name: str
    project_title: str
    overview: str
    deliverables: List[str]
    timeline: str
    next_steps: str

@mcp.tool()
def generate_project_proposal(client_name: str, project_description: str) -> StructuredProposal:
    # ... (tool implementation)
    if not project_description:
        title = "Generic Project Proposal"
    else:
        title = f"Custom Solution for {project_description.split()[0].capitalize()}"
    return StructuredProposal(client_name=client_name, project_title=title, overview=f"...", deliverables=["..."], timeline="4-6 weeks", next_steps="...")


# --- From video_server.py ---
@dataclass
class VideoScript:
    # ... (dataclass definition)
    title: str
    script_pas_framework: str

@mcp.tool()
def create_video_script(product_name: str, primary_pain_point: str, target_audience: str) -> VideoScript:
    # ... (tool implementation)
    script = f"..."
    return VideoScript(title=f"VSL for {product_name}", script_pas_framework=script)

# --- From forecasting_server.py ---
@dataclass
class ForecastResult:
    # ... (dataclass definition)
    product_category: str
    labels: List[str]
    historical_data: List[int]
    forecast_data: List[int]

def generate_historical_data(category: str, periods: int = 24):
    # ... (helper function implementation)
    base_sales = 15000
    dates = pd.date_range(end=datetime.date.today(), periods=periods, freq='MS')
    trend = np.linspace(0, 5000, periods)
    sales_data = base_sales + trend
    return pd.Series(sales_data.astype(int), index=dates)

@mcp.tool()
def forecast_sales(product_category: str, months_to_forecast: int = 6) -> ForecastResult:
    # ... (tool implementation)
    historical_series = generate_historical_data(product_category)
    model = SARIMAX(historical_series, order=(1, 1, 1), seasonal_order=(1, 1, 1, 12))
    results = model.fit(disp=False)
    forecast = results.get_forecast(steps=months_to_forecast)
    predicted_series = forecast.predicted_mean.astype(int)
    all_labels = [d.strftime('%b %Y') for d in historical_series.index] + [d.strftime('%b %Y') for d in predicted_series.index]
    historical_values = list(historical_series.values) + [None] * months_to_forecast
    forecast_values = [None] * len(historical_series) + list(predicted_series.values)
    return ForecastResult(product_category=product_category, labels=all_labels, historical_data=historical_values, forecast_data=forecast_values)


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
# --- ... Add ALL your other tools here in the same way ... ---