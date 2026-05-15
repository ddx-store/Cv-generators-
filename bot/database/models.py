from sqlalchemy import Column, Integer, BigInteger, String, Text, DateTime, ForeignKey, func
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False, index=True)
    full_name = Column(String(255), nullable=True)
    job_title = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    email = Column(String(255), nullable=True)
    city_country = Column(String(255), nullable=True)
    linkedin = Column(String(500), nullable=True)
    portfolio = Column(String(500), nullable=True)
    summary = Column(Text, nullable=True)
    skills = Column(Text, nullable=True)
    languages = Column(Text, nullable=True)
    cv_language = Column(String(10), nullable=True, default="ar")
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    experiences = relationship("Experience", back_populates="user", cascade="all, delete-orphan")
    educations = relationship("Education", back_populates="user", cascade="all, delete-orphan")
    courses = relationship("Course", back_populates="user", cascade="all, delete-orphan")
    projects = relationship("Project", back_populates="user", cascade="all, delete-orphan")
    saved_cvs = relationship("SavedCV", back_populates="user", cascade="all, delete-orphan")


class Experience(Base):
    __tablename__ = "experiences"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    company = Column(String(255), nullable=False)
    title = Column(String(255), nullable=False)
    start_date = Column(String(50), nullable=False)
    end_date = Column(String(50), nullable=True)
    responsibilities = Column(Text, nullable=True)

    user = relationship("User", back_populates="experiences")


class Education(Base):
    __tablename__ = "educations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    degree = Column(String(255), nullable=False)
    institution = Column(String(255), nullable=False)
    graduation_year = Column(String(10), nullable=True)

    user = relationship("User", back_populates="educations")


class Course(Base):
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    provider = Column(String(255), nullable=True)
    year = Column(String(10), nullable=True)

    user = relationship("User", back_populates="courses")


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    link = Column(String(500), nullable=True)

    user = relationship("User", back_populates="projects")


class SavedCV(Base):
    __tablename__ = "saved_cvs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    profile_name = Column(String(255), nullable=False)
    data_json = Column(Text, nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    user = relationship("User", back_populates="saved_cvs")
