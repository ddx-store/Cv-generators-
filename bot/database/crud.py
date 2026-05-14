from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

import json

from bot.database.models import User, Experience, Education, Course, Project, SavedCV


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


def _user_to_dict(user: User) -> dict:
    return {
        "full_name": user.full_name,
        "job_title": user.job_title,
        "phone": user.phone,
        "email": user.email,
        "city_country": user.city_country,
        "linkedin": user.linkedin,
        "portfolio": user.portfolio,
        "summary": user.summary,
        "skills": user.skills,
        "languages": user.languages,
        "cv_language": user.cv_language,
        "experiences": [
            {
                "company": e.company, "title": e.title,
                "start_date": e.start_date, "end_date": e.end_date,
                "responsibilities": e.responsibilities,
            }
            for e in user.experiences
        ],
        "educations": [
            {
                "degree": e.degree, "institution": e.institution,
                "graduation_year": e.graduation_year,
            }
            for e in user.educations
        ],
        "courses": [
            {"name": c.name, "provider": c.provider, "year": c.year}
            for c in user.courses
        ],
        "projects": [
            {"name": p.name, "description": p.description, "link": p.link}
            for p in user.projects
        ],
    }


async def save_cv_profile(session: AsyncSession, telegram_id: int, profile_name: str) -> SavedCV:
    user = await get_or_create_user(session, telegram_id)
    data = _user_to_dict(user)
    saved = SavedCV(user_id=user.id, profile_name=profile_name, data_json=json.dumps(data, ensure_ascii=False))
    session.add(saved)
    await session.commit()
    return saved


async def list_cv_profiles(session: AsyncSession, telegram_id: int) -> list[SavedCV]:
    user = await get_or_create_user(session, telegram_id)
    stmt = select(SavedCV).where(SavedCV.user_id == user.id).order_by(SavedCV.created_at.desc())
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def load_cv_profile(session: AsyncSession, telegram_id: int, profile_id: int) -> bool:
    user = await get_or_create_user(session, telegram_id)
    stmt = select(SavedCV).where(SavedCV.id == profile_id, SavedCV.user_id == user.id)
    result = await session.execute(stmt)
    saved = result.scalar_one_or_none()
    if not saved:
        return False

    data = json.loads(saved.data_json)

    for field in ("full_name", "job_title", "phone", "email", "city_country",
                  "linkedin", "portfolio", "summary", "skills", "languages", "cv_language"):
        setattr(user, field, data.get(field))

    for exp in list(user.experiences):
        await session.delete(exp)
    for edu in list(user.educations):
        await session.delete(edu)
    for c in list(user.courses):
        await session.delete(c)
    for p in list(user.projects):
        await session.delete(p)
    await session.flush()

    for exp_data in data.get("experiences", []):
        session.add(Experience(user_id=user.id, **exp_data))
    for edu_data in data.get("educations", []):
        session.add(Education(user_id=user.id, **edu_data))
    for c_data in data.get("courses", []):
        session.add(Course(user_id=user.id, **c_data))
    for p_data in data.get("projects", []):
        session.add(Project(user_id=user.id, **p_data))

    await session.commit()
    return True


async def delete_cv_profile(session: AsyncSession, telegram_id: int, profile_id: int) -> bool:
    user = await get_or_create_user(session, telegram_id)
    stmt = select(SavedCV).where(SavedCV.id == profile_id, SavedCV.user_id == user.id)
    result = await session.execute(stmt)
    saved = result.scalar_one_or_none()
    if not saved:
        return False
    await session.delete(saved)
    await session.commit()
    return True
