from typing import TypedDict, List, Annotated
from langchain_core.messages import AnyMessage
from src.agentic_system.basemodels import *

from typing import List
def add_with_limit_for_messages(a:List,b:List) -> List:
    c = a + b
    return c[-10:]

def add_or_erase(a:List,b:List) -> List:
    c = a + b
    if '<ERASELISTNOW>' in c:
        c = []
    return c

class OverallState(TypedDict):
    user_id: int
    user_input: str
    messages: Annotated[List[AnyMessage], add_with_limit_for_messages]
    task_list: ListTaskModel 
    updates: Annotated[List[UpdateBaseModel], add_or_erase]
    sql_queries: Annotated[List[SQLQueryBaseModel], add_or_erase]
    sql_results: Annotated[list, add_or_erase]

class TaskState(TypedDict):
    task: TaskModel
    messages: List[AnyMessage]

class UpdateState(TypedDict):
    update: UpdateBaseModel

class Configurable(TypedDict):
    thread_id: Union[int,str]
    user_id: int
class Config(TypedDict):
    configurable:Configurable