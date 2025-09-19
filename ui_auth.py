import wx
from db.users import get_conn, login, register, reset_password


# ========== 登录界面 ==========
class LoginFrame(wx.Frame):
    def __init__(self, on_success_callback, on_open_register, on_open_reset):
        super().__init__(None, title="登录", size=(400, 300))
        self.on_success_callback = on_success_callback
        self.on_open_register = on_open_register
        self.on_open_reset = on_open_reset

        panel = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)
        vbox.AddStretchSpacer(1)

        mid_box = wx.BoxSizer(wx.VERTICAL)
        self.username = wx.TextCtrl(panel, size=(300, -1))
        self.username.SetHint("用户名")
        self.password = wx.TextCtrl(panel, style=wx.TE_PASSWORD, size=(300, -1))
        self.password.SetHint("密码")
        self.result_label = wx.StaticText(panel, label="", style=wx.ALIGN_CENTER)

        btn_login = wx.Button(panel, label="登录", size=(120, 35))
        btn_register = wx.Button(panel, label="注册新用户", size=(120, 35))
        btn_reset = wx.Button(panel, label="找回密码", size=(120, 35))

        mid_box.Add(self.username, 0, wx.ALIGN_CENTER | wx.ALL, 10)
        mid_box.Add(self.password, 0, wx.ALIGN_CENTER | wx.ALL, 10)
        mid_box.Add(btn_login, 0, wx.ALIGN_CENTER | wx.ALL, 10)
        mid_box.Add(btn_register, 0, wx.ALIGN_CENTER | wx.ALL, 10)
        mid_box.Add(btn_reset, 0, wx.ALIGN_CENTER | wx.ALL, 10)
        mid_box.Add(self.result_label, 0, wx.ALIGN_CENTER | wx.ALL, 10)

        vbox.Add(mid_box, 0, wx.ALIGN_CENTER | wx.ALL, 10)
        vbox.AddStretchSpacer(2)
        panel.SetSizer(vbox)

        # 🔹 事件绑定
        btn_login.Bind(wx.EVT_BUTTON, self.on_login)
        btn_register.Bind(wx.EVT_BUTTON, lambda e: self.on_open_register())
        btn_reset.Bind(wx.EVT_BUTTON, lambda e: self.on_open_reset())

        self.Centre()
        # ❌ self.Show() 删除，避免重复创建
        self.Bind(wx.EVT_CLOSE, self.on_close)

    def on_login(self, event):
        username = self.username.GetValue().strip()
        password = self.password.GetValue().strip()
        if login(username, password):
            wx.MessageBox("登录成功 ✅", "提示", wx.OK | wx.ICON_INFORMATION)
            self.on_success_callback(username)
            self.Destroy()
        else:
            wx.MessageBox("用户名或密码错误 ❌", "错误", wx.OK | wx.ICON_ERROR)

    def on_close(self, event):
        """点 × 时退出整个应用"""
        wx.GetApp().ExitMainLoop()


# ========== 注册界面 ==========
class RegisterFrame(wx.Frame):
    def __init__(self, on_back_callback):
        super().__init__(None, title="用户注册", size=(600, 400))
        self.on_back_callback = on_back_callback

        panel = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)

        self.username = wx.TextCtrl(panel, size=(300, -1))
        self.username.SetHint("用户名")
        self.password = wx.TextCtrl(panel, style=wx.TE_PASSWORD, size=(300, -1))
        self.password.SetHint("密码")
        self.confirm_pwd = wx.TextCtrl(panel, style=wx.TE_PASSWORD, size=(300, -1))
        self.confirm_pwd.SetHint("确认密码")
        self.phone = wx.TextCtrl(panel, size=(300, -1))
        self.phone.SetHint("手机号")

        btn_ok = wx.Button(panel, label="注册", size=(120, 35))
        btn_back = wx.Button(panel, label="返回登录", size=(120, 35))

        vbox.Add(self.username, 0, wx.ALIGN_CENTER | wx.ALL, 10)
        vbox.Add(self.password, 0, wx.ALIGN_CENTER | wx.ALL, 10)
        vbox.Add(self.confirm_pwd, 0, wx.ALIGN_CENTER | wx.ALL, 10)
        vbox.Add(self.phone, 0, wx.ALIGN_CENTER | wx.ALL, 10)
        vbox.Add(btn_ok, 0, wx.ALIGN_CENTER | wx.ALL, 10)
        vbox.Add(btn_back, 0, wx.ALIGN_CENTER | wx.ALL, 10)

        panel.SetSizer(vbox)

        btn_ok.Bind(wx.EVT_BUTTON, self.on_register)
        btn_back.Bind(wx.EVT_BUTTON, lambda e: self.on_back_callback())

        self.Centre()
        # ❌ self.Show() 删除

    def on_register(self, event):
        username = self.username.GetValue().strip()
        pwd1 = self.password.GetValue().strip()
        pwd2 = self.confirm_pwd.GetValue().strip()
        phone = self.phone.GetValue().strip()

        if pwd1 != pwd2:
            wx.MessageBox("两次密码不一致 ❌", "错误", wx.OK | wx.ICON_ERROR)
            return

        if register(username, pwd1, username, phone):  # nickname 暂时用 username
            wx.MessageBox("注册成功 ✅", "提示", wx.OK | wx.ICON_INFORMATION)
            self.Close()
            self.on_back_callback()
        else:
            wx.MessageBox("注册失败（可能用户名已存在） ❌", "错误", wx.OK | wx.ICON_ERROR)


# ========== 找回密码界面 ==========
class PasswordResetFrame(wx.Frame):
    def __init__(self, on_back_callback):
        super().__init__(None, title="找回密码", size=(600, 400))
        self.on_back_callback = on_back_callback
        self.panel = wx.Panel(self)
        self.vbox = wx.BoxSizer(wx.VERTICAL)

        # 用户名 & 手机号
        self.username = wx.TextCtrl(self.panel, size=(300, -1))
        self.username.SetHint("用户名")
        self.phone = wx.TextCtrl(self.panel, size=(300, -1))
        self.phone.SetHint("手机号")

        self.btn_verify = wx.Button(self.panel, label="验证身份", size=(120, 35))
        self.btn_back = wx.Button(self.panel, label="返回登录", size=(120, 35))

        self.vbox.Add(self.username, 0, wx.ALIGN_CENTER | wx.ALL, 10)
        self.vbox.Add(self.phone, 0, wx.ALIGN_CENTER | wx.ALL, 10)
        self.vbox.Add(self.btn_verify, 0, wx.ALIGN_CENTER | wx.ALL, 10)
        self.vbox.Add(self.btn_back, 0, wx.ALIGN_CENTER | wx.ALL, 10)

        self.panel.SetSizer(self.vbox)

        # 事件绑定
        self.btn_verify.Bind(wx.EVT_BUTTON, self.on_verify)
        self.btn_back.Bind(wx.EVT_BUTTON, lambda e: self.on_back_callback())

        self.Centre()
        # ❌ self.Show() 删除

    def on_verify(self, event):
        username = self.username.GetValue().strip()
        phone = self.phone.GetValue().strip()

        # 查询数据库确认用户和手机号
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE username=%s AND phone=%s", (username, phone))
        row = cur.fetchone()
        cur.close()
        conn.close()

        if not row:
            wx.MessageBox("用户名或手机号不匹配 ❌", "错误", wx.OK | wx.ICON_ERROR)
            return

        # 验证成功
        wx.MessageBox("身份验证成功 ✅", "提示", wx.OK | wx.ICON_INFORMATION)

        # 禁用身份输入
        self.username.Disable()
        self.phone.Disable()
        self.btn_verify.Disable()

        # 添加新密码输入区
        self.new_pwd = wx.TextCtrl(self.panel, style=wx.TE_PASSWORD, size=(300, -1))
        self.new_pwd.SetHint("新密码")
        self.confirm_pwd = wx.TextCtrl(self.panel, style=wx.TE_PASSWORD, size=(300, -1))
        self.confirm_pwd.SetHint("确认密码")
        self.btn_ok = wx.Button(self.panel, label="确定", size=(120, 35))

        self.vbox.Add(self.new_pwd, 0, wx.ALIGN_CENTER | wx.ALL, 10)
        self.vbox.Add(self.confirm_pwd, 0, wx.ALIGN_CENTER | wx.ALL, 10)
        self.vbox.Add(self.btn_ok, 0, wx.ALIGN_CENTER | wx.ALL, 10)

        self.panel.Layout()

        # 绑定确定按钮
        self.btn_ok.Bind(wx.EVT_BUTTON, self.on_reset)

    def on_reset(self, event):
        username = self.username.GetValue().strip()
        phone = self.phone.GetValue().strip()
        pwd1 = self.new_pwd.GetValue().strip()
        pwd2 = self.confirm_pwd.GetValue().strip()

        if pwd1 != pwd2:
            wx.MessageBox("两次输入的密码不一致 ❌", "错误", wx.OK | wx.ICON_ERROR)
            return

        if reset_password(username, phone, pwd1):
            wx.MessageBox("密码修改成功 ✅", "提示", wx.OK | wx.ICON_INFORMATION)
            self.Close()
            self.on_back_callback()
        else:
            wx.MessageBox("密码修改失败 ❌", "错误", wx.OK | wx.ICON_ERROR)
