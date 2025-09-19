import wx
import socket
import threading
import wx.richtext as rt

from db.friends import get_friends
from db.groups import list_groups, list_group_members
from db.messages import get_messages, get_group_messages
from ui_topbar import TopBar
from ui_actions import on_info, on_friend_mgmt, on_group_mgmt, on_history


class ChatFrame(wx.Frame):
    def __init__(self, username):
        super().__init__(None, title=f"聊天主界面 - {username}", size=(1024, 768))
        self.username = username
        self.chat_target = None
        self.chat_target_type = None  # "friend" / "group"
        self.mode = "chat"            # chat / history
        self.running = False

        # ====== socket 连接 ======
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.client.connect(("127.0.0.1", 12345))
            self.client.send(self.username.encode("utf-8"))
            self.running = True
            threading.Thread(target=self.listen_server, daemon=True).start()
        except Exception:
            wx.MessageBox("服务器未开通，无法登录 ❌", "错误", wx.OK | wx.ICON_ERROR)
            self.Destroy()
            return

        panel = wx.Panel(self)

        # ========== 左侧：联系人树 + 未读消息 + 功能菜单 ==========
        left_panel = wx.Panel(panel)
        left_vbox = wx.BoxSizer(wx.VERTICAL)

        # 联系人树
        self.tree = wx.TreeCtrl(left_panel, style=wx.TR_HAS_BUTTONS | wx.TR_LINES_AT_ROOT | wx.TR_HIDE_ROOT)
        il = wx.ImageList(16, 16)
        self.icon_user = il.Add(wx.ArtProvider.GetBitmap(wx.ART_NORMAL_FILE, wx.ART_OTHER, (16, 16)))
        self.icon_group = il.Add(wx.ArtProvider.GetBitmap(wx.ART_FOLDER, wx.ART_OTHER, (16, 16)))
        self.tree.AssignImageList(il)

        root = self.tree.AddRoot("Root")
        self.friend_root = self.tree.AppendItem(root, "好友", image=self.icon_user)
        self.group_root = self.tree.AppendItem(root, "群聊", image=self.icon_group)

        self.refresh_friend_list()
        self.refresh_group_list()

        left_vbox.Add(self.tree, 2, wx.EXPAND | wx.ALL, 5)

        # 未读消息列表
        left_vbox.Add(wx.StaticText(left_panel, label="未读消息"), 0, wx.ALL, 2)
        self.unread_list = wx.ListBox(left_panel)
        left_vbox.Add(self.unread_list, 1, wx.EXPAND | wx.ALL, 5)

        # 标记已读按钮（放在未读消息列表下方）
        self.mark_read_btn = wx.Button(left_panel, label="标记已读")
        self.mark_read_btn.Hide()
        left_vbox.Add(self.mark_read_btn, 0, wx.EXPAND | wx.ALL, 5)

        # 功能菜单
        menu_box = wx.BoxSizer(wx.VERTICAL)
        self.btn_friend_mgmt = wx.Button(left_panel, label="好友管理")
        self.btn_group_mgmt = wx.Button(left_panel, label="群聊管理")
        self.btn_history = wx.Button(left_panel, label="历史记录")
        menu_box.Add(self.btn_friend_mgmt, 0, wx.EXPAND | wx.ALL, 2)
        menu_box.Add(self.btn_group_mgmt, 0, wx.EXPAND | wx.ALL, 2)
        menu_box.Add(self.btn_history, 0, wx.EXPAND | wx.ALL, 2)
        left_vbox.Add(menu_box, 0, wx.EXPAND | wx.ALL, 5)

        left_panel.SetSizer(left_vbox)

        # 新增退出登录 + 设置按钮区域
        hbox_bottom = wx.BoxSizer(wx.HORIZONTAL)
        self.btn_logout = wx.Button(left_panel, label="退出登录")
        self.btn_settings = wx.Button(left_panel, label="设置")

        hbox_bottom.Add(self.btn_logout, 1, wx.EXPAND | wx.ALL, 2)
        hbox_bottom.Add(self.btn_settings, 1, wx.EXPAND | wx.ALL, 2)

        left_vbox.Add(hbox_bottom, 0, wx.EXPAND | wx.ALL, 5)

        # 事件绑定
        self.tree.Bind(wx.EVT_TREE_ITEM_ACTIVATED, self.on_double_click)
        self.unread_list.Bind(wx.EVT_LISTBOX_DCLICK, self.on_unread_click)
        self.mark_read_btn.Bind(wx.EVT_BUTTON, self.on_mark_read)
        self.btn_friend_mgmt.Bind(wx.EVT_BUTTON, lambda e: on_friend_mgmt(self, e))
        self.btn_group_mgmt.Bind(wx.EVT_BUTTON, lambda e: on_group_mgmt(self, e))
        self.btn_history.Bind(wx.EVT_BUTTON, lambda e: on_history(self, e))
        self.btn_logout.Bind(wx.EVT_BUTTON, lambda e: self.logout())
        self.btn_settings.Bind(wx.EVT_BUTTON, lambda e: self.open_settings())

        # ========== 右侧：顶部栏 + 聊天区 ==========
        right_panel = wx.Panel(panel)
        right_vbox = wx.BoxSizer(wx.VERTICAL)

        self.topbar = TopBar(right_panel, lambda e: on_info(self, e))
        right_vbox.Add(self.topbar, 0, wx.EXPAND | wx.ALL, 5)

        self.chat_display = rt.RichTextCtrl(right_panel, style=wx.TE_MULTILINE | wx.TE_READONLY)
        # ✅ 启动时默认用微软雅黑 14 号字体
        default_font = wx.Font(14,
                               wx.FONTFAMILY_DEFAULT,
                               wx.FONTSTYLE_NORMAL,
                               wx.FONTWEIGHT_NORMAL,
                               faceName="Microsoft YaHei")
        self.chat_display.SetFont(default_font)

        self.chat_input = wx.TextCtrl(right_panel, style=wx.TE_MULTILINE, size=(-1, 100))
        self.send_btn = wx.Button(right_panel, label="发送", size=(100, 40))

        right_vbox.Add(self.chat_display, 5, wx.EXPAND | wx.ALL, 5)
        right_vbox.Add(self.chat_input, 1, wx.EXPAND | wx.ALL, 5)
        right_vbox.Add(self.send_btn, 0, wx.ALIGN_RIGHT | wx.ALL, 5)
        self.mark_read_btn = wx.Button(right_panel, label="标记已读", size=(100, 30))
        self.mark_read_btn.Hide()
        right_vbox.Add(self.mark_read_btn, 0, wx.ALIGN_RIGHT | wx.ALL, 5)
        # 绑定事件
        self.mark_read_btn.Bind(wx.EVT_BUTTON, self.on_mark_read)

        right_panel.SetSizer(right_vbox)

        # 总体布局
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        hbox.Add(left_panel, 1, wx.EXPAND)
        hbox.Add(right_panel, 3, wx.EXPAND)
        panel.SetSizer(hbox)

        # 事件绑定
        self.send_btn.Bind(wx.EVT_BUTTON, self.on_send)
        self.tree.Bind(wx.EVT_TREE_ITEM_ACTIVATED, self.on_double_click)
        self.unread_list.Bind(wx.EVT_LISTBOX_DCLICK, self.on_unread_click)
        self.btn_friend_mgmt.Bind(wx.EVT_BUTTON, lambda e: on_friend_mgmt(self, e))
        self.btn_group_mgmt.Bind(wx.EVT_BUTTON, lambda e: on_group_mgmt(self, e))
        self.btn_history.Bind(wx.EVT_BUTTON, lambda e: on_history(self, e))
        self.Bind(wx.EVT_CLOSE, self.on_close)

        self.Show()

    # ========== 列表刷新 ==========
    def refresh_friend_list(self):
        self.tree.DeleteChildren(self.friend_root)
        for f in get_friends(self.username):
            self.tree.AppendItem(self.friend_root, f, image=self.icon_user)
        self.tree.Expand(self.friend_root)

    def refresh_group_list(self):
        self.tree.DeleteChildren(self.group_root)
        for g in list_groups(self.username):
            self.tree.AppendItem(self.group_root, g, image=self.icon_group)
        self.tree.Expand(self.group_root)

    # ========== 消息发送 ==========
    def on_send(self, event):
        if self.mode != "chat":
            return
        msg = self.chat_input.GetValue().strip()
        if not self.chat_target:
            wx.MessageBox("请先选择聊天对象", "提示", wx.OK | wx.ICON_WARNING)
            return
        if msg:
            try:
                target = self.chat_target.replace("(群主)", "")
                if self.chat_target_type == "friend":
                    data = f"{target}:{msg}"
                else:
                    data = f"@group:{target}:{msg}"
                self.client.send(data.encode("utf-8"))

                # ✅ 本地显示要放到 CallAfter，保证立即刷新
                wx.CallAfter(self.append_message, self.username, msg, True)
                self.chat_input.Clear()
            except ConnectionResetError:
                wx.MessageBox("服务器已断开连接，请重新登录", "错误", wx.OK | wx.ICON_ERROR)
                self.client = None

    # ========== 接收服务器消息 ==========
    def listen_server(self):
        while self.running:
            try:
                data = self.client.recv(4096).decode("utf-8")
                if not data:
                    break

                if data.startswith("[群聊:"):
                    prefix, content = data.split("]", 1)
                    group_info = prefix + "]"
                    sender, msg = content.strip().split(":", 1)
                    sender = sender.strip()
                    msg = msg.strip()

                    if sender == self.username:
                        # ⛔ 已在 on_send 显示过，不再重复
                        continue

                    if self.chat_target == group_info[4:-1]:
                        wx.CallAfter(self.append_message, sender, msg, is_self=False, group_prefix=group_info)
                    else:
                        wx.CallAfter(self.add_unread, f"{group_info} {sender}: {msg}")
                elif ":" in data:
                    sender, msg = data.split(":", 1)
                    sender = sender.strip()
                    msg = msg.strip()
                    is_self = (sender == self.username)
                    if self.chat_target == sender:
                        wx.CallAfter(self.append_message, sender, msg, is_self)
                    else:
                        if not is_self:  # 自己的不算未读
                            wx.CallAfter(self.add_unread, f"{sender}: {msg}")
                elif data.startswith("[离线消息]"):
                    msg_text = data.replace("[离线消息]", "").strip()
                    wx.CallAfter(self.add_unread, msg_text)
                else:
                    wx.CallAfter(self.chat_display.AppendText, data + "\n")
            except Exception as e:
                print("服务器连接错误:", e)
                break
        self.client = None

    # ========== 消息显示（对话气泡） ==========
    def append_message(self, sender, msg, is_self=False, group_prefix=None):
        if self.mode != "chat":
            return
        self.chat_display.BeginAlignment(wx.TEXT_ALIGNMENT_RIGHT if is_self else wx.TEXT_ALIGNMENT_LEFT)
        prefix = f"{group_prefix} {sender}: " if group_prefix and not is_self else (
            f"{sender}: " if not is_self else "")
        self.chat_display.WriteText(prefix + msg + "\n")
        self.chat_display.EndAlignment()

        # ✅ 自动滚动到底部
        last_pos = self.chat_display.GetLastPosition()
        self.chat_display.ShowPosition(last_pos)

    # ========== 未读消息 ==========
    def add_unread(self, text):
        self.unread_list.Append(text)

    def clear_unread(self, idx):
        if 0 <= idx < self.unread_list.GetCount():
            self.unread_list.Delete(idx)

        # 恢复按钮和标题
        self.topbar.set_button_label("详情")
        self.topbar.info_btn.Bind(wx.EVT_BUTTON, lambda e: on_info(self, e))
        self.Layout()

    def restore_unread(self, event):
        if hasattr(self, "current_unread") and self.current_unread:
            # 如果这条消息不在未读列表里，就加回去
            if self.current_unread not in [self.unread_list.GetString(i) for i in range(self.unread_list.GetCount())]:
                self.unread_list.Append(self.current_unread)

        # 按钮保持“标记未读”，不恢复详情
        self.topbar.set_button_label("标记未读")
        self.topbar.info_btn.Bind(wx.EVT_BUTTON, self.restore_unread)

    def on_unread_click(self, event):
        idx = event.GetSelection()
        text = self.unread_list.GetString(idx)

        # 删除未读消息
        if idx != wx.NOT_FOUND:
            self.unread_list.Delete(idx)

        # 聊天框显示消息
        self.chat_display.Clear()
        if text.startswith("[离线消息]"):
            # 离线消息 → 去掉前缀后显示
            clean_text = text.replace("[离线消息]", "").strip()
            self.chat_display.WriteText(f"[未读消息]\n{clean_text}\n")
        else:
            # 普通未读消息 → 原逻辑
            self.chat_display.WriteText(f"[未读消息]\n{text}\n")

        # 保存当前消息，供标记未读时使用（保留原始 text，不去掉前缀）
        self.current_unread = text

        # 设置顶部栏
        sender = text.replace("[离线消息]", "").split(":", 1)[0].strip() if ":" in text else "未知"
        self.topbar.set_label(f"未读消息: {sender}")
        self.topbar.set_button_label("标记未读")

        # 持续绑定 restore_unread
        self.topbar.info_btn.Bind(wx.EVT_BUTTON, self.restore_unread)

    def on_mark_read(self, event):
        # 直接取当前选中项索引
        idx = self.unread_list.GetSelection()
        if idx != wx.NOT_FOUND:
            self.unread_list.Delete(idx)

        # 删除后取消选中并隐藏按钮
        self.unread_list.DeselectAll()
        self.mark_read_btn.Hide()
        self.Layout()

    # ========== 切换聊天对象 ==========
    def on_double_click(self, event):
        item = event.GetItem()
        target = self.tree.GetItemText(item)
        if target in ("好友", "群聊"):
            return

        parent = self.tree.GetItemText(self.tree.GetItemParent(item))
        self.chat_display.Clear()

        if parent == "好友":
            self.chat_target = target
            self.chat_target_type = "friend"
            self.topbar.set_label(f"好友: {self.chat_target}")
            self.topbar.set_button_label("详情")
            # 绑定回正常的详情逻辑
            self.topbar.info_btn.Bind(wx.EVT_BUTTON, lambda e: on_info(self, e))

            history = get_messages(self.username, self.chat_target)
            for ts, sender, receiver, content in history:
                self.append_message(sender, content, is_self=(sender == self.username))

        elif parent == "群聊":
            self.chat_target = target
            self.chat_target_type = "group"
            members = list_group_members(self.chat_target)
            self.topbar.set_label(f"群聊: {self.chat_target} （{len(members)}人）")
            self.topbar.set_button_label("详情")
            # 绑定回正常的详情逻辑
            self.topbar.info_btn.Bind(wx.EVT_BUTTON, lambda e: on_info(self, e))

            history = get_group_messages(self.chat_target)
            for ts, sender, content in history:
                self.append_message(sender, content, is_self=(sender == self.username))

        self.mode = "chat"
        self.chat_input.Enable()
        self.send_btn.Enable()

    # ========== 退出登录 ==========
    def logout(self):
        confirm = wx.MessageBox("确认是否退出登录？", "提示",
                                wx.YES_NO | wx.ICON_QUESTION)
        if confirm != wx.YES:
            return

        self.running = False
        try:
            self.client.close()
        except:
            pass
        self.Destroy()

        # 回到登录界面
        from ui_main import MainApp
        app = wx.GetApp()
        if isinstance(app, MainApp):
            app.show_login()

    # ========== 设置窗口 ==========
    def open_settings(self):
        """打开设置窗口（字体 + 字号在同一个对话框，放大版，带预览）"""

        # 常用字体（微软雅黑放最前面）
        fonts = {
            "微软雅黑": "Microsoft YaHei",
            "宋体": "SimSun",
            "楷体": "KaiTi",
            "黑体": "SimHei",
            "Consolas（等宽）": "Consolas"
        }

        # 默认值
        default_face = "Microsoft YaHei"
        default_size = 14

        # 创建对话框，放大窗口
        dlg = wx.Dialog(self, title="设置字体", size=(400, 250))

        vbox = wx.BoxSizer(wx.VERTICAL)

        # 第一行：字体选择 + 字号输入
        hbox = wx.BoxSizer(wx.HORIZONTAL)

        font_choice = wx.Choice(dlg, choices=list(fonts.keys()))
        font_choice.SetSelection(0)  # 默认选中“微软雅黑”

        size_ctrl = wx.TextCtrl(dlg, value=str(default_size), style=wx.TE_CENTER, size=(60, -1))

        hbox.Add(wx.StaticText(dlg, label="字体："), 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)
        hbox.Add(font_choice, 1, wx.EXPAND | wx.ALL, 5)
        hbox.Add(wx.StaticText(dlg, label="字号："), 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)
        hbox.Add(size_ctrl, 0, wx.EXPAND | wx.ALL, 5)

        vbox.Add(hbox, 0, wx.EXPAND | wx.ALL, 10)

        # 第二行：预览区域
        preview = wx.StaticText(dlg, label="这是预览文字", style=wx.ALIGN_CENTER)
        preview.SetFont(wx.Font(default_size,
                                wx.FONTFAMILY_DEFAULT,
                                wx.FONTSTYLE_NORMAL,
                                wx.FONTWEIGHT_NORMAL,
                                faceName=default_face))
        vbox.Add(preview, 1, wx.EXPAND | wx.ALL, 10)

        # 更新预览函数
        def update_preview(event=None):
            try:
                size = int(size_ctrl.GetValue())
            except ValueError:
                size = default_size
            faceName = fonts.get(font_choice.GetStringSelection(), default_face)
            font = wx.Font(size,
                           wx.FONTFAMILY_DEFAULT,
                           wx.FONTSTYLE_NORMAL,
                           wx.FONTWEIGHT_NORMAL,
                           faceName=faceName)
            preview.SetFont(font)
            preview.SetLabel(f"这是 {font_choice.GetStringSelection()} {size} 号字的预览")

        font_choice.Bind(wx.EVT_CHOICE, update_preview)
        size_ctrl.Bind(wx.EVT_TEXT, update_preview)

        # 底部按钮
        btns = dlg.CreateButtonSizer(wx.OK | wx.CANCEL)
        vbox.Add(btns, 0, wx.ALIGN_CENTER | wx.ALL, 10)

        dlg.SetSizer(vbox)

        if dlg.ShowModal() == wx.ID_OK:
            try:
                size = int(size_ctrl.GetValue())
                faceName = fonts.get(font_choice.GetStringSelection(), default_face)
                font = wx.Font(size,
                               wx.FONTFAMILY_DEFAULT,
                               wx.FONTSTYLE_NORMAL,
                               wx.FONTWEIGHT_NORMAL,
                               faceName=faceName)
                self.chat_display.SetFont(font)
            except ValueError:
                wx.MessageBox("请输入有效的数字！", "错误", wx.OK | wx.ICON_ERROR)

        dlg.Destroy()

    # ========== 窗口关闭 ==========
    def on_close(self, event):
        self.running = False
        try:
            self.client.close()
        except:
            pass
        self.Destroy()


if __name__ == "__main__":
    app = wx.App(False)
    frame = ChatFrame("alice")  # 测试用户
    app.MainLoop()
