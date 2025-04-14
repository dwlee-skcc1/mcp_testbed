from langchain_core.messages import BaseMessage
from typing_extensions import TypedDict
from typing import List, Dict

class State(TypedDict):

    user_query:str
    messages: List[Dict]
    tool:List[str]
    answer:str