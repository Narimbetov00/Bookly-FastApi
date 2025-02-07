from fastapi import APIRouter,Depends
from sqlmodel.ext.asyncio.session import AsyncSession


from src.auth.dependencies import RoleChecker
from src.books.schemas import Book
from src.db.main import get_session

from .schemas import TagsCreateModel,TagsModel,TagsAddModel
from .service import TagService

from typing import List
from src.errors import TagNotFound

tags_router = APIRouter()
tag_service = TagService()
role_checker = Depends(RoleChecker(['admin','User']))



@tags_router.get('/',response_model=List[TagsModel])
async def get_all_tags(session:AsyncSession =Depends(get_session)):
    tags = await tag_service.get_tags(session)

    return tags

@tags_router.post('/',response_model=TagsModel)
async def add_tags(
    tag_data:TagsCreateModel,session:AsyncSession=Depends(get_session)
):
    tag_added = await tag_service.add_tag(tag_data,session)

    return tag_added

@tags_router.post('/book/{book_uid}/tags',response_model=Book)
async def add_tag_to_book(
    book_uid:str,tag_data:TagsAddModel,session:AsyncSession=Depends(get_session)
):
    book_with_tag = await tag_service.add_tags_to_book(
        book_uid=book_uid,tag_data=tag_data,session=session
    )
    return book_with_tag

@tags_router.put('/{tag_uid}',response_model=TagsModel)
async def update_tags(
    tag_uid:str,tag_update_data:TagsCreateModel,session:AsyncSession=Depends(get_session)
):
    update_tag = await tag_service.update_tag(
        tag_uid,tag_update_data,session
    )
    return update_tag

@tags_router.delete('/{tag_uid}',response_model=TagsModel)
async def delete_tags(
    tag_uid:str,session:AsyncSession=Depends(get_session)
):
    delete_tag = await tag_service.delete_tag(
        tag_uid,session
    )
    return delete_tag
    