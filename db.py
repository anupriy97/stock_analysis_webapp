import os
from sqlmodel import SQLModel, create_engine

sqlite_file_name = os.getenv('SQLITE_FILE_NAME')
sqlite_url = f"sqlite:///{sqlite_file_name}"

connect_args = {"check_same_thread": False}
engine = create_engine(sqlite_url, echo=True, connect_args=connect_args)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)
