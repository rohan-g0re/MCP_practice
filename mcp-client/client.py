import asyncio
import os
from typing import Optional
from contextlib import AsyncExitStack

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()  # load environment variables from .env

class MCPClient:
    def __init__(self):
        # Initialize session and client objects
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()

        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY environment variable is required")
        self.gemini_client = genai.Client(api_key=api_key)
    
    # methods will go here

    async def connect_to_server(self, server_script_path: str):
        """Connect to an MCP server

        Args:
            server_script_path: Path to the server script (.py or .js)
        """
        is_python = server_script_path.endswith('.py')
        is_js = server_script_path.endswith('.js')
        if not (is_python or is_js):
            raise ValueError("Server script must be a .py or .js file")

        command = "uv" if is_python else "node"

        server_params = StdioServerParameters(
            command=command,
            args=[
                "--directory",
                "D:\\STUFF\\Projects\\MCP_Projects\\weather",
                "run",
                "weather.py"
            ],
            env=None
        )

        stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
        self.stdio, self.write = stdio_transport
        self.session = await self.exit_stack.enter_async_context(ClientSession(self.stdio, self.write))

        await self.session.initialize()

        # List available tools
        response = await self.session.list_tools()
        tools = response.tools
        print("\nConnected to server with tools:", [tool.name for tool in tools])
        return tools

    def convert_mcp_tools_to_gemini(self, mcp_tools):
        """Convert MCP tools to Gemini function declarations format"""
        gemini_tools = []
        
        for tool in mcp_tools:
            function_declaration = types.FunctionDeclaration(
                name=tool.name,
                description=tool.description,
                parameters=tool.inputSchema
            )
            gemini_tools.append(function_declaration)
        
        return gemini_tools

    async def process_query(self, query: str) -> str:
        """Process a query using Gemini and available tools"""
        try:
            # Get available MCP tools
            response = await self.session.list_tools()
            mcp_tools = response.tools
            
            if not mcp_tools:
                # No tools available, just use Gemini directly
                response = self.gemini_client.models.generate_content(
                    model="gemini-2.0-flash-exp",
                    contents=query,
                    config=types.GenerateContentConfig(
                        temperature=0.7,
                        max_output_tokens=1000,
                    )
                )
                return self._extract_text_from_response(response)
            
            # Convert MCP tools to Gemini format
            gemini_tools = self.convert_mcp_tools_to_gemini(mcp_tools)
            
            # Create tools object for Gemini
            tools = [types.Tool(function_declarations=gemini_tools)]
            
            # Initial Gemini API call with tools
            response = self.gemini_client.models.generate_content(
                model="gemini-2.0-flash-exp",
                contents=query,
                config=types.GenerateContentConfig(
                    tools=tools,
                    temperature=0.7,
                    max_output_tokens=1000,
                )
            )
            
            # Process response and handle tool calls
            final_text = []
            
            if hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                
                for part in candidate.content.parts:
                    if hasattr(part, 'text') and part.text:
                        final_text.append(part.text)
                    elif hasattr(part, 'function_call'):
                        # Execute the function call via MCP
                        function_name = part.function_call.name
                        function_args = dict(part.function_call.args) if part.function_call.args else {}
                        
                        print(f"[Calling tool {function_name} with args {function_args}]")
                        
                        try:
                            # Execute tool call via MCP session
                            result = await self.session.call_tool(function_name, function_args)
                            
                            # Format the tool result content
                            if hasattr(result, 'content') and result.content:
                                if isinstance(result.content, list):
                                    tool_result = "\n".join([str(item.text) if hasattr(item, 'text') else str(item) for item in result.content])
                                else:
                                    tool_result = str(result.content)
                            else:
                                tool_result = "Tool executed successfully but returned no content."
                            
                            # Continue conversation with function result
                            follow_up_contents = [
                                types.Content(role="user", parts=[types.Part(text=query)]),
                                types.Content(role="model", parts=[types.Part(function_call=types.FunctionCall(
                                    name=function_name, 
                                    args=function_args
                                ))]),
                                types.Content(role="user", parts=[types.Part(function_response=types.FunctionResponse(
                                    name=function_name, 
                                    response={"result": tool_result}
                                ))])
                            ]
                            
                            follow_up_response = self.gemini_client.models.generate_content(
                                model="gemini-2.0-flash-exp",
                                contents=follow_up_contents,
                                config=types.GenerateContentConfig(
                                    tools=tools,
                                    temperature=0.7,
                                    max_output_tokens=1000,
                                )
                            )
                            
                            follow_up_text = self._extract_text_from_response(follow_up_response)
                            if follow_up_text:
                                final_text.append(follow_up_text)
                                
                        except Exception as e:
                            final_text.append(f"Error executing tool {function_name}: {str(e)}")
            else:
                # No function calls, just return the text response
                text_response = self._extract_text_from_response(response)
                if text_response:
                    final_text.append(text_response)
            
            return "\n".join(final_text) if final_text else "No response generated."
        
        except Exception as e:
            return f"Error processing query: {str(e)}"

    def _extract_text_from_response(self, response):
        """Helper method to extract text from Gemini response"""
        if hasattr(response, 'text'):
            return response.text
        elif hasattr(response, 'candidates') and response.candidates:
            candidate = response.candidates[0]
            text_parts = []
            for part in candidate.content.parts:
                if hasattr(part, 'text') and part.text:
                    text_parts.append(part.text)
            return "\n".join(text_parts) if text_parts else None
        return None

    async def chat_loop(self):
        """Run an interactive chat loop"""
        print("\nMCP Client Started!")
        print("Type your queries or 'quit' to exit.")

        while True:
            try:
                query = input("\nQuery: ").strip()

                if query.lower() == 'quit':
                    break

                response = await self.process_query(query)
                print("\n" + response)

            except Exception as e:
                print(f"\nError: {str(e)}")

    async def cleanup(self):
        """Clean up resources"""
        await self.exit_stack.aclose()

    
async def main():
    import sys
    if len(sys.argv) < 2:
        print("Usage: python client.py <path_to_server_script>")
        sys.exit(1)

    client = MCPClient()
    try:
        await client.connect_to_server(sys.argv[1])
        await client.chat_loop()
    finally:
        await client.cleanup()

if __name__ == "__main__":
    asyncio.run(main())