import wx
import subprocess
import atexit
import os
import sys

from ui_auth import LoginFrame
from ui_chat import ChatFrame


class MainApp(wx.App):
    def OnInit(self):
        # === 启动服务器子进程 ===
        self.server_process = None
        self.start_server()

        self.login_frame = LoginFrame(self.show_chat, self.show_register, self.show_reset)
        self.login_frame.Show()
        return True

    def start_server(self):
        """启动 server.py 作为子进程"""
        try:
            # 获取 server.py 的绝对路径
            base_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
            server_path = os.path.join(base_dir, "server.py")

            # 启动服务器
            self.server_process = subprocess.Popen(
                [sys.executable, server_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            print("[系统] 服务器已启动")
        except Exception as e:
            wx.MessageBox(f"服务器启动失败: {e}", "错误", wx.OK | wx.ICON_ERROR)

        # 注册退出时关闭服务器
        atexit.register(self.stop_server)

    def stop_server(self):
        """关闭服务器子进程"""
        if self.server_process and self.server_process.poll() is None:
            self.server_process.terminate()
            print("[系统] 服务器已关闭")

    # === 窗口切换逻辑 ===
    def show_login(self):
        # 如果已经有一个登录界面并且正在显示，就不再新建
        if hasattr(self, "login_frame") and self.login_frame and self.login_frame.IsShown():
            self.login_frame.Raise()  # 把已有的窗口置顶
            return

        self.chat_frame = None
        self.login_frame = LoginFrame(self.show_chat, self.show_register, self.show_reset)
        self.login_frame.Show()

    def show_register(self):
        from ui_auth import RegisterFrame
        self.register_frame = RegisterFrame(self.show_login)
        self.register_frame.Show()
        if self.login_frame:
            self.login_frame.Hide()

    def show_reset(self):
        from ui_auth import PasswordResetFrame
        self.reset_frame = PasswordResetFrame(self.show_login)
        self.reset_frame.Show()
        if self.login_frame:
            self.login_frame.Hide()

    def show_chat(self, username):
        self.chat_frame = ChatFrame(username)
        self.chat_frame.Show()
        if self.login_frame:
            self.login_frame.Hide()


if __name__ == "__main__":
    app = MainApp(False)
    app.MainLoop()
