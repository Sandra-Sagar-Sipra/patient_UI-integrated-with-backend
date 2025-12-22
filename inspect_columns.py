from app.core.db import engine
from sqlalchemy import inspect

ins = inspect(engine)
print("SOAPNotes columns:", [c['name'] for c in ins.get_columns('soap_notes')])
