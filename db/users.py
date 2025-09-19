import pymysql

# 获取数据库连接
def get_conn():
    return pymysql.connect(
        host="localhost",
        user="root",           # 改成你自己的 MySQL 用户名
        password="123456",    # 改成你自己的 MySQL 密码
        database="chatdb",
        charset="utf8mb4"
    )

# 注册
def register(username, password, nickname, phone):
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO users (username, password, nickname, phone) VALUES (%s, %s, %s, %s)",
            (username, password, nickname, phone)
        )
        conn.commit()
        return True
    except Exception as e:
        print("注册失败:", e)
        conn.rollback()
        return False
    finally:
        cur.close()
        conn.close()

# 登录
def login(username, password):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE username=%s AND password=%s", (username, password))
    user = cur.fetchone()
    cur.close()
    conn.close()
    return user is not None

# 列出所有用户
def list_users():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT username FROM users")
    users = [row[0] for row in cur.fetchall()]
    cur.close()
    conn.close()
    return users

# 重置密码功能
def reset_password(username, phone, new_password):
    conn = get_conn()
    cur = conn.cursor()
    try:
        # 检查用户名和手机号是否匹配
        cur.execute("SELECT * FROM users WHERE username=%s AND phone=%s", (username, phone))
        if not cur.fetchone():
            return False  # 用户名或手机号错误

        # 更新密码
        cur.execute("UPDATE users SET password=%s WHERE username=%s", (new_password, username))
        conn.commit()
        return True
    except Exception as e:
        print("密码重置失败:", e)
        conn.rollback()
        return False
    finally:
        cur.close()
        conn.close()

# 查询用户信息（按用户名或昵称）
def get_user(name):
    conn = get_conn()
    cur = conn.cursor()
    try:
        # 先按用户名查
        cur.execute("SELECT username, nickname, phone FROM users WHERE username=%s", (name,))
        row = cur.fetchone()
        if row:
            return row

        # 如果用户名没查到，再按昵称查
        cur.execute("SELECT username, nickname, phone FROM users WHERE nickname=%s", (name,))
        row = cur.fetchone()
        return row
    finally:
        cur.close()
        conn.close()
