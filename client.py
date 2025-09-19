import socket
import threading
from db.users import login
from db.friends import get_friends, add_friend, remove_friend
from db.messages import get_messages, get_group_messages
from db.groups import list_groups, list_group_members

def receive_messages(sock, username):
    """接收消息的线程"""
    while True:
        try:
            msg = sock.recv(1024).decode("utf-8")
            if msg:
                print("\n" + msg)
            else:
                break
        except:
            break


def main():
    username = input("请输入用户名: ")
    password = input("请输入密码: ")

    if not login(username, password):
        print("登录失败！用户名或密码错误。")
        return

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(("127.0.0.1", 12345))
    sock.send(username.encode("utf-8"))

    threading.Thread(target=receive_messages, args=(sock, username), daemon=True).start()

    print("登录成功！")
    print("好友列表:", get_friends(username))
    print("群聊列表:", list_groups(username))  # ✅ 新增
    print("可用命令：")
    print("  /friends             查看好友列表")
    print("  /add <用户名>        添加好友")
    print("  /remove <用户名>     删除好友")
    print("  /chat <用户名>       切换聊天对象（私聊）")
    print("  /chat <群名>         切换群聊")
    print("  /groupcreate <群名>  创建群组")
    print("  /groupjoin <群名>    加入群组")
    print("  /groupmembers <群名> 查看群成员")
    print("  /groupleave <群名>   退出群聊")
    print("  /groupdelete <群名>  解散群聊（仅群主）")
    print("  /grouplist           查看自己所在的群")
    print("  /history <用户名>    查看私聊历史记录")
    print("  /history <群名>      查看群聊历史记录")
    print("  quit                 退出程序")

    chat_target = None
    chat_mode = None   # "user" 或 "group"

    while True:
        msg = input()
        if msg.lower() == "quit":
            break

        # 🔹 好友管理
        elif msg.startswith("/friends"):
            print("好友列表:", get_friends(username))
        elif msg.startswith("/add"):
            parts = msg.split()
            if len(parts) == 2:
                add_friend(username, parts[1])
            else:
                print("[系统] 用法: /add <用户名>")
        elif msg.startswith("/remove"):
            parts = msg.split()
            if len(parts) == 2:
                remove_friend(username, parts[1])
            else:
                print("[系统] 用法: /remove <用户名>")

        # 🔹 聊天切换
        elif msg.startswith("/chat"):
            parts = msg.split()
            if len(parts) == 2:
                chat_target = parts[1]
                user_groups = list_groups(username)

                if chat_target in user_groups:
                    # ✅ 用户在群里 → 群聊
                    chat_mode = "group"
                    print(f"[系统] 已切换到群聊 → {chat_target}")
                else:
                    # ✅ 检查是不是群，但用户没加入
                    from db.groups import list_group_members
                    members = list_group_members(chat_target)
                    if members:  # 群存在，但自己不在群
                        print(f"[系统] 你不在 {chat_target} 群聊中，无法切换")
                        chat_target = None
                        chat_mode = None
                    else:
                        # ✅ 当作私聊：检查是否好友
                        friends = get_friends(username)
                        if chat_target in friends:
                            chat_mode = "user"
                            print(f"[系统] 已切换到私聊对象 → {chat_target}")
                        else:
                            print(f"[系统] 你和 {chat_target} 还不是好友，无法切换")
                            chat_target = None
                            chat_mode = None
            else:
                print("[系统] 用法: /chat <用户名|群名>")



        # 🔹 历史消息
        elif msg.startswith("/history"):
            parts = msg.split()
            if len(parts) == 2:
                target = parts[1]
                if target in list_groups(username):
                    history = get_group_messages(target)
                    if not history:
                        print("[系统] 暂无群聊历史消息")
                    else:
                        for ts, sender, content in history:
                            print(f"[{ts}] {sender} -> 所有人: {content}")
                else:
                    history = get_messages(username, target)
                    if not history:
                        print("[系统] 暂无私聊历史消息")
                    else:
                        for ts, sender, receiver, content in history:
                            print(f"[{ts}] {sender} -> {receiver}: {content}")
            else:
                print("[系统] 用法: /history <用户名|群名>")

        # 🔹 群组管理
        elif msg.startswith("/groupcreate"):
            parts = msg.split()
            if len(parts) == 2:
                sock.send(msg.encode("utf-8"))
            else:
                print("[系统] 用法: /groupcreate <群名>")

        elif msg.startswith("/groupjoin"):
            parts = msg.split()
            if len(parts) == 2:
                sock.send(msg.encode("utf-8"))
            else:
                print("[系统] 用法: /groupjoin <群名>")

        elif msg.startswith("/groupmembers"):
            parts = msg.split()
            if len(parts) == 2:
                sock.send(msg.encode("utf-8"))
            else:
                print("[系统] 用法: /groupleave <群名>")


        elif msg.startswith("/groupleave"):
            parts = msg.split()
            if len(parts) == 2:
                sock.send(msg.encode("utf-8"))
                # ✅ 如果当前正在这个群聊，退出后清空聊天对象
                if chat_mode == "group" and chat_target == parts[1]:
                    chat_target = None
                    chat_mode = None
            else:
                print("[系统] 用法: /groupleave <群名>")


        elif msg.startswith("/groupdelete"):
            parts = msg.split()
            if len(parts) == 2:
                sock.send(msg.encode("utf-8"))
            else:
                print("[系统] 用法: /groupdelete <群名>")

        elif msg.startswith("/grouplist"):
            sock.send(msg.encode("utf-8"))

        # 🔹 普通消息（私聊/群聊）
        else:
            if chat_mode == "user" and chat_target:
                sock.send(f"{chat_target}:{msg}".encode("utf-8"))
            elif chat_mode == "group" and chat_target:
                sock.send(f"@group:{chat_target}:{msg}".encode("utf-8"))
            else:
                print("[系统] 请先用 /chat <用户名|群名> 选择聊天对象")

    sock.close()


if __name__ == "__main__":
    main()
