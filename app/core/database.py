from sqlalchemy.orm import declarative_base,sessionmaker
from sqlalchemy import create_engine
from app.core.config import DATABASE_URL

engine = create_engine(DATABASE_URL)

sessionLocal = sessionmaker(
    autoflush=False,
    autocommit = False,
    bind=engine
)

Base = declarative_base()

def get_db():
    db=sessionLocal()

    try:
        yield db
    finally:
        db.close()

