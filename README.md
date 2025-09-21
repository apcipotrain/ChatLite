# ChatLite

一个基于 **wxPython + MySQL** 的轻量级聊天系统。  
支持 **好友私聊、群聊、历史记录、未读消息管理等**，附带图形界面和简单的启动脚本。
3G大学《程序设计综合实践》的产物。
从0开始，花了15小时，呕心沥血，粗制滥造之作。
但至少也是本人目前写的最像样最拿得出手的实战项目了。
还望各位不吝赐教。

---

## 🚀 功能模块

<img width="1626" height="761" alt="333e1cf4a3b8549f7aaa1b533bd1b055" src="https://github.com/user-attachments/assets/fee64677-2235-41e4-9870-429eb46c2033" />

目前来说，
最大的问题是：群聊暂时不支持离线推送未读消息。
最小的问题是：界面不在美，能跑就行；功能不在多，够用就灵。

---

## ⚙️ 使用方法
1. MySQL依赖
   请把 `mysql_database_backup` 的内容复制粘贴到数据库上，这需要自己本地的数据库！
2. 启动方法
   先启动 `Server.bat`
   再启动 `ChatLite.bat`
   不然没开服务器你怎么能直接跑客户端呢！！！
3. 测试建议
   如下图
   
<img width="1694" height="837" alt="9d5a3d8e6fed242ef673c0ec5a3fefa4" src="https://github.com/user-attachments/assets/08eff8b1-fb98-4a0f-bc48-27e71781b64f" />


## 📂 项目结构

### 🔹 数据库模块（db/）
1. **users.py**  
   用户管理模块  
   - `register`：注册用户（用户名、密码、昵称、手机号）  
   - `login`：验证用户名+密码是否正确  
   - `list_users`：列出所有用户  
   - `reset_password`：根据用户名+手机号重置密码  
   - `get_user`：查询用户信息（支持用户名或昵称）  
   👉 功能定位：提供用户注册、登录、信息查询和安全管理的接口。  

2. **friends.py**  
   好友关系管理模块  
   - `add_friend`：双向添加好友  
   - `remove_friend`：双向删除好友  
   - `get_friends`：获取某个用户的好友列表  
   👉 功能定位：维护用户之间的好友关系。  

3. **groups.py**  
   群聊管理模块  
   - `create_group`：创建群聊，自动把群主加入群成员表  
   - `join_group`：用户加入群聊  
   - `list_groups`：查询用户所在的所有群  
   - `list_group_members`：查看群成员列表（群主标注）  
   - `leave_group`：用户退出群聊  
   - `delete_group`：群主解散群聊  
   👉 功能定位：支持群聊的生命周期管理和成员维护。  

4. **messages.py**  
   消息存储与查询模块  
   - `save_message`：保存一条私聊消息  
   - `get_messages`：获取两人之间的私聊历史  
   - `save_group_message`：保存一条群聊消息  
   - `get_group_messages`：获取群聊历史  
   - `get_unread_messages`：获取用户未读的私聊消息（离线消息补发）  
   - `mark_messages_read`：标记用户的私聊消息为已读  
   👉 功能定位：负责消息的落库、历史查询和未读状态管理。  

E-R图如下

<img width="1531" height="950" alt="4a1d3d538b392357e15c1a5fc90c15d0" src="https://github.com/user-attachments/assets/c7b61826-8998-473c-a86b-8f1cefcb0f81" />

---

### 🔹 主程序文件
1. **client.py**  
   命令行客户端  
   - 登录验证  
   - 好友管理（添加、删除、查看）  
   - 群聊管理（创建、加入、退出、解散、查看成员）  
   - 切换私聊/群聊对象并发送消息  
   - 查看历史记录  
   - 接收服务器转发的消息并打印  
   👉 功能定位：命令行版本客户端，用于调试和快速测试。  

2. **server.py**  
   服务器端  
   - 维护 `online_users`（在线用户字典）  
   - 处理用户连接与下线  
   - 私聊消息转发（支持离线消息入库与上线推送）  
   - 群聊消息转发与群管理命令  
   👉 功能定位：即时通信的核心消息中转站。  

3. **test_db.py**  
   数据库测试脚本  
   - 验证用户名+手机号  
   - 支持修改密码  
   👉 功能定位：数据库功能调试工具。  

---

### 🔹 图形界面模块（UI）
4. **ui_actions.py**  
   界面操作逻辑模块  
   - `on_info`：查看聊天对象详情（好友 → 删除/查询历史；群聊 → 成员/解散/退出/查询历史）  
   - `show_history`：展示历史记录（自动滚动到底）  
   - `on_friend_mgmt`：好友管理入口  
   - `on_group_mgmt`：群聊管理入口  
   - `on_history`：左下角按钮入口（手动输入名称查询）  
   👉 功能定位：UI 与逻辑层的桥梁。  

5. **ui_auth.py**  
   认证界面模块  
   - `LoginFrame`：登录框（支持跳转注册/找回密码）  
   - `RegisterFrame`：注册框  
   - `PasswordResetFrame`：找回密码框  
   👉 功能定位：系统入口 UI，负责用户身份管理。  

6. **ui_chat.py**  
   聊天主界面  
   - 左侧：好友树 / 群聊树、未读消息列表、功能菜单、退出/设置按钮  
   - 右侧：顶部栏、消息显示区、输入框、发送按钮  
   - 功能：消息左右分栏、未读消息管理、离线消息补发、历史消息展示、字体设置、退出登录  
   👉 功能定位：即时通信的核心承载界面。  

7. **ui_main.py**  
   程序主入口  
   - `MainApp(wx.App)`  
     - `show_login` → 显示登录  
     - `show_register` → 显示注册  
     - `show_reset` → 显示找回密码  
     - `show_chat` → 显示聊天主界面  
   👉 功能定位：全局窗口控制器，负责窗口切换。  

8. **ui_topbar.py**  
   聊天窗口顶部栏  
   - 显示聊天对象标题  
   - 提供 “详情/返回/标记未读” 按钮  
   👉 功能定位：辅助 UI 组件，提升交互体验。  

---

### 🔹 辅助文件
- **Server.bat**：启动服务器脚本（运行 `server.py`）  
- **ChatLite.bat**：启动客户端脚本（运行 `ui_main.py`）  
- **mysql_database_backup.txt**：数据库初始化脚本（建表语句等）  

---
