import os
import asyncio
import json
from dapr_agents import Agent
from dapr_agents.tool.mcp.client import MCPClient
from dotenv import load_dotenv

# טעינת משתני סביבה מקובץ .env
load_dotenv()

# הגדרות והנחיות זהות לאלו שבסקריפט הראשי שלך
instructions = [
    "You are an expert N1QL (Couchbase) query specialist with 10+ years of experience.",
    "ROLE: Senior N1QL Database Engineer specializing in JSON document querying and optimization.",
    "SESSION BEHAVIOR: Use schema discovery tools only during initialization. For query generation, rely on provided schema context.",
    "OPTIMIZATION FOCUS: Generate syntactically correct, performance-optimized SQL++ queries using established schema knowledge.",
    "If something is unclear about the data structure, refer to the session's schema context first before asking clarifying questions."
]

# הפרומפט שברצוננו לבדוק
discovery_prompt = (
    "INITIALIZATION TASK: Discover and document the complete bucket structure:\n"
    "1. Use CouchbaseMcpGetScopesAndCollectionsInBucket to map all scopes and collections.\n"
    "2. For each collection found ONLY in the `_default` scope (explicitly ignore the `_system` scope), use CouchbaseMcpGetSchemaForCollection.\n"
    "3. Summarize all findings from the previous steps into a final, structured JSON format to be used as context.\n\n"
)

async def run_discovery_test():
    """
    Main function to initialize the agent and run the discovery prompt test.
    """
    print("--- Starting Discovery Test ---")

    mcp_url = os.getenv("MCP_SERVER_URL")
    if not mcp_url:
        print("🛑 Error: MCP_SERVER_URL environment variable not set.")
        return

    client = MCPClient(timeout=120.0)
    try:
        print(f"🔗 Connecting to MCP server at {mcp_url}...")
        await client.connect_sse(
            server_name="couchbase_mcp",
            url=mcp_url,
            headers=None,
        )
        print("✅ Connection to MCP server successful.")
    except Exception as e:
        print(f"🛑 Failed to connect to MCP Server: {e}")
        return

    tools = client.get_all_tools()
    tool_names = ", ".join([tool.name for tool in tools])
    print(f"🛠️  Discovered Tools: {tool_names}")

    agent = Agent(
        name="DiscoveryAgent",
        role="Couchbase Schema Expert",
        instructions=instructions,
        tools=tools,
    )
    print("🤖 Agent initialized.")

    print("\n🚀 Running discovery prompt... (This may take a moment)")
    try:
        schema_discovery_result = await agent.run(discovery_prompt)
        
        print("\n--- DISCOVERY RESULT ---")
        print(schema_discovery_result.content) # <-- שינוי קטן כאן
        print("------------------------")

        # --- התיקון המרכזי כאן ---
        try:
            # 1. שלוף את תוכן הטקסט מהאובייקט
            result_content = schema_discovery_result.content
            
            with open('schema_context.json', 'w', encoding='utf-8') as f:
                # 2. חלץ את ה-JSON מתוך תוכן הטקסט
                json_start = result_content.find('{')
                json_end = result_content.rfind('}') + 1
                if json_start != -1 and json_end != -1:
                    json_content = result_content[json_start:json_end]
                    parsed_json = json.loads(json_content)
                    json.dump(parsed_json, f, indent=2, ensure_ascii=False)
                else:
                    f.write(result_content)

            print("\n✅ Successfully wrote schema to schema_context.json")
        except Exception as e:
            print(f"🛑 Error writing to file: {e}")
        # --------------------------

    except Exception as e:
        print(f"🛑 An error occurred during agent execution: {e}")

        
# --- נקודת הכניסה להרצת הסקריפט ---
if __name__ == "__main__":
    asyncio.run(run_discovery_test())
# -----------------------------------