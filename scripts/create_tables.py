#!/usr/bin/env python
"""Create required tables if they don't exist: `use`, `room`, `session_log`.

Run from be/: python scripts/create_tables.py
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1] / ''))

from app.services.mysql_adapter import _get_conn

CREATE_USE = """
CREATE TABLE IF NOT EXISTS `user` (
  user_id INT NOT NULL AUTO_INCREMENT,
  name VARCHAR(255) NOT NULL,
  joined_time DATETIME DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
"""

CREATE_ROOM = """
CREATE TABLE IF NOT EXISTS `room` (
  room_id INT NOT NULL AUTO_INCREMENT,
  roomname VARCHAR(255) NOT NULL,
  password VARCHAR(255),
  number_participate INT DEFAULT 0,
  created_time DATETIME DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (room_id),
  UNIQUE KEY uq_roomname (roomname)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
"""

CREATE_SESSION_LOG = """
CREATE TABLE IF NOT EXISTS `session_log` (
  id INT NOT NULL AUTO_INCREMENT,
  user_id INT NOT NULL,
  name VARCHAR(255),
  detection JSON,
  picture LONGBLOB,
  room_id INT,
  timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
"""


def main():
    conn = _get_conn()
    try:
        with conn.cursor() as cur:
            print('Creating table `user`...')
            cur.execute(CREATE_USE)
            print('Creating table `room`...')
            cur.execute(CREATE_ROOM)
            print('Creating table `session_log`...')
            cur.execute(CREATE_SESSION_LOG)
        conn.commit()
        print('Tables created (if they did not exist).')
    finally:
        conn.close()


if __name__ == '__main__':
    main()
