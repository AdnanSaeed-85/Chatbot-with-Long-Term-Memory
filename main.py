from langchain_groq import ChatGroq
from langgraph.graph import START, END, StateGraph
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from typing import List, TypedDict, Annotated
from CONFIG import GROQ_MODEL
from langchain_core.messages import AnyMessage, HumanMessage, SystemMessage
from langgraph.graph.message import add_messages
from prompts import SYSTEM_PROMPT_TEMPLATE
from langchain_core.runnables import RunnableConfig
from langgraph.store.base import BaseStore
from langgraph.store.postgres import PostgresStore
load_dotenv()

llm = ChatGroq(model=GROQ_MODEL)

# ----------------- Pydantic Schemas --------------------
class state_message(TypedDict):
    messages: Annotated[List[AnyMessage], add_messages]
    response: str

class MemoryItems(BaseModel):
    text: str = Field(..., description="Atomic user memory")
    is_new: bool = Field(..., description="True if new, else False")

class MemoryDecision(BaseModel):
    should_write: bool = Field(...)
    memories: List[MemoryItems] = Field(default_factory=list)

structured_llm = llm.with_structured_output(MemoryDecision)

# -------------------- Remember Node ------------------------
def RememberNode(state: state_message):
    pass

# -------------------- Chat Node ------------------------
def chatnode(state: state_message):
    messages = state['messages']
    response = llm.invoke(messages).content
    return {'response': response}

# ------------------- Nodes and Edges -------------------
graph = StateGraph(state_message)
graph.add_node('chatnode', chatnode)
graph.add_edge(START, 'chatnode')
graph.add_edge('chatnode', END)
chatbot = graph.compile()

while True:
    user_input = input('user: ')
    if user_input in ['exit', 'bye']:
        print('Thanks')
        break
    respo = chatbot.invoke(
        {
            'messages': [HumanMessage(content=user_input)]
        }
    )
    print(respo['response'])