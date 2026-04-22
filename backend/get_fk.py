import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, inspect
from app.core.config import settings

def main():
    engine = create_engine(str(settings.SQLALCHEMY_DATABASE_URI))
    inspector = inspect(engine)
    fks = inspector.get_foreign_keys('question')
    for fk in fks:
        if 'section_id' in fk['constrained_columns']:
            print(f"Found FK: {fk['name']}")

if __name__ == "__main__":
    main()
