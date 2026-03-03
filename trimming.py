from langchain_core.messages.utils import trim_messages, count_tokens_approximately
from langchain_groq import ChatGroq
from CONFIG import GROQ_MODEL
from dotenv import load_dotenv
from langgraph.graph import START, END, MessagesState, StateGraph
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import InMemorySaver

load_dotenv()

llm = ChatGroq(model=GROQ_MODEL)

MAX_TOKENS = 1000

def trimming(state: MessagesState):
    messages = trim_messages(
        state['messages'],
        strategy='last',
        token_counter = count_tokens_approximately,
        max_tokens=MAX_TOKENS
    )

    print(f'Current token counts = {count_tokens_approximately(messages=messages)}')

    response = llm.invoke(messages)

    return {'messages': response.content}

graph = StateGraph(MessagesState)

checkpointer = InMemorySaver()

graph.add_node('trimming', trimming)
graph.add_edge(START, 'trimming')
graph.add_edge('trimming', END)

bot = graph.compile(checkpointer=checkpointer)

config = {'configurable': {'thread_id': 't2'}}

while True:
    user_input = input('User: ')
    if user_input in ['exit', 'clear','bye']:
        break
    output = bot.invoke(
    {
        'messages': [HumanMessage(content=user_input)]
    },
    config=config
)
    print(f"{output['messages'][-1].content}\n")