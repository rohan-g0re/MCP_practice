Following documentation to create MCP servers. ONly One change that I used Gemini for LLM in `mcp-client\client.py` instead of an anthropic key.

You can run the setup with following steps:

1. Create uv or python based venv --> and activate it using .\.venv\Scripts\activate

2. add requirements using `pip install` or `uv add`

3. run with command: `uv run client.py <_path_>weather\\weather.py`

4. Test Queries to verify working:

    Query 1: List the tools available via MCP.

    Query 2: what is the status at latitude: 47.6062 and longitude: -122.3325 --> use mcp tool get_forecast.

    Query 3: alerts in state of NY