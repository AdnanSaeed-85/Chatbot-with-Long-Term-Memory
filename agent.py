import asyncio
import uuid
import warnings
from typing import List, TypedDict, Annotated

from langsmith import traceable
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import AnyMessage, HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph import START, END, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from pydantic import BaseModel, Field
from langgraph.types import Command

from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.store.postgres import PostgresStore
from langgraph.store.base import BaseStore
from CONFIG import GROQ_MODEL, POSTGRES_USER, POSTGRES_DB, POSTGRES_PASSWORD
from prompts import SYSTEM_PROMPT_TEMPLATE, MEMORY_PROMPT
from langchain_mcp_adapters.client import MultiServerMCPClient
from tools import karavan_rag

load_dotenv()
warnings.filterwarnings("ignore", category=UserWarning)

# ----------------- Configuration & MCP --------------------
SERVERS = {
    "tools": {
        "transport": "sse",
        "url": "https://dynamic-purple-blackbird.fastmcp.app/mcp"
    }
}

# ----------------- Models --------------------
llm1 = ChatOpenAI(model='gpt-4o-mini', temperature=0)
llm2 = ChatOpenAI(model='gpt-4o-mini')

# ----------------- Pydantic Schemas --------------------
class state_message(TypedDict):
    messages: Annotated[List[AnyMessage], add_messages]

class MemoryItems(BaseModel):
    text: str = Field(..., description="Atomic user memory")
    is_new: bool = Field(..., description="True if new, else False")

class MemoryDecision(BaseModel):
    should_write: bool = Field(...)
    memories: List[MemoryItems] = Field(default_factory=list)

structured_llm = llm1.with_structured_output(MemoryDecision)

# -------------------- Remember Node ------------------------
@traceable(name="Remember Agent")
def RememberNode(state: state_message, config: RunnableConfig, store: BaseStore):
    user_id = config['configurable']['user_id']
    namespace = ('user', user_id, 'details')

    items = store.search(namespace)
    existing = '\n'.join(i.value.get('data', '') for i in items)

    last_text = state['messages'][-1].content

    decision: MemoryDecision = structured_llm.invoke(
        [
            SystemMessage(
                content=MEMORY_PROMPT.format(user_details_content=existing)
            ),
            HumanMessage(content=last_text)
        ]
    )

    if decision.should_write:
        for mem in decision.memories:
            if mem.is_new and mem.text.strip():
                store.put(namespace, str(uuid.uuid4()), {"data": mem.text.strip()})

    return {}

# ------------------- Graph Construction & Execution -------------------
async def main():
    print("Connecting to MCP server...")
    client = MultiServerMCPClient(SERVERS)
    mcp_tools = await client.get_tools()
    print(f"--- Loaded MCP: {[t.name for t in mcp_tools]} ---")
    print(f"--- Loaded Tools: {[karavan_rag.name]} ---")

    llm_with_tools = llm2.bind_tools(mcp_tools + [karavan_rag])

    async def chatnode(state: state_message, config: RunnableConfig, store: BaseStore):
        user_id = config['configurable']['user_id']
        namespace = ('user', user_id, 'details')

        items = store.search(namespace)
        user_details = '\n'.join(i.value.get('data', '') for i in items)

        system_message = SystemMessage(
            content=SYSTEM_PROMPT_TEMPLATE.format(user_details_content=user_details)
        )

        messages = state['messages']
        response = await llm_with_tools.ainvoke([system_message] + messages)
        
        return {"messages": [response]}

    DB_URI = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@localhost:5442/{POSTGRES_DB}?sslmode=disable"

    async with AsyncPostgresSaver.from_conn_string(DB_URI) as checkpointer:
        await checkpointer.setup()
        with PostgresStore.from_conn_string(DB_URI) as store:
            store.setup()
            
            builder = StateGraph(state_message)

            builder.add_node('chatnode', chatnode)
            builder.add_node('RememberNode', RememberNode)
            builder.add_node('tools', ToolNode(mcp_tools + [karavan_rag]))
            builder.add_edge(START, 'RememberNode')
            builder.add_edge('RememberNode', 'chatnode')
            
            builder.add_conditional_edges('chatnode', tools_condition)
            builder.add_edge('tools', 'chatnode')

            chatbot = builder.compile(
                store=store,
                checkpointer=checkpointer
                )

            config = {'configurable': {'user_id': 'a5', 'thread_id': 'A5'}}

            while True:
                user_input = input('\nuser: ')
                if user_input.lower() in ['exit', 'bye', 'quit']:
                    print('Thanks')
                    break

                input_data = {"messages": [HumanMessage(content=user_input)]}

                while True:
                    interrupted = False

                    async for update in chatbot.astream(
                        input_data,
                        config=config,
                        stream_mode=["updates", "messages"]
                    ):
                        mode, data = update
                        if mode == "updates":
                            if "__interrupt__" in data:
                                interrupt_data = data["__interrupt__"][0].value
                                print(f"\nHITL: {interrupt_data}")
                                decision = input("your decision: ").strip()
                                input_data = Command(resume=decision)
                                interrupted = True
                                break

                        elif mode == "messages":
                            msg_chunk, metadata = data
                            if (metadata.get("langgraph_node") == "chatnode" and hasattr(msg_chunk, "content") and msg_chunk.content):
                                print(msg_chunk.content, end="", flush=True)

                    if not interrupted:
                        break

                print()
                print("\n--- Current Stored Memories ---")
                namespace = ('user', config['configurable']['user_id'], 'details')
                personal_messages = store.search(namespace)
                for i in personal_messages:
                    print(i.value['data'])
                print("-------------------------------")

if __name__ == '__main__':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())