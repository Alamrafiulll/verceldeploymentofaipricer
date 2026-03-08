import sqlalchemy as sa
from sqlalchemy import create_engine, inspect

# Use the SQLite database URL
DATABASE_URL = "sqlite:///./pricing.db"

engine = create_engine(DATABASE_URL)
inspector = inspect(engine)

if inspector.has_table("users"):
    columns = [col['name'] for col in inspector.get_columns("users")]
    print(f"Columns in users table: {columns}")
else:
    print("Table 'users' does not exist.")
