import sqlalchemy as sa
from sqlalchemy import create_engine, inspect

# Use the SQLite database URL
DATABASE_URL = "sqlite:///./pricing.db"

engine = create_engine(DATABASE_URL)
inspector = inspect(engine)

tables = inspector.get_table_names()
print(f"Tables in database: {tables}")
