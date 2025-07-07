# mcp_servers/forecasting_server.py

# Make sure all these imports are present
from mcp.server.fastmcp import FastMCP
from dataclasses import dataclass
from typing import List
import random
import datetime
from calendar import month_name

# Make sure this class is defined correctly
@dataclass
class ForecastResult:
    product_category: str
    labels: List[str]
    data: List[int]

# Make sure this line is correct and the name is in quotes
mcp = FastMCP("FinancialForecastingServer")

@mcp.tool()
def forecast_sales(product_category: str, months_to_forecast: int = 6) -> ForecastResult:
    """
    Generates a dummy sales forecast for a given product category over a specified number of future months.
    In a real-world scenario, this would involve a machine learning model or a complex statistical analysis.
    This tool returns a structured object containing month labels and corresponding sales data.
    """
    labels = []
    data = []
    
    current_sales = random.randint(10000, 25000)
    today = datetime.date.today()

    for i in range(months_to_forecast):
        future_month_num = (today.month + i) % 12 + 1
        future_year = today.year + (today.month + i) // 12
        labels.append(f"{month_name[future_month_num]} {future_year}")
        growth_factor = 1 + random.uniform(0.02, 0.15)
        current_sales = int(current_sales * growth_factor)
        data.append(current_sales)

    return ForecastResult(
        product_category=product_category,
        labels=labels,
        data=data
    )