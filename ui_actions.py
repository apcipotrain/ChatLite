import wx
from db.friends import add_friend, remove_friend
from db.groups import list_group_members, join_group, create_group, leave_group, delete_group
from db.messages import get_messages, get_group_messages
from db.users import get_user

def on_info(cf, event):
    if cf.mode == "history":
        # 返回聊天模式
        cf.mode = "chat"
        cf.chat_display.Clear()
        cf.chat_input.Enable()
        cf.send_btn.Enable()
        cf.topbar.set_label("未选择聊天对象")
        cf.chat_target = None
        cf.chat_target_type = None
        return

    if not cf.chat_target:
        wx.MessageBox("请先选择聊天对象", "提示", wx.OK | wx.ICON_WARNING)
        return

    # ========== 好友 ==========
    if cf.chat_target_type == "friend":
        dlg = wx.Dialog(cf, title="好友信息", size=(350,250))
        panel = wx.Panel(dlg)
        vbox = wx.BoxSizer(wx.VERTICAL)

        # 信息展示
        info_text = wx.StaticText(panel, label=f"好友: {cf.chat_target}")
        vbox.Add(info_text, 0, wx.ALL | wx.EXPAND, 10)

        # 操作按钮
        btn_delete = wx.Button(panel, label="删除好友")
        btn_history = wx.Button(panel, label="查询历史记录")
        vbox.Add(btn_delete, 0, wx.EXPAND | wx.ALL, 5)
        vbox.Add(btn_history, 0, wx.EXPAND | wx.ALL, 5)

        # 底部确认/取消
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        btn_ok = wx.Button(panel, label="确定")
        btn_cancel = wx.Button(panel, label="取消")
        hbox.Add(btn_ok, 1, wx.EXPAND | wx.ALL, 5)
        hbox.Add(btn_cancel, 1, wx.EXPAND | wx.ALL, 5)
        vbox.Add(hbox, 0, wx.EXPAND | wx.ALL, 5)

        panel.SetSizer(vbox)

        # 状态标记
        action = {"type": None}

        # 点击事件
        btn_delete.Bind(wx.EVT_BUTTON, lambda e: action.update(type="delete"))
        btn_history.Bind(wx.EVT_BUTTON, lambda e: action.update(type="history"))

        btn_ok.Bind(wx.EVT_BUTTON, lambda e: (dlg.EndModal(wx.ID_OK)))
        btn_cancel.Bind(wx.EVT_BUTTON, lambda e: (dlg.EndModal(wx.ID_CANCEL)))

        if dlg.ShowModal() == wx.ID_OK:
            if action["type"] == "delete":
                if remove_friend(cf.username, cf.chat_target):
                    wx.MessageBox(f"已删除好友 {cf.chat_target}", "成功", wx.OK | wx.ICON_INFORMATION)
                    cf.refresh_friend_list()
                else:
                    wx.MessageBox("删除失败", "错误", wx.OK | wx.ICON_ERROR)
            elif action["type"] == "history":
                show_history(cf, "friend", cf.chat_target)
        dlg.Destroy()

    # ========== 群聊 ==========
    elif cf.chat_target_type == "group":
        members = list_group_members(cf.chat_target)
        owner = None
        clean_members = []
        for m in members:
            if "(群主)" in m:
                owner = m.replace("(群主)", "")
            clean_members.append(m)
        member_names = ", ".join(clean_members)

        dlg = wx.Dialog(cf, title="群聊信息", size=(400,300))
        panel = wx.Panel(dlg)
        vbox = wx.BoxSizer(wx.VERTICAL)

        # 信息展示
        info_text = wx.StaticText(panel, label=f"群聊: {cf.chat_target}\n成员: {member_names}")
        vbox.Add(info_text, 0, wx.ALL | wx.EXPAND, 10)

        # 操作按钮
        if cf.username == owner:
            btn_action = wx.Button(panel, label="解散群聊")
        else:
            btn_action = wx.Button(panel, label="退出群聊")
        btn_history = wx.Button(panel, label="查询历史记录")
        vbox.Add(btn_action, 0, wx.EXPAND | wx.ALL, 5)
        vbox.Add(btn_history, 0, wx.EXPAND | wx.ALL, 5)

        # 底部确认/取消
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        btn_ok = wx.Button(panel, label="确定")
        btn_cancel = wx.Button(panel, label="取消")
        hbox.Add(btn_ok, 1, wx.EXPAND | wx.ALL, 5)
        hbox.Add(btn_cancel, 1, wx.EXPAND | wx.ALL, 5)
        vbox.Add(hbox, 0, wx.EXPAND | wx.ALL, 5)

        panel.SetSizer(vbox)

        # 状态标记
        action = {"type": None}

        # 点击事件
        btn_action.Bind(wx.EVT_BUTTON, lambda e: action.update(type="action"))
        btn_history.Bind(wx.EVT_BUTTON, lambda e: action.update(type="history"))

        btn_ok.Bind(wx.EVT_BUTTON, lambda e: (dlg.EndModal(wx.ID_OK)))
        btn_cancel.Bind(wx.EVT_BUTTON, lambda e: (dlg.EndModal(wx.ID_CANCEL)))

        if dlg.ShowModal() == wx.ID_OK:
            if action["type"] == "action":
                if cf.username == owner:
                    if delete_group(cf.chat_target, cf.username):
                        wx.MessageBox(f"群聊 {cf.chat_target} 已解散", "成功", wx.OK | wx.ICON_INFORMATION)
                        cf.refresh_group_list()
                else:
                    if leave_group(cf.chat_target, cf.username):
                        wx.MessageBox(f"已退出群聊 {cf.chat_target}", "成功", wx.OK | wx.ICON_INFORMATION)
                        cf.refresh_group_list()
            elif action["type"] == "history":
                show_history(cf, "group", cf.chat_target)
        dlg.Destroy()

def show_history(cf, target_type, name):
    if target_type == "friend":
        history = get_messages(cf.username, name)
        if history:
            cf.mode = "history"
            cf.chat_target = None
            cf.chat_display.Clear()
            cf.chat_input.Disable()
            cf.send_btn.Disable()
            cf.topbar.set_label(f"历史记录查询：好友：{name}")
            for ts, sender, receiver, content in history:
                cf.chat_display.AppendText(f"[{ts}] {sender} -> {receiver}: {content}\n")
            # ✅ 滚动到底
            last_pos = cf.chat_display.GetLastPosition()
            cf.chat_display.ShowPosition(last_pos)
        else:
            wx.MessageBox("查无此记录", "提示", wx.OK | wx.ICON_WARNING)

    elif target_type == "group":
        history = get_group_messages(name)
        members = list_group_members(name)
        if history:
            cf.mode = "history"
            cf.chat_target = None
            cf.chat_display.Clear()
            cf.chat_input.Disable()
            cf.send_btn.Disable()
            cf.topbar.set_label(f"历史记录查询：群聊：{name}（{len(members)}人）")
            for ts, sender, content in history:
                cf.chat_display.AppendText(f"[{ts}] {sender}: {content}\n")
            # ✅ 滚动到底
            last_pos = cf.chat_display.GetLastPosition()
            cf.chat_display.ShowPosition(last_pos)
        else:
            wx.MessageBox("查无此记录", "提示", wx.OK | wx.ICON_WARNING)


def on_friend_mgmt(cf, event):
    dlg = wx.TextEntryDialog(cf, "请输入好友昵称：", "查找好友")
    if dlg.ShowModal() == wx.ID_OK:
        nickname = dlg.GetValue().strip()
        if nickname == cf.username:
            wx.MessageBox("不能添加自己为好友", "提示", wx.OK | wx.ICON_WARNING)
            return
        user_info = get_user(nickname)
        if not user_info:
            wx.MessageBox("查无此人", "提示", wx.OK | wx.ICON_WARNING)
        else:
            confirm = wx.MessageBox(f"是否确认添加 {nickname} 为好友？", "确认", wx.YES_NO | wx.ICON_QUESTION)
            if confirm == wx.YES:
                add_friend(cf.username, nickname)
                wx.MessageBox(f"已添加 {nickname} 为好友", "成功", wx.OK | wx.ICON_INFORMATION)
                cf.refresh_friend_list()
    dlg.Destroy()


def on_group_mgmt(cf, event):
    dlg = wx.SingleChoiceDialog(cf, "请选择操作：", "群聊管理", ["加入群聊", "创建群聊"])
    if dlg.ShowModal() == wx.ID_OK:
        choice = dlg.GetStringSelection()
        if choice == "加入群聊":
            name_dlg = wx.TextEntryDialog(cf, "请输入群聊名称：", "加入群聊")
            if name_dlg.ShowModal() == wx.ID_OK:
                gname = name_dlg.GetValue().strip()
                if join_group(gname, cf.username):
                    wx.MessageBox(f"已加入群聊 {gname}", "成功", wx.OK | wx.ICON_INFORMATION)
                    cf.refresh_group_list()
                else:
                    wx.MessageBox("加入失败，可能群不存在或已在群中", "错误", wx.OK | wx.ICON_ERROR)
            name_dlg.Destroy()
        elif choice == "创建群聊":
            name_dlg = wx.TextEntryDialog(cf, "请输入新群聊名称：", "创建群聊")
            if name_dlg.ShowModal() == wx.ID_OK:
                gname = name_dlg.GetValue().strip()
                if create_group(gname, cf.username):
                    wx.MessageBox(f"群聊 {gname} 创建成功", "成功", wx.OK | wx.ICON_INFORMATION)
                    cf.refresh_group_list()
                else:
                    wx.MessageBox("群聊创建失败，可能已存在", "错误", wx.OK | wx.ICON_ERROR)
            name_dlg.Destroy()
    dlg.Destroy()


def on_history(cf, event):
    dlg = wx.SingleChoiceDialog(cf, "请选择查询类型：", "历史记录", ["好友记录", "群聊记录"])
    if dlg.ShowModal() == wx.ID_OK:
        choice = dlg.GetStringSelection()
        name_dlg = wx.TextEntryDialog(cf, f"请输入{choice[:-2]}名称：", choice)
        if name_dlg.ShowModal() == wx.ID_OK:
            name = name_dlg.GetValue().strip()
            if choice == "好友记录":
                history = get_messages(cf.username, name)
                if history:
                    cf.mode = "history"
                    cf.chat_target = None
                    cf.chat_display.Clear()
                    cf.chat_input.Disable()
                    cf.send_btn.Disable()
                    cf.topbar.set_label(f"历史记录查询：好友：{name}")
                    for ts, sender, receiver, content in history:
                        cf.chat_display.AppendText(f"[{ts}] {sender} -> {receiver}: {content}\n")
                    last_pos = cf.chat_display.GetLastPosition()
                    cf.chat_display.ShowPosition(last_pos)
                else:
                    wx.MessageBox("查无此记录", "提示", wx.OK | wx.ICON_WARNING)
            else:  # 群聊
                history = get_group_messages(name)
                members = list_group_members(name)
                if history:
                    cf.mode = "history"
                    cf.chat_target = None
                    cf.chat_display.Clear()
                    cf.chat_input.Disable()
                    cf.send_btn.Disable()
                    cf.topbar.set_label(f"历史记录查询：群聊：{name}（{len(members)}人）")
                    for ts, sender, content in history:
                        cf.chat_display.AppendText(f"[{ts}] {sender}: {content}\n")
                    last_pos = cf.chat_display.GetLastPosition()
                    cf.chat_display.ShowPosition(last_pos)
                else:
                    wx.MessageBox("查无此记录", "提示", wx.OK | wx.ICON_WARNING)
        name_dlg.Destroy()
    dlg.Destroy()
