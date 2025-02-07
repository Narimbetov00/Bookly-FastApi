from src.db.models import Tags
from fastapi.exceptions import HTTPException
from sqlmodel.ext.asyncio.session import AsyncSession
from .schemas import TagsAddModel,TagsCreateModel,TagsModel
from sqlmodel import select,desc

from src.books.service import BookService
from src.errors import BookNotFound,TagNotFound,TagAlreadyExists

book_service = BookService()

class TagService:

    async def get_tags(self,session:AsyncSession):
        statement = select(Tags).order_by(desc(Tags.created_at))

        result = await session.exec(statement)
 
        return result.all()

    async def get_tag_by_uid(tag_uid:str,session:AsyncSession):
        statement = select(Tags).where(Tags.uid==tag_uid)

        result = await session.exec(statement)
 
        return result.first()


    async def add_tag(self,tag_data:TagsCreateModel,session:AsyncSession):
        statement = select(Tags).where(Tags.name == tag_data.name)
        result = await session.exec(statement)

        tag = result.first()

        if tag:
            raise TagAlreadyExists()

        new_tag = Tags(name=tag_data.name)
        session.add(new_tag)
        await session.commit()

        return new_tag

    async def add_tags_to_book(
        self,book_uid:str,tag_data:TagsAddModel,session:AsyncSession
    ):
        book = await book_service.get_book(book_uid=book_uid,session=session)

        if not book:
            raise BookNotFound()
        if book.tags is None:
            book.tags = []

        existing_tags = set(book.tags)  # `UUID` lar ro‘yxati sifatida saqlaymiz

        for tag_name in tag_data.tags:
            # 📌 1. Tag bazada bormi? Tekshiramiz
            result = await session.exec(select(Tags).where(Tags.name == tag_name))
            tag = result.one_or_none()

            if not tag:
                # 📌 2. Tag yo‘q bo‘lsa, yangi `UUID` yaratamiz va bazaga qo‘shamiz
                tag = Tags(uid=uuid.uuid4(), name=tag_name)
                session.add(tag)
                await session.commit()  # Yangi tagni bazaga saqlash
                await session.refresh(tag)

            # 📌 3. Tag `UUID` sini `Book` ga qo‘shamiz
            existing_tags.add(tag.uid)

        # 📌 4. Yangilangan `UUID` larni saqlash
        book.tags = list(existing_tags)
        session.add(book)
        await session.commit()
        await session.refresh(book)

        return book

    async def update_tag(self,tag_uid,tag_update_date:TagsCreateModel,session:AsyncSession):
        tag = await self.get_tag_by_uid(tag_uid,session)

        if not tag:
            raise TagNotFound()
          
        update_date_dict = tag_update_date.model_dump()

        for k,v in update_date_dict.items():
            setattr(tag,k,v)

            await session.commit()

            await session.refresh()
        return tag
    
    async def delete_tag(self,tag_uid,session:AsyncSession):
        statement = select(Tags).where(Tags.uid==tag_uid)

        result = await session.exec(statement)
 
        tag = result.first()

        if not tag:
            raise TagNotFound()
        
        await session.delete(tag)

        await session.commit()
        