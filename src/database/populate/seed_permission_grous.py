from typing import Annotated

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.dependencies import get_db
from src.database.models import UserGroupModel
from src.enums import UserGroupEnum


# Method for seed user group (For local test only)
async def seed_groups(db: Annotated[AsyncSession, Depends(get_db)]) -> None:
    for group_name in UserGroupEnum:
        stmt = select(UserGroupModel).where(UserGroupModel.name == group_name)
        result = await db.execute(stmt)
        if not result.scalar_one_or_none():
            db.add(UserGroupModel(name=group_name))

    await db.commit()
