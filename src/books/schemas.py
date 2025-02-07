from pydantic import BaseModel,validator
import uuid
from datetime import datetime,date
from typing import List
from src.reviews.schemas import ReviewModel
from src.tags.schemas import TagsModel
class Book(BaseModel):
    uid:uuid.UUID
    title:str
    author:str
    publisher:str
    published_date:str
    page_count:int
    language:str
    created_at:datetime
    update_at:datetime

class BookDetailModel(Book):
    reviews:List[ReviewModel]
    tags:List[TagsModel]

class BookCreateModel(BaseModel):
    title:str
    author:str
    publisher:str
    published_date:str
    page_count:int
    language:str


class BookUpdate(BaseModel):
    title:str
    author:str
    publisher:str
    page_count:int
    language:str