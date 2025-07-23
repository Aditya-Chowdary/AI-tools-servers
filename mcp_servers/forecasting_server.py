# FILE: mcp_servers/forecasting_server.py

from typing import List, Union, Literal, Optional
from pydantic import BaseModel, Field
import numpy as np
from statsmodels.tsa.arima.model import ARIMA
import warnings

# --- Pydantic Models ---
class PieSlice(BaseModel):
    label: str = Field(description="The name or label for the pie chart slice.")
    value: float = Field(description="The numerical value for the pie chart slice.")

# [NEW] A dedicated model for our two-pie-chart response
class ComparativePieChartResult(BaseModel):
    tool_name: str = Field(default="ComparativePieChartResult", init=False)
    data_name: str
    chart_type: Literal['comparative_pie'] # A new, specific type for the frontend
    historical_pie: List[PieSlice] = Field(description="Data for the first pie chart (Historical).")
    forecast_pie: List[PieSlice] = Field(description="Data for the second pie chart (Forecasted).")

class ForecastResult(BaseModel):
    tool_name: str = Field(default="ForecastResult", init=False)
    data_name: str
    chart_type: Literal["line", "bar", "pie"]
    labels: List[str]
    historical_data: List[Union[int, float, None]]
    forecast_data: List[Union[int, float, None]]


# --- Logic for Line and Bar Chart Forecasting ---
def line_chart_forecast(historical_data: List[float], data_name: str, forecast_periods: int = 4) -> ForecastResult:
    if len(historical_data) < 3: return ForecastResult(data_name=f"Not enough data for '{data_name}'", labels=["Error"], historical_data=[], forecast_data=[], chart_type='line')
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore")
        model = ARIMA(historical_data, order=(1, 1, 0)); model_fit = model.fit()
    forecast = np.maximum(model_fit.forecast(steps=forecast_periods), 0).round(2).tolist()
    forecast_chart_data = [None] * (len(historical_data) - 1) + [historical_data[-1]] + forecast
    labels = [f"P{i+1}" for i in range(len(historical_data) + forecast_periods)]
    return ForecastResult(data_name=data_name, chart_type='line', labels=labels, historical_data=historical_data + [None] * forecast_periods, forecast_data=forecast_chart_data)

def bar_chart_forecast(historical_data: List[float], data_name: str, forecast_periods: int = 4) -> ForecastResult:
    if len(historical_data) < 3: return ForecastResult(data_name=f"Not enough data for '{data_name}'", labels=["Error"], historical_data=[], forecast_data=[], chart_type='line')
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore")
        model = ARIMA(historical_data, order=(1, 1, 0)); model_fit = model.fit()
    forecast = np.maximum(model_fit.forecast(steps=forecast_periods), 0).round(2).tolist()
    forecast_chart_data = [None] * (len(historical_data) - 1) + [historical_data[-1]] + forecast
    labels = [f"P{i+1}" for i in range(len(historical_data) + forecast_periods)]
    return ForecastResult(data_name=data_name, chart_type='bar', labels=labels, historical_data=historical_data + [None] * forecast_periods, forecast_data=forecast_chart_data)


# --- [FIXED] Logic for a single pie chart visualization ---
def pie_chart_visualizer(data_name: str, pie_data: List[Union[PieSlice, dict]]) -> ForecastResult:
    # This ensures that any dictionaries passed from the AI are converted to Pydantic objects.
    parsed_pie_data = [PieSlice(**item) if isinstance(item, dict) else item for item in pie_data]
    chart_labels = [item.label for item in parsed_pie_data]
    chart_values = [item.value for item in parsed_pie_data]
    return ForecastResult(
        data_name=data_name,
        chart_type='pie',
        labels=chart_labels,
        historical_data=chart_values,
        forecast_data=[]
    )

# --- Logic for the two-pie-chart forecast ---
def forecast_and_generate_pie_charts(historical_data: List[float], data_name: str, forecast_periods: int) -> ComparativePieChartResult:
    if len(historical_data) < 3:
        raise ValueError("Not enough historical data to generate a forecast. Please provide at least 3 data points.")
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore")
        model = ARIMA(historical_data, order=(1, 1, 0)); model_fit = model.fit()
    forecasted_values = np.maximum(model_fit.forecast(steps=forecast_periods), 0).round(2).tolist()
    historical_pie_slices = [PieSlice(label=f"Historical Period {i+1}", value=value) for i, value in enumerate(historical_data)]
    forecast_pie_slices = [PieSlice(label=f"Forecast Period {i+1}", value=value) for i, value in enumerate(forecasted_values)]
    return ComparativePieChartResult(
        data_name=data_name,
        chart_type='comparative_pie',
        historical_pie=historical_pie_slices,
        forecast_pie=forecast_pie_slices
    )