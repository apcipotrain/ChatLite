import pymysql

def get_conn():
    return pymysql.connect(
        host="localhost",
        user="root",
        password="123456",
        database="chatdb",
        charset="utf8mb4"
    )

# 保存私聊消息
def save_message(sender, receiver, content):
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute("INSERT INTO messages (sender, receiver, content) VALUES (%s, %s, %s)",
                    (sender, receiver, content))
        conn.commit()
    finally:
        cur.close()
        conn.close()

# 获取私聊历史
def get_messages(user1, user2):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT timestamp, sender, receiver, content
        FROM messages
        WHERE (sender=%s AND receiver=%s) OR (sender=%s AND receiver=%s)
        ORDER BY timestamp ASC
    """, (user1, user2, user2, user1))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows

# 保存群聊消息
def save_group_message(sender, group_name, content):
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute("SELECT id FROM `groups` WHERE group_name=%s", (group_name,))
        row = cur.fetchone()
        if not row:
            return False
        group_id = row[0]
        cur.execute("INSERT INTO group_messages (group_id, sender, content) VALUES (%s, %s, %s)",
                    (group_id, sender, content))
        conn.commit()
        return True
    finally:
        cur.close()
        conn.close()

# 获取群聊历史
def get_group_messages(group_name):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id FROM `groups` WHERE group_name=%s", (group_name,))
    row = cur.fetchone()
    if not row:
        return []
    group_id = row[0]
    cur.execute("SELECT timestamp, sender, content FROM group_messages WHERE group_id=%s ORDER BY timestamp ASC",
                (group_id,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows

def get_unread_messages(username):
    """获取某个用户的未读私聊消息"""
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        "SELECT sender, content FROM messages WHERE receiver=%s AND is_read=0 ORDER BY timestamp",
        (username,)
    )
    rows = c.fetchall()
    c.close()
    conn.close()
    return rows


def mark_messages_read(username):
    """标记该用户的私聊消息为已读"""
    conn = get_conn()
    c = conn.cursor()
    c.execute("UPDATE messages SET is_read=1 WHERE receiver=%s", (username,))
    conn.commit()
    c.close()
    conn.close()
