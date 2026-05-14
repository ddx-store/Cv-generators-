from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from bot.database.models import User, Experience, Education, Course, Project


async def get_or_create_user(session: AsyncSession, telegram_id: int) -> User:
    stmt = (
        select(User)
        .where(User.telegram_id == telegram_id)
        .options(
            selectinload(User.experiences),
            selectinload(User.educations),
            selectinload(User.courses),
            selectinload(User.projects),
        )
    )
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()
    if user is None:
        user = User(telegram_id=telegram_id)
        session.add(user)
        await session.commit()
        await session.refresh(user)
    return user


async def update_user_field(session: AsyncSession, telegram_id: int, field: str, value: str) -> User:
    user = await get_or_create_user(session, telegram_id)
    setattr(user, field, value)
    await session.commit()
    await session.refresh(user)
    return user


async def add_experience(session: AsyncSession, telegram_id: int, data: dict) -> Experience:
    user = await get_or_create_user(session, telegram_id)
    exp = Experience(user_id=user.id, **data)
    session.add(exp)
    await session.commit()
    return exp


async def add_education(session: AsyncSession, telegram_id: int, data: dict) -> Education:
    user = await get_or_create_user(session, telegram_id)
    edu = Education(user_id=user.id, **data)
    session.add(edu)
    await session.commit()
    return edu


async def add_course(session: AsyncSession, telegram_id: int, data: dict) -> Course:
    user = await get_or_create_user(session, telegram_id)
    course = Course(user_id=user.id, **data)
    session.add(course)
    await session.commit()
    return course


async def add_project(session: AsyncSession, telegram_id: int, data: dict) -> Project:
    user = await get_or_create_user(session, telegram_id)
    project = Project(user_id=user.id, **data)
    session.add(project)
    await session.commit()
    return project


async def get_user_full(session: AsyncSession, telegram_id: int) -> User | None:
    stmt = (
        select(User)
        .where(User.telegram_id == telegram_id)
        .options(
            selectinload(User.experiences),
            selectinload(User.educations),
            selectinload(User.courses),
            selectinload(User.projects),
        )
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def delete_user_experiences(session: AsyncSession, telegram_id: int) -> None:
    user = await get_or_create_user(session, telegram_id)
    for exp in list(user.experiences):
        await session.delete(exp)
    await session.commit()


async def delete_user_educations(session: AsyncSession, telegram_id: int) -> None:
    user = await get_or_create_user(session, telegram_id)
    for edu in list(user.educations):
        await session.delete(edu)
    await session.commit()


async def delete_user_courses(session: AsyncSession, telegram_id: int) -> None:
    user = await get_or_create_user(session, telegram_id)
    for c in list(user.courses):
        await session.delete(c)
    await session.commit()


async def delete_user_projects(session: AsyncSession, telegram_id: int) -> None:
    user = await get_or_create_user(session, telegram_id)
    for p in list(user.projects):
        await session.delete(p)
    await session.commit()
