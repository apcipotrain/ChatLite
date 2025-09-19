import pymysql

def get_conn():
    return pymysql.connect(
        host="localhost",
        user="root",
        password="123456",
        database="chatdb",
        charset="utf8mb4"
    )

# 创建群
def create_group(group_name, owner):
    """创建群组并自动加入群主"""
    conn = get_conn()
    cur = conn.cursor()
    try:
        # 插入群组（群名唯一）
        cur.execute("INSERT INTO `groups` (group_name, owner) VALUES (%s, %s)", (group_name, owner))
        group_id = cur.lastrowid

        # 群主自动加入群成员表
        cur.execute("INSERT INTO group_members (group_id, username) VALUES (%s, %s)", (group_id, owner))

        conn.commit()
        return True
    except Exception as e:
        if "Duplicate entry" in str(e):
            print(f"[系统] 群组 {group_name} 已存在，不能重复创建")
        else:
            print("创建群失败:", e)
        conn.rollback()
        return False
    finally:
        cur.close()
        conn.close()

# 加入群
def join_group(group_name, username):
    conn = get_conn()
    cur = conn.cursor()
    try:
        # 获取群 id
        cur.execute("SELECT id FROM `groups` WHERE group_name=%s", (group_name,))
        row = cur.fetchone()
        if not row:
            print(f"[系统] 群组 {group_name} 不存在")
            return False
        group_id = row[0]

        # 检查是否已加入
        cur.execute("SELECT * FROM group_members WHERE group_id=%s AND username=%s", (group_id, username))
        if cur.fetchone():
            print(f"[系统] {username} 已经在群 {group_name} 中")
            return False

        # 插入成员
        cur.execute("INSERT INTO group_members (group_id, username) VALUES (%s, %s)", (group_id, username))
        conn.commit()
        print(f"[系统] {username} 加入群 {group_name} 成功")
        return True
    except Exception as e:
        print("加入群失败:", e)
        conn.rollback()
        return False
    finally:
        cur.close()
        conn.close()

# 查询用户所在群
def list_groups(username):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT g.group_name 
        FROM group_members gm
        JOIN `groups` g ON gm.group_id = g.id
        WHERE gm.username=%s
    """, (username,))
    groups = [row[0] for row in cur.fetchall()]
    cur.close()
    conn.close()
    return groups

# 获取群成员
def list_group_members(group_name):
    """查看群成员（群主标注）"""
    conn = get_conn()
    cur = conn.cursor()
    try:
        # 获取群 id 和群主
        cur.execute("SELECT id, owner FROM `groups` WHERE group_name=%s", (group_name,))
        row = cur.fetchone()
        if not row:
            return []
        group_id, owner = row

        # 获取群成员
        cur.execute("SELECT username FROM group_members WHERE group_id=%s", (group_id,))
        members = [r[0] for r in cur.fetchall()]

        # 标注群主
        members_with_role = [f"{m}(群主)" if m == owner else m for m in members]
        return members_with_role
    finally:
        cur.close()
        conn.close()

def leave_group(group_name, username):
    """用户退出群聊"""
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute("SELECT id FROM `groups` WHERE group_name=%s", (group_name,))
        row = cur.fetchone()
        if not row:
            return False
        group_id = row[0]
        cur.execute("DELETE FROM group_members WHERE group_id=%s AND username=%s", (group_id, username))
        conn.commit()
        return True
    finally:
        cur.close()
        conn.close()


def delete_group(group_name, username):
    """群主解散群聊"""
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute("SELECT owner FROM `groups` WHERE group_name=%s", (group_name,))
        row = cur.fetchone()
        if not row:
            return False
        owner = row[0]
        if owner != username:
            return False  # 不是群主，不能解散
        cur.execute("DELETE FROM `groups` WHERE group_name=%s", (group_name,))
        conn.commit()
        return True
    finally:
        cur.close()
        conn.close()
