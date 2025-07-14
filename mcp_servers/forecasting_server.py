from typing import List, Union
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field
from dotenv import load_dotenv
import numpy as np
# Import the ARIMA model
from statsmodels.tsa.arima.model import ARIMA

load_dotenv()
app = FastMCP("ForecastingServer")

class ForecastResult(BaseModel):
    tool_name: str = Field(default="ForecastResult", init=False)
    data_name: str = Field(description="The name for the data series being forecasted.")
    labels: List[str] = Field(description="The labels for the x-axis.")
    historical_data: List[Union[int, float, None]] = Field(description="The historical data points.")
    forecast_data: List[Union[int, float, None]] = Field(description="The forecasted data points, padded with nulls.")

@app.tool()
def forecast_data(historical_data: List[float], data_name: str, forecast_periods: int = 4) -> ForecastResult:
    """
    Generates a realistic forecast using an ARIMA time-series model based on historical data.
    'historical_data' should be a list of numbers, e.g., [110, 125, 150, 142, 168, 180].
    'data_name' is the name for the data, e.g., 'New User Signups'.
    'forecast_periods' is the number of future time periods to predict.
    """
    if len(historical_data) < 5: 
        return ForecastResult(data_name=f"Error for '{data_name}'", labels=["Error"], historical_data=[], forecast_data=[])
    
    try:
        model = ARIMA(historical_data, order=(2, 1, 1))
        model_fit = model.fit()
        
       
        forecast = model_fit.forecast(steps=forecast_periods)
        
     
        forecasted_points = np.maximum(forecast, 0).tolist() # Ensure no negative predictions
        forecasted_points = [round(p, 2) for p in forecasted_points]
        
        last_historical_value = historical_data[-1]
        forecast_chart_data = [None] * (len(historical_data) - 1) + [last_historical_value] + forecasted_points

        labels = [f"P{i+1}" for i in range(len(historical_data) + forecast_periods)]
        
        return ForecastResult(
            data_name=data_name,
            labels=labels,
            historical_data=historical_data + [None] * forecast_periods,
            forecast_data=forecast_chart_data
        )
    except Exception as e:
        print(f"ARIMA model error: {e}")
        return ForecastResult(data_name=f"Could not forecast '{data_name}'", labels=["Error"], historical_data=[], forecast_data=[])