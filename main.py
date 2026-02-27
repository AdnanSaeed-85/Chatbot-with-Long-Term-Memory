from langchain_groq import ChatGroq
from langgraph.graph import START, END, StateGraph
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from typing import List, TypedDict, Annotated
import warnings
from CONFIG import GROQ_MODEL, POSTGRES_USER, POSTGRES_DB, POSTGRES_PASSWORD
from langchain_core.messages import AnyMessage, HumanMessage, SystemMessage
from langgraph.graph.message import add_messages
from prompts import SYSTEM_PROMPT_TEMPLATE, MEMORY_PROMPT
from langchain_core.runnables import RunnableConfig
from langgraph.store.base import BaseStore
from langgraph.store.postgres import PostgresStore
import uuid

load_dotenv()

warnings.filterwarnings("ignore", category=UserWarning)

llm = ChatGroq(model=GROQ_MODEL)
llm1 = ChatOpenAI(model='gpt-4o-mini', temperature=0)
llm2 = ChatOpenAI(model='gpt-4o-mini', temperature=1)

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

structured_llm = llm1.with_structured_output(MemoryDecision, include_raw=False)

# -------------------- Remember Node ------------------------
def RememberNode(state: state_message, config: RunnableConfig, store: BaseStore):
    user_id = config['configurable']['user_id']
    namespace = ('user', user_id, 'details')

    items = store.search(namespace)
    existing = '\n'.join(i.value.get('data', '') for i in items)

    last_text = state['messages'][-1].content

    decision: MemoryDecision = structured_llm.invoke(
        [
            SystemMessage(
                MEMORY_PROMPT.format(
                    user_details_content=existing
                )
            ),
            {'role': 'user', 'content': last_text}
        ]
    )

    if decision.should_write:
        for mem in decision.memories:
            if mem.is_new and mem.text.strip():
                store.put(namespace, str(uuid.uuid4()), {"data": mem.text.strip()})

    return {}        

# -------------------- Chat Node ------------------------
def chatnode(state: state_message, config: RunnableConfig, store: BaseStore):
    config = config['configurable']['user_id']
    namespace = ('user', config, 'details')

    items = store.search(namespace)
    user_details = '\n'.join(i.value.get('data', '') for i in items)

    system_message = SystemMessage(
        content=SYSTEM_PROMPT_TEMPLATE.format(
            user_details_content=user_details
        )
    )

    messages = state['messages']
    response = llm2.invoke([system_message] + messages).content
    return {'response': response}

# ------------------- Nodes and Edges -------------------
DB_URI = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@localhost:5442/{POSTGRES_DB}?sslmode=disable"
with PostgresStore.from_conn_string(DB_URI) as store:
    store.setup()
    config = {'configurable': {'user_id': '3'}}
    graph = StateGraph(state_message)

    graph.add_node('chatnode', chatnode)
    graph.add_node('RememberNode', RememberNode)

    graph.add_edge(START, 'RememberNode')
    graph.add_edge('RememberNode', 'chatnode')
    graph.add_edge('chatnode', END)

    chatbot = graph.compile(store=store)

    while True:
        user_input = input('\nuser: ')
        if user_input in ['exit', 'bye']:
            print('Thanks')
            break
        respo = chatbot.invoke(
            {
                'messages': [HumanMessage(content=user_input)]
            },
            config=config
        )
        print(f"Bot: {respo['response']}\n")
        namespace = ('user', config['configurable']['user_id'], 'details')
        personal_messages = store.search(namespace)
        for i in personal_messages:
            print(i.value['data'])
