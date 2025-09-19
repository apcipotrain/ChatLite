from db.users import reset_password

def main():
    username = input("请输入用户名: ").strip()
    phone = input("请输入手机号: ").strip()

    # 第一步：验证用户名+手机号是否存在（只查不改）
    from db.users import get_conn
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE username=%s AND phone=%s", (username, phone))
    row = cur.fetchone()
    cur.close()
    conn.close()

    if not row:
        print("验证失败：用户名或手机号不匹配 ❌")
        return
    else:
        print("验证成功 ✅")

    # 第二步：输入新密码
    pwd1 = input("请输入新密码: ").strip()
    pwd2 = input("请确认新密码: ").strip()

    if pwd1 != pwd2:
        print("两次输入的密码不一致 ❌")
        return
    else:
        print("两次密码一致 ✅")

    # 第三步：确认是否修改
    confirm = input("是否确认修改密码？(y/n): ").strip().lower()
    if confirm == "y":
        if reset_password(username, phone, pwd1):
            print("密码修改成功 ✅")
        else:
            print("密码修改失败 ❌")
    else:
        print("已取消修改")

if __name__ == "__main__":
    main()
