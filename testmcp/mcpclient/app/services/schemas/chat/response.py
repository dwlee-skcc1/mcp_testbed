from typing import List, Optional, Dict

from pydantic import BaseModel, Field

class SampleResponse(BaseModel):
    answer:str

class RfqDraftAction(BaseModel):
    id:int=Field(description="The order of the action")
    name:str = Field(description="Name of the action")
    description:str = Field(description="Description of the action")
    tool:str = Field(description="Tool to be used in the action")
    parameters:Optional[Dict] = Field(description="Parameters of the tool")

class RfqDraftStep(BaseModel):
    id:int=Field(description="The order of the step")
    name:str = Field(description="Name of the step")
    description:str = Field(description="Description of the step")
    actions:List[RfqDraftAction] = Field(description="List of actions")

class RfqDraftResponse(BaseModel):
    steps:List[RfqDraftStep] = Field(description="List of steps")