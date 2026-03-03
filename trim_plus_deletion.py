from dotenv import load_dotenv
from langchain.messages import RemoveMessage
from langgraph.graph import START, END, StateGraph, MessagesState
from langchain_core.messages import HumanMessage
from langchain_groq import ChatGroq
from CONFIG import GROQ_MODEL
from langgraph.checkpoint.memory import InMemorySaver

load_dotenv()

llm = ChatGroq(model=GROQ_MODEL)

def chatnode(state: MessagesState):
    messages = state['messages']
    response = llm.invoke(messages)
    return {'messages': [response]}

def cleanup(state: MessagesState):
    messages = state['messages']
    
    if len(messages) > 10:
        remove = messages[:6]

        return {'messages': RemoveMessage(id=m.id) for m in remove}
    
graph = StateGraph(MessagesState)

graph.add_node('chatnode', chatnode)
graph.add_node('cleanup', cleanup)

graph.add_edge(START, 'chatnode')
graph.add_edge('chatnode', 'cleanup')
graph.add_edge('cleanup', END)

bot = graph.compile(checkpointer=InMemorySaver())

config = {'configurable': {'thread_id': 'id_1'}}

while True:
    user_input = input('User: ')
    if user_input in ['exit', 'clear']:
        print('Thanks.')
        break
    respo = bot.invoke(
        {
            'messages': [HumanMessage(content=user_input)]
        },
        config=config
    )

    print(f"Assistant: {respo['messages'][-1].content}\n")

print('*'*80)
print(f"Length of total messags are:- {len(bot.get_state(config).values['messages'])}")