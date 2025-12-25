import os
import json
import re
import pymysql
from typing import Optional
from ..config import settings

def _get_conn():
    # prefer full DATABASE_URL if provided
    if settings.DATABASE_URL:
        # parse connection from URL
        # expected format: mysql+pymysql://user:pass@host:port/dbname
        url = settings.DATABASE_URL
        # strip prefix if present
        if url.startswith('mysql+pymysql://'):
            url = url[len('mysql+pymysql://'):]
        # split user:pass and host/db
        creds, hostdb = url.split('@') if '@' in url else (None, url)
        if creds:
            user, pwd = creds.split(':', 1)
        else:
            user = settings.DB_USER
            pwd = settings.DB_PASS
        hostport, dbname = hostdb.split('/', 1)
        if ':' in hostport:
            host, port = hostport.split(':', 1)
        else:
            host = hostport
            port = settings.DB_PORT
        db = dbname.split('?')[0]
    else:
        user = settings.DB_USER
        pwd = settings.DB_PASS
        host = settings.DB_HOST
        port = settings.DB_PORT
        db = settings.DB_NAME

    conn = pymysql.connect(host=host, port=int(port), user=user, password=pwd, database=db, charset='utf8mb4')
    return conn

def ensure_room(roomname: str, password: Optional[str] = None):
    conn = _get_conn()
    try:
        with conn.cursor() as cur:
            # try to find existing room
            cur.execute("SELECT room_id FROM room WHERE roomname=%s LIMIT 1", (roomname,))
            r = cur.fetchone()
            if r:
                print(f"[mysql_adapter] found existing room '{roomname}' id={r[0]}")
                return r[0]
            # insert new room
            cur.execute("INSERT INTO room (roomname, password, number_participate, created_time) VALUES (%s, %s, %s, NOW())", (roomname, password, 0))
            conn.commit()
            print(f"[mysql_adapter] created room '{roomname}' id={cur.lastrowid}")
            # create per-room session_log table for this room (non-fatal)
            try:
                create_session_log_table(roomname)
            except Exception as e:
                print(f"[mysql_adapter] warning: failed to create per-room session_log table for '{roomname}': {e}")
            return cur.lastrowid
    finally:
        conn.close()


def increment_room_participants(room_id: int, delta: int = 1):
    conn = _get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("UPDATE room SET number_participate = IFNULL(number_participate,0) + %s WHERE room_id = %s", (delta, room_id))
            conn.commit()
            print(f"[mysql_adapter] increment_room_participants room_id={room_id} delta={delta}")
    finally:
        conn.close()

def ensure_user(user_name: str):
    conn = _get_conn()
    try:
        with conn.cursor() as cur:
            # Try to find by name first (use `user` table)
            cur.execute("SELECT user_id, name FROM `user` WHERE name=%s LIMIT 1", (user_name,))
            r = cur.fetchone()
            if r:
                print(f"[mysql_adapter] found existing user '{user_name}' id={r[0]}")
                # existing user: return id
                return r[0]
            # insert new user
            cur.execute("INSERT INTO `user` (name, joined_time) VALUES (%s, NOW())", (user_name,))
            conn.commit()
            print(f"[mysql_adapter] created user '{user_name}' id={cur.lastrowid}")
            return cur.lastrowid
    finally:
        conn.close()


def update_user_lastseen(user_id: int, name: Optional[str] = None):
    conn = _get_conn()
    try:
        with conn.cursor() as cur:
            if name:
                cur.execute("UPDATE `user` SET name=%s, joined_time = IFNULL(joined_time, NOW()) WHERE user_id=%s", (name, user_id))
            else:
                cur.execute("UPDATE `user` SET joined_time = IFNULL(joined_time, NOW()) WHERE user_id=%s", (user_id,))
            conn.commit()
            print(f"[mysql_adapter] update_user_lastseen user_id={user_id} name={name}")
    finally:
        conn.close()

def insert_session_log(user_id: int, name: str, detection_json: dict, picture_bytes: bytes, room_id: int):
    conn = _get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("INSERT INTO session_log (user_id, name, detection, picture, room_id, timestamp) VALUES (%s, %s, %s, %s, %s, NOW())",
                        (user_id, name, json.dumps(detection_json, ensure_ascii=False), picture_bytes, room_id))
            conn.commit()
            print(f"[mysql_adapter] inserted session_log user_id={user_id} room_id={room_id} id={cur.lastrowid} size={len(picture_bytes) if picture_bytes else 0}")
            return cur.lastrowid
    finally:
        conn.close()


def _sanitize_table_name(name: str) -> str:
    # keep only alnum and underscore, prefix with letter if necessary
    s = name.lower()
    s = re.sub(r"[^a-z0-9_]", "_", s)
    # ensure it doesn't start with a digit
    if re.match(r"^[0-9]", s):
        s = "r_" + s
    # limit length to reasonable size
    return s[:48]


def create_session_log_table(roomname: str):
    """Create a per-room session log table named `session_log_room_<sanitized>`.

    This mirrors the `session_log` schema.
    """
    tbl_suffix = _sanitize_table_name(roomname)
    table_name = f"session_log_room_{tbl_suffix}"
    create_sql = f"""
    CREATE TABLE IF NOT EXISTS `{table_name}` (
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
    conn = _get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(create_sql)
        conn.commit()
        print(f"[mysql_adapter] created per-room session log table '{table_name}' (if not exists)")
        return table_name
    finally:
        conn.close()


def get_user_by_email(email: str):
    conn = _get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id, email, password_hash, role, created_at FROM users WHERE email=%s LIMIT 1", (email,))
            return cur.fetchone()
    finally:
        conn.close()


def create_user(email: str, password_hash: str, role: str = "user"):
    conn = _get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("INSERT INTO users (email, password_hash, role, created_at) VALUES (%s, %s, %s, NOW())",
                        (email, password_hash, role))
            conn.commit()
            print(f"[mysql_adapter] created user '{email}' id={cur.lastrowid}")
            return cur.lastrowid
    finally:
        conn.close()
