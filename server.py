import socket
import threading
from db.messages import save_message, save_group_message, get_unread_messages, mark_messages_read
from db.friends import get_friends
from db.groups import create_group, join_group, list_groups, list_group_members, leave_group, delete_group

online_users = {}


def handle_client(conn, addr):
    print(f"[新连接] {addr}")
    username = None

    try:
        username = conn.recv(1024).decode("utf-8")
        if not username:
            conn.close()
            return

        online_users[username] = conn
        print(f"[上线] {username} 已连接")

        # 登录后推送离线私聊消息
        try:
            unread = get_unread_messages(username)
            for sender, content in unread:
                conn.send(f"[离线消息] {sender}: {content}".encode("utf-8"))
            mark_messages_read(username)
        except Exception as e:
            print(f"[离线消息推送错误] {e}")

        while True:
            data = conn.recv(1024).decode("utf-8")
            if not data:
                break

            # 🔹 群聊消息
            if data.startswith("@group:"):
                _, group_name, msg_content = data.split(":", 2)
                members = list_group_members(group_name)
                if not members:
                    conn.send(f"[系统] 群组 {group_name} 不存在或无成员".encode("utf-8"))
                else:
                    save_group_message(username, group_name, msg_content)
                    for member in members:
                        # ✅ 去掉 “(群主)” 标记
                        pure_name = member.replace("(群主)", "")
                        if pure_name in online_users:
                            online_users[pure_name].send(
                                f"[群聊:{group_name}] {username}: {msg_content}".encode("utf-8")
                            )

            # 🔹 创建群
            elif data.startswith("/groupcreate"):
                _, group_name = data.split(maxsplit=1)
                if create_group(group_name, username):  # ✅ 传入当前用户名
                    conn.send(f"[系统] 群组 {group_name} 创建成功，你是群主并已自动加入群".encode("utf-8"))
                else:
                    conn.send(f"[系统] 群组 {group_name} 创建失败".encode("utf-8"))

            # 🔹 加入群
            elif data.startswith("/groupjoin"):
                _, group_name = data.split(maxsplit=1)
                if join_group(group_name, username):
                    conn.send(f"[系统] 你已加入群 {group_name}".encode("utf-8"))
                else:
                    conn.send(f"[系统] 加入群 {group_name} 失败".encode("utf-8"))

            # 🔹 查看所在群
            elif data.startswith("/grouplist"):
                groups = list_groups(username)
                conn.send(f"[系统] 你所在的群: {groups}".encode("utf-8"))

            # 🔹 查看群成员
            elif data.startswith("/groupmembers"):
                parts = data.split()
                if len(parts) == 2:
                    group_name = parts[1]
                    members = list_group_members(group_name)
                    if members:
                        conn.send(f"[系统] 群 {group_name} 的成员: {', '.join(members)}".encode("utf-8"))
                    else:
                        conn.send(f"[系统] 群 {group_name} 不存在或没有成员".encode("utf-8"))
                else:
                    conn.send("[系统] 用法: /groupmembers <群名>".encode("utf-8"))

            # 🔹 退出群
            elif data.startswith("/groupleave"):
                _, group_name = data.split(maxsplit=1)
                if leave_group(group_name, username):
                    conn.send(f"[系统] 你已退出群 {group_name}".encode("utf-8"))
                else:
                    conn.send(f"[系统] 退出群 {group_name} 失败".encode("utf-8"))

            # 🔹 解散群
            elif data.startswith("/groupdelete"):
                _, group_name = data.split(maxsplit=1)
                if delete_group(group_name, username):
                    conn.send(f"[系统] 你已解散群 {group_name}".encode("utf-8"))
                else:
                    conn.send(f"[系统] 解散群 {group_name} 失败（可能不是群主）".encode("utf-8"))

            # 🔹 私聊消息
            elif ":" in data:
                to_user, msg = data.split(":", 1)
                if to_user not in get_friends(username):
                    conn.send(f"[系统] 你和 {to_user} 还不是好友".encode("utf-8"))
                    continue
                save_message(username, to_user, msg)
                if to_user in online_users:
                    online_users[to_user].send(f"{username}: {msg}".encode("utf-8"))
                else:
                    conn.send(f"[系统] 用户 {to_user} 不在线".encode("utf-8"))

            else:
                conn.send("[系统] 消息格式错误".encode("utf-8"))

    except Exception as e:
        print(f"[错误] {e}")
    finally:
        if username in online_users:
            del online_users[username]
        conn.close()
        print(f"[下线] {username} 已断开")


def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(("127.0.0.1", 12345))
    server.listen(5)
    print("[服务器启动] 等待客户端连接...")

    while True:
        conn, addr = server.accept()
        thread = threading.Thread(target=handle_client, args=(conn, addr))
        thread.start()


if __name__ == "__main__":
    main()
