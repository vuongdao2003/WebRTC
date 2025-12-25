#!/usr/bin/env python
"""Create a unique test room via mysql_adapter.ensure_room and check whether
- a new row in `room` is present
- the per-room `session_log_room_<sanitized>` table exists

Run from be/: python scripts/test_create_room.py
"""
import sys
import time
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1] / ''))

from app.services.mysql_adapter import ensure_room, _get_conn, _sanitize_table_name


def main():
    room_name = f"test_room_for_check_{int(time.time())}"
    print('Creating/ensuring room:', room_name)
    room_id = ensure_room(room_name, None)
    print('ensure_room returned id=', room_id)

    # compute expected per-room table name
    tbl_suffix = _sanitize_table_name(room_name)
    table_name = f"session_log_room_{tbl_suffix}"

    # check in DB whether this table exists and whether room row exists
    conn = _get_conn()
    try:
        with conn.cursor() as cur:
            # check room row
            cur.execute("SELECT room_id, roomname, created_time FROM room WHERE room_id=%s LIMIT 1", (room_id,))
            r = cur.fetchone()
            print('room row:', r)

            # check table existence using SHOW TABLES LIKE
            cur.execute("SHOW TABLES LIKE %s", (table_name,))
            t = cur.fetchone()
            print('per-room table found:' , bool(t), 'table_name=', table_name)
    finally:
        conn.close()

    print('\nTest complete. If `per-room table found` is True then creation worked.')


if __name__ == '__main__':
    main()
