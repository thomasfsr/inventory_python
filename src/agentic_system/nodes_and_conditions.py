from uuid import UUID
from typing import Union
from langchain_core.runnables import RunnableConfig

from langchain_groq.chat_models import ChatGroq
from langchain_openai.chat_models import ChatOpenAI

from langgraph.graph import StateGraph, END, START
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Send, Command

from langchain_core.messages import AIMessage, HumanMessage
from sqlalchemy.util import ellipses_string

from src.agentic_system.basemodels import *
from src.agentic_system.utils_async import (DatabaseHandler, llm_chain_call, 
                                            struct_output_call)
from src.agentic_system.portuguese_prompts import *
from src.agentic_system.states import *

from dotenv import load_dotenv
_ = load_dotenv()
import os

mix_name : str = os.getenv("MIXTRAL", "")
l70_name = os.getenv("LLAMA3_70B")
l8_name = os.getenv("LLAMA3_8B")
gemma_name = os.getenv("GEMMA2")

mix = ChatGroq(temperature=0, 
                   model = mix_name, 
               api_key = os.getenv('GROQ_KEY', "") # type: ignore
                   )
l70b = ChatGroq(temperature=0, 
                   model = l70_name, 
                   api_key= os.getenv('GROQ_KEY', ""),
                   )
l8b = ChatGroq(temperature=0, 
                   model = l8_name, 
                   api_key= os.getenv('GROQ_KEY', ""),
                   )
gemma = ChatGroq(temperature=0, 
                   model = gemma_name, 
                   api_key= os.getenv('GROQ_KEY', ""),
                   )
gpt = ChatOpenAI(temperature=0,
                 api_key= os.getenv('OPENAI_KEY', ""),
                 verbose=True,
                 model='gpt-4o-mini'
                 )
db_handler = DatabaseHandler()

# Handlers:
async def handle_update(task_description:str, user_id:Union[str, UUID] ,**kwargs):
    system = update_system
    human = f'TASK: {task_description}'
    response = await struct_output_call(system=system, human=human, llm=l70b, basemodel=UpdateBaseModel)
    update = response['parsed']
    tokens = response['raw'].usage_metadata['total_tokens']
    await db_handler.add_total_tokens(user_id=user_id, n_tokens=tokens)
    return {'updates':[update]}

async def handle_query(task_description:str, user_id:Union[str, UUID] , **kwargs):
    system = query_system.format(user_id=user_id)
    human = f'TASK: {task_description}'
    response = await struct_output_call(system=system, human=human, llm=l70b, basemodel=SQLQueryBaseModel)
    query = response['parsed']
    tokens = response['raw'].usage_metadata['total_tokens']
    await db_handler.add_total_tokens(user_id=user_id, n_tokens=tokens)
    query_result = await db_handler.query(query.query)
    treated_answer = await llm_chain_call(system=treat_query_system, 
                                    human=f'Tarefa requisitada: {task_description}, comando SQL executado:{query.query} e resultado da query: {str(query_result)}', 
                                    llm=l70b)
    treated_answer.role = "assistant"
    await db_handler.add_total_tokens(user_id=user_id, n_tokens=treated_answer.usage_metadata['total_tokens'])
    return {'messages':[treated_answer], 'sql_queries':[query],'sql_results':[query_result]}

async def handle_chatting(task_description:str, chat_history:str, user_id:Union[str, UUID] , **kwargs):
    user_name = await db_handler.user_name(user_id)
    system = chatting_system.format(chat_history=chat_history)
    human = f'user {user_name} message: {task_description}'
    chat_answer = await llm_chain_call(system=system, human=human, llm=l70b)
    await db_handler.add_total_tokens(user_id=user_id, n_tokens=chat_answer.usage_metadata['total_tokens'])
    chat_answer.role = "assistant"
    return {'messages':[chat_answer]}

async def handle_subtract(user_id, item_name, quantity, **kwargs):
    existing_item, message_not_found = await db_handler.check_existing_item(user_id=user_id, item_name=item_name)
    if existing_item:
        return await db_handler.subtract_to_existing_item(user_id=user_id, item_name=item_name, quantity=quantity)
    return message_not_found

async def handle_add(user_id: int,
                     item_name: str,
                     quantity: float,
                     unit: str,
                     category: str | None = None, 
                     desc: str | None = None,
                     loc: str | None = None,
                     **kwargs):
    
    is_in_db, _ = await db_handler.check_existing_item(user_id=user_id, item_name=item_name)

    if is_in_db:
        return await db_handler.add_to_existing_item(user_id=user_id, item_name=item_name, quantity=quantity)
    return await db_handler.creating_new_item(user_id=user_id, 
                                              item_name=item_name, 
                                              quantity=quantity, 
                                              desc=desc, loc=loc, 
                                              unit=unit, 
                                              category= category)

async def handle_discard_all(user_id, item_name, **kwargs):
    existing_item, message_not_found = await db_handler.check_existing_item(user_id=user_id, item_name=item_name)
    if existing_item:
        return await db_handler.discard_all_to_existing_item(user_id=user_id, item_name=item_name)
    return message_not_found

async def handle_rename(user_id, old_item_name, new_item_name, **kwargs):
    return await db_handler.renaming_existing_item(user_id=user_id, old_item_name=old_item_name, new_item_name=new_item_name)

async def handle_change_unit(user_id, item_name, unit, **kwargs):
    return await db_handler.change_unit(user_id=user_id, item_name=item_name, unit=unit)

# Nodes and Conditions:

async def extract_tasks(state: OverallState, config: RunnableConfig):
    user_id = config["configurable"].get("user_id", None)
    user_input = state['user_input']
    human_message = HumanMessage(content=user_input, role='user')
    system = extract_tasks_system
    response = await struct_output_call(system=system, human=user_input, llm=l70b, basemodel=ListTaskModel)
    task_list = response['parsed']
    tokens = response['raw'].usage_metadata['total_tokens']
    await db_handler.add_total_tokens(user_id=user_id, n_tokens=tokens)
    return {'task_list': task_list.task_list, 
            'user_id': user_id, 
            'messages':[human_message],
            'updates':['<ERASELISTNOW>'],
            'sql_queries':['<ERASELISTNOW>'],
            'sql_results':['<ERASELISTNOW>']}

def send_tasks(state:OverallState):
    return [Send('map_tasks',
                 {'task': t, 'messages': state['messages']}) 
             for t in state['task_list']
             ]


async def map_tasks(state: TaskState, config:RunnableConfig):
    user_id = config['configurable']['user_id']
    task = state['task']
    messages = state.get('messages', [])
    try:
        chat_history = '\n'.join([msg.content for msg in messages])
    except:
        chat_history = ''
    task_description = task.task
    label = task.label.value
    if label ==None:
        label = 'chatting'
    task_map = {'update': handle_update, 
                'query':handle_query, 
                'chatting':handle_chatting}
    handler = task_map.get(label)
    return await handler(user_id=user_id, chat_history=chat_history, task_description=task_description)

def agg_tasks(state: OverallState):
    updates = state.get('updates',[])
    if updates:
        c = Command(goto=[Send("process_update", {"update": u}) for u in updates])
    else:
        c= Command(goto=END)
    return c

async def process_update(state: UpdateState, config: RunnableConfig):
    user_id = config["configurable"].get("user_id", None)
    update = state.get('update', [])

    item_name = update.item_name
    quantity = update.quantity
    unit = update.unit.value
    old_item_name = update.old_item_name
    new_item_name = update.new_item_name
    category = update.category
    action = update.action.value
    loc = update.location
    desc = update.description

    action_handlers = {
    'subtract': handle_subtract,
    'add': handle_add,
    'discard_all': handle_discard_all,
    'rename': handle_rename,
    'change_unit': handle_change_unit}

    handler = action_handlers.get(action)

    message = await handler(
        user_id=user_id,
        item_name=item_name,
        quantity=quantity,
        unit=unit,
        old_item_name=old_item_name,
        new_item_name=new_item_name,
        category=category,
        desc=desc,
        loc=loc
    )
    assistant_msg = AIMessage(role="assistant", content=message)
    return {'messages':[assistant_msg]}

class Graph:
    def __init__(self):
        memory = MemorySaver()
        graph = StateGraph(OverallState)

        graph.add_node('extract_tasks', extract_tasks)
        graph.add_edge(START, 'extract_tasks')
        graph.add_node('map_tasks', map_tasks)
        graph.add_conditional_edges('extract_tasks',send_tasks, ['map_tasks'])
        graph.add_node('agg_tasks',agg_tasks)
        graph.add_edge('map_tasks', 'agg_tasks')
        graph.add_node('process_update', process_update)
        graph.add_edge('process_update', END)
        self.graph = graph.compile(checkpointer=memory)
    
    async def async_invoking(self, config:Config, message:str):     
        await self.graph.ainvoke(input={'user_input':message}, config=config)
 
    async def async_state(self, config:Config):
        return await self.graph.aget_state(config=config)
    
    def response(self, config:Config):
        messages = self.graph.get_state(config=config).values['messages']
        last_ia_messages = ''
        for m in reversed(messages):
            if m.role == "user":
                break
            else:
                last_ia_messages+=f"{m.content} \n"
        return last_ia_messages
