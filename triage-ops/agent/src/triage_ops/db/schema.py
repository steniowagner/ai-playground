from sqlalchemy.orm import Session, sessionmaker

type SessionFactory = sessionmaker[Session]
