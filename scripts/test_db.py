#!/usr/bin/env python
"""Simple DB connectivity tester.

Usage:
  cd be
  python scripts/test_db.py

It reads `DATABASE_URL` from the environment or from `be/.env` (python-dotenv is used).
"""
import os
import sys
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError


def main():
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        print('ERROR: DATABASE_URL is not set. Set it in be/.env or as an environment variable.')
        sys.exit(2)

    print('Testing DATABASE_URL:', db_url)
    try:
        engine = create_engine(db_url, pool_pre_ping=True)
        with engine.connect() as conn:
            r = conn.execute(text('SELECT 1'))
            val = r.scalar()
            print('SELECT 1 ->', val)
        print('OK: Connected to database successfully')
    except SQLAlchemyError as e:
        print('SQLAlchemy error:', e)
        sys.exit(3)
    except Exception as e:
        print('Unexpected error:', e)
        sys.exit(4)


if __name__ == '__main__':
    main()
