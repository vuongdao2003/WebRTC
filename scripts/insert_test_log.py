#!/usr/bin/env python
"""Insert a single test session_log row via mysql_adapter.

Usage:
  cd be
  python scripts/insert_test_log.py
"""
import os
import sys
import json
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

from pathlib import Path
import sys
sys.path.append(str(Path(__file__).resolve().parents[1] / ''))

from app.services.mysql_adapter import ensure_room, ensure_user, insert_session_log


def main():
    room = os.getenv('TEST_ROOM', 'automation_test_room')
    participant = os.getenv('TEST_PARTICIPANT', 'automation_user')

    print('Ensuring room...')
    room_id = ensure_room(room, None)
    print('room_id=', room_id)

    print('Ensuring user...')
    user_id = ensure_user(participant)
    print('user_id=', user_id)

    # small placeholder JPEG bytes (1x1 px minimal JPEG header could be used), but we'll send empty bytes if not available
    pic = b'\xff\xd8\xff\xd9'  # minimal JPEG start/end markers

    detection = {"test": True, "boxes": []}

    print('Inserting session_log...')
    sid = insert_session_log(user_id, participant, detection, pic, room_id)
    print('inserted session_log id=', sid)


if __name__ == '__main__':
    main()
