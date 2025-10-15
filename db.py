from sqlalchemy import create_engine, Column, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()


class Resume(Base):
    __tablename__ = "resumes"
    id = Column(Integer, primary_key=True)
    name = Column(String(200))
    raw = Column(Text)
    emails = Column(String(500))
    phones = Column(String(200))
    skills = Column(String(1000))
    years = Column(Integer)


def get_session(sqlite_path: str = "sqlite:///resumes.db"):
    engine = create_engine(sqlite_path)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session()


def save_resume(session, parsed: dict):
    r = Resume(
        name=parsed.get("name", ""),
        raw=parsed.get("full_text", ""),
        emails=",".join(parsed.get("emails", [])),
        phones=",".join(parsed.get("phones", [])),
        skills=",".join(parsed.get("skills", [])),
        years=parsed.get("years_experience_est", 0),
    )
    session.add(r)
    session.commit()
    return r.id
