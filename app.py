import os
import json
import chainlit as cl
from dapr_agents import Agent
from dapr_agents.tool.mcp.client import MCPClient
from dapr_agents.llm.dapr import DaprChatClient
from dotenv import load_dotenv

load_dotenv()

def create_prompt_for_llm(user_question: str, schema_context: str) -> str:
    """
    Loads the prompt template from an external file and formats it with dynamic content.
    """
    prompt_file_path = os.path.join('prompts', 'llm_router_prompt.txt')
    try:
        with open(prompt_file_path, 'r', encoding='utf-8') as f:
            prompt_template = f.read()
    except FileNotFoundError:        
        error_message = f"Error: Prompt file not found at '{prompt_file_path}'. Please ensure it exists."        
        raise FileNotFoundError(error_message)

    # Use the .format() method to inject the dynamic variables into the template
    return prompt_template.format(
        user_question=user_question,
        schema_context=schema_context
    )

@cl.on_chat_start
async def start():
    """
    Initializes the agent when a new chat session starts.
    """
    instructions = [
        "You are an expert N1QL (Couchbase) query specialist with 10+ years of experience.",
        "ROLE: Senior N1QL/SQL++ Database Engineer specializing in JSON document querying and optimization.",
        "SESSION BEHAVIOR: For query generation, rely on the already provided schema context."
    ]
    # Load the schema context from the JSON file
    try:
        with open('schema_context.json', 'r', encoding='utf-8') as f:
            schema_context = f.read()
    except FileNotFoundError:
        await cl.Message(content="Error: `schema_context.json` not found. Please run `cb_discovery.py` script first to generate it.").send()
        return
    cl.user_session.set("schema_context", schema_context)

    component_name = os.getenv("DAPR_LLM_COMPONENT_DEFAULT", "openai")
    # Initialize the LLM agent - this agent will handle the LLM routing and SQL++ query generation
    llm_agent = Agent(
        name="llm_agent",
        role="Senior SQL++ Couchbase Database Expert Engineer specializing in SQL++ Couchbase querying and optimization.",
        instructions=instructions,
        llm=DaprChatClient(component_name=component_name)
    )
    cl.user_session.set("llm_agent", llm_agent)

    # Connect to the MCP Server    
    mcp_url = os.getenv("MCP_SERVER_URL")
    if not mcp_url:
        await cl.Message(content="Error: MCP_SERVER_URL environment variable not set.").send()
        return
    client = MCPClient(timeout=60.0)
    try:
        await client.connect_sse(server_name="couchbase_mcp", url=mcp_url, headers=None)
    except Exception as e:
        await cl.Message(content=f"Error: Failed to connect to MCP Server: {e}").send()
        return          
    tools = client.get_all_tools()
    #cl.user_session.set("tools", tools)
    if not tools:
        await cl.Message(content="Error: Tools not initialized. Please restart the chat.").send()
        return
    
    # Initialize the MCP Tool Agent - this agent will handle the SQL++ query execution
    tools_agent = Agent(
                name="tools_agent",
                role="Execution agent using couchbase mcp tools.",                
                instructions=[
                "You are an Execution agent using mcp tools to query the Couchbase.",
                "if given sql++ query, use the mcp tools to execute it. Do not change the query."
                ],               
                tools=tools                
            )

    cl.user_session.set("tools_agent", tools_agent)           
        
    await cl.Message(content="✅ Couchbase Agent is ready. How can I help?").send()

@cl.on_message
async def main(message: cl.Message):
    """Handles incoming user messages."""      
    llm_agent = cl.user_session.get("llm_agent")
    if not llm_agent:
               await cl.Message(content="Error: llm_agent  not initialized. Please restart the chat.").send()
               return
    schema_context = cl.user_session.get("schema_context")   
    # Build the optimized prompt to create a SQL++ query or answer the question directly
    prompt = create_prompt_for_llm(message.content, schema_context)  
    try:
        result: AssistantMessage = await llm_agent.run(prompt) 

        prefix = 'Tool needed:' # This prefix indicates that the MCP Tool Agent should be used
        if result.content.startswith(prefix):
            #If tools needed continue with MCP Tool Agent
                tools_agent = cl.user_session.get("tools_agent")
                if not tools_agent:
                    await cl.Message(content="Error: Tools agent not initialized. Please restart the chat.").send()
                    return
                sql_query = result.content[len(prefix):].strip()
                await cl.Message(content=f"⚙️ **Tool identified.** Executing query:\n```sql\n{sql_query}\n```").send()                     
                execution_prompt = f"execute the following sql++ query using the mcp tools : {sql_query}"
                # Run the SQL++ query using the MCP Tool Agent
                result_set: AssistantMessage = await tools_agent.run(execution_prompt)
                final_answer = result_set.content.strip()
        else:
            # If no tools are needed, respond directly with the answer
            final_answer = result.content.strip()  
        # Send the final answer back to the user
        await cl.Message(content=f"✅ **Answer:** {final_answer}").send()
    except Exception as e:
        # A single, robust catch-all for any error in the workflow
        await cl.Message(content=f"🚨 An error occurred during processing: {str(e)}").send()
