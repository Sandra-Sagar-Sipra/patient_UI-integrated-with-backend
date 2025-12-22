from app.core.db import engine
from sqlalchemy import inspect

ins = inspect(engine)
print("Tables:", ins.get_table_names())
