import pymysql
from db.users import get_user
def get_conn():
    return pymysql.connect(
        host="localhost",
        user="root",
        password="123456",
        database="chatdb",
        charset="utf8mb4"
    )

# 添加好友（双向）
def add_friend(user, friend):
    conn = get_conn()
    cur = conn.cursor()
    try:
        # 检查对方是否存在
        if not get_user(friend):
            print(f"[系统] 用户 {friend} 不存在")
            return False

        # 检查是否已是好友
        cur.execute("SELECT * FROM friends WHERE user=%s AND friend=%s", (user, friend))
        if cur.fetchone():
            print(f"[系统] {user} 和 {friend} 已经是好友")
            return False

        # 插入双向关系
        cur.execute("INSERT INTO friends (user, friend) VALUES (%s, %s)", (user, friend))
        cur.execute("INSERT INTO friends (user, friend) VALUES (%s, %s)", (friend, user))
        conn.commit()
        print(f"[系统] {user} 和 {friend} 成为好友")
        return True
    except Exception as e:
        print("添加好友失败:", e)
        conn.rollback()
        return False
    finally:
        cur.close()
        conn.close()

# 删除好友（双向）
def remove_friend(user, friend):
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM friends WHERE (user=%s AND friend=%s) OR (user=%s AND friend=%s)",
                    (user, friend, friend, user))
        conn.commit()
        print(f"[系统] {user} 和 {friend} 已解除好友关系")
        return True
    except Exception as e:
        print("删除好友失败:", e)
        conn.rollback()
        return False
    finally:
        cur.close()
        conn.close()

# 获取好友列表
def get_friends(user):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT friend FROM friends WHERE user=%s", (user,))
    friends = [row[0] for row in cur.fetchall()]
    cur.close()
    conn.close()
    return friends
