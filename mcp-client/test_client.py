# #!/usr/bin/env python3
# """
# Test script for MCP client with Gemini integration
# """
# import asyncio
# import sys
# import os
# from client import MCPClient

# async def test_client():
#     """Test the MCP client with various queries"""
    
#     # Check if API key is set
#     if not os.getenv("GOOGLE_API_KEY"):
#         print("❌ Error: GOOGLE_API_KEY environment variable not set")
#         print("Please create a .env file with:")
#         print("GOOGLE_API_KEY=your_api_key_here")
#         return False
    
#     if len(sys.argv) < 2:
#         print("Usage: python test_client.py <path_to_weather_server>")
#         print("Example: python test_client.py D:\\STUFF\\Projects\\MCP_Projects\\weather\\weather.py")
#         return False
    
#     server_path = sys.argv[1]
    
#     # Test connection
#     print("🔄 Testing MCP Client...")
#     client = MCPClient()
    
#     try:
#         print(f"📡 Connecting to server: {server_path}")
#         tools = await client.connect_to_server(server_path)
#         print(f"✅ Connected successfully! Available tools: {[tool.name for tool in tools]}")
        
#         # Test queries
#         test_queries = [
#             "What's the weather forecast for latitude 37.7749 and longitude -122.4194?",
#             "Are there any weather alerts for California?",
#             "Tell me about the weather in general"
#         ]
        
#         for i, query in enumerate(test_queries, 1):
#             print(f"\n🧪 Test {i}: {query}")
#             print("🤖 Response:")
#             response = await client.process_query(query)
#             print(response)
#             print("-" * 50)
        
#         print("\n✅ All tests completed successfully!")
#         return True
        
#     except Exception as e:
#         print(f"❌ Error during testing: {str(e)}")
#         return False
#     finally:
#         await client.cleanup()

# if __name__ == "__main__":
#     success = asyncio.run(test_client())
#     sys.exit(0 if success else 1)