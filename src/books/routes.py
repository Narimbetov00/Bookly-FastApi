from fastapi import APIRouter,Depends
from .schemas import Book,BookUpdate,BookCreateModel,BookDetailModel
from src.tags.schemas import TagsModel
from src.reviews.schemas import ReviewModel
from src.db.models import Tags
from src.auth.schemas import UserBooksModel
from typing import List
from fastapi.exceptions import HTTPException
from src.db.main import get_session
from sqlmodel.ext.asyncio.session import AsyncSession
from src.books.service import BookService
from src.auth.dependencies import AccessTokenBearer,RoleChecker
from sqlalchemy.future import select
from src.errors import BookNotFound
book_router = APIRouter()
book_service = BookService()
access_token_bearer = AccessTokenBearer()
role_checker = Depends(RoleChecker(['admin','User']))

@book_router.get("/",response_model=List[Book],dependencies=[role_checker])
async def get_all_books(session:AsyncSession = Depends(get_session),token_details=Depends(access_token_bearer)):
    books = await book_service.get_all_books(session)
    return books


@book_router.get("/user/{user_uid}",response_model=List[Book],dependencies=[role_checker])
async def get_user_book_submissions(user_uid:str,session:AsyncSession = Depends(get_session),token_details=Depends(access_token_bearer)):

    books = await book_service.get_user_books(user_uid,session)
    return books

@book_router.post("/",response_model=Book,dependencies=[role_checker])
async def create_a_book(book_data:BookCreateModel,session:AsyncSession = Depends(get_session),token_details:dict=Depends(access_token_bearer)):
    user_id = token_details.get("user")["user_uid"]
    new_book = await book_service.create_book(book_data,user_id,session)
    return new_book

@book_router.get("/{book_uid}",response_model=BookDetailModel,dependencies=[role_checker])
async def get_book(book_uid:str,session:AsyncSession = Depends(get_session),token_details=Depends(access_token_bearer)):
    book = await book_service.get_book(book_uid,session)
    
    if not book:
        raise BookNotFound()

    result = await session.execute(select(Tags).where(Tags.uid.in_(book.tags)))  # book.tags -> UUID lar
    tags_list = result.scalars().all()

    
    tags_objects = [TagsModel(uid=t.uid, name=t.name, created_at=t.created_at) for t in tags_list]

    return BookDetailModel(
        uid=book.uid,
        title=book.title,
        author=book.author,
        publisher=book.publisher,
        published_date=book.published_date,
        page_count=book.page_count,
        language=book.language,
        created_at=book.created_at,
        update_at=book.update_at,
        reviews=[],
        tags=tags_objects
    )


@book_router.patch("/{book_uid}",response_model=Book)
async def get_update_book(book_uid:str,book_update_data:BookUpdate,session:AsyncSession = Depends(get_session),token_details=Depends(access_token_bearer)):
    updated_book = await book_service.update_book(book_uid,book_update_data,session) 
    if updated_book is None:
        raise BookNotFound()
    else:
        return updated_book

@book_router.delete("/{book_uid}",status_code=204)
async def get_delete_book(book_uid:str,session:AsyncSession = Depends(get_session),token_details=Depends(access_token_bearer)):
    book_to_delete = await book_service.delete_book(book_uid,session)
    if book_to_delete is None:
        raise BookNotFound()
    else:
        return {"massage":"Success","status":"No content"}