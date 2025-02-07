from pydantic import BaseModel
import uuid
from datetime import datetime
from typing import List

class TagsModel(BaseModel):
    uid:uuid.UUID
    name:str
    created_at:datetime

class TagsCreateModel(BaseModel):
    name:str

class TagsAddModel(BaseModel):
    tags:List[str]
