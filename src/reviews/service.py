from src.db.models import Reviews
from fastapi.exceptions import HTTPException
from src.auth.service import UserService
from src.books.service import BookService
from sqlmodel.ext.asyncio.session import AsyncSession
from .schemas import ReviewCreateModel
import logging

book_service = BookService()
user_service = UserService()


class ReviewService:

    async def add_review_to_book(self,user_email:str,book_uid:str,review_data:ReviewCreateModel,session:AsyncSession):
        try:
            book = await book_service.get_book(
                book_uid=book_uid,
                session=session
            )
            user = await user_service.get_user_by_email(
                email=user_email,
                session=session
            )

            

            review_data_dict = review_data.model_dump()
            new_review = Reviews(
                **review_data_dict
            )
            if not book:
                raise HTTPException(
                    status_code=404,
                    detail="Book Not Found"
                )
            
            if not user:
                raise HTTPException(
                    status_code=404,
                    detail="User Not Found"
                )
            new_review.user = user
            new_review.book = book

            session.add(new_review)
            await session.commit()

            return new_review

        except Exception as e:
            logging.exception(e)
            raise HTTPException(
                status_code=500,
                detail="Oops ... Something went wrong!"
            )