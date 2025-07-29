from typing  import Any
import httpx
from mcp.server.fastmcp import FastMCP


mcp = FastMCP("weather")
# so we have created a mcp server where "weather" is the name of the server

NWS_API_BASE = "https://api.weather.gov"
USER_AGENT = "weather-mcp/1.0"




# we are adding helper functions

async def make_nws_request(url: str) -> dict[str, Any] | None:
    """
    Make a request to the NWS API and return the response as a dictionary.
    """
    headers = {
        "User-Agent": USER_AGENT, 
        "Accept": "application/geo+json"
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, timeout=30.0)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            return None
        

def format_alert(feature: dict) -> str:
    """Format an alert feature into a readable string."""
    props = feature["properties"]
    return f"""
Event: {props.get('event', 'Unknown')}
Area: {props.get('areaDesc', 'Unknown')}
Severity: {props.get('severity', 'Unknown')}
Description: {props.get('description', 'No description available')}
Instructions: {props.get('instruction', 'No specific instructions provided')}
"""



@mcp.tool()

async def get_alerts(state: str) -> str:
    """Get weather alerts for a given state."""

    url = f"{NWS_API_BASE}/alerts/active/area/{state}"
    data = await make_nws_request(url)

    # print (data) # this is the raw data from the API --> i initially thought that this was the just the GET request we send to the api call

    if not data or "features" not in data:
        return "No alerts found for the given state."
    
    if not data["features"]:
        return "No active alerts for this state."
    
    ## we only need first 3 features from the data - so that the model does not overload
    alerts = [format_alert(feature) for feature in data["features"][:3]]
    return "\n\n".join(alerts)


@mcp.tool()
async def get_forecast(latitude: float, longitude: float) -> str:
    """Get the current weather forecast for a given location."""

    # first lets get the forecast grid endpoint
    points_url = f"{NWS_API_BASE}/points/{latitude},{longitude}"
    points_data = await make_nws_request(points_url)

    if not points_data:
        return "Unable to fetch forecast for this location."
    
    forecast_url = points_data["properties"]["forecast"]
    forecast_data = await make_nws_request(forecast_url)

    # print(forecast_data)

    if forecast_data is None:
        return "Unable to fetch forecast for this location."
    
    
    periods = forecast_data["properties"]["periods"]
    forecasts = []

    for period in periods[:5]:
        forecast = f"""
            Period: {period["name"]}
            Temperature: {period["temperature"]} {period["temperatureUnit"]}
            Wind: {period["windSpeed"]} {period["windDirection"]}
            Forecast: {period["detailedForecast"]}
        """
        forecasts.append(forecast)

    return "\n\n".join(forecasts)

if __name__ == "__main__":
    mcp.run(transport="stdio")







