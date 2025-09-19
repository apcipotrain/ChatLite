import wx

class TopBar(wx.Panel):
    """
    顶部栏：显示当前聊天对象的标题 + 右侧详情按钮
    - set_label(text): 更新标题
    - set_button_label(text): 更新按钮文字
    """

    def __init__(self, parent, on_info_callback=None):
        super().__init__(parent)

        hbox = wx.BoxSizer(wx.HORIZONTAL)

        # 左侧标题
        self.target_label = wx.StaticText(self, label="未选择聊天对象", style=wx.ALIGN_CENTER)
        font = self.target_label.GetFont()
        font.PointSize += 4
        font = font.Bold()
        self.target_label.SetFont(font)

        # 右侧按钮
        self.info_btn = wx.Button(self, label="详情", size=(80, 30))

        hbox.Add(self.target_label, 1, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 10)
        hbox.Add(self.info_btn, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 10)

        self.SetSizer(hbox)

        # 如果传入了回调，就绑定到按钮
        if on_info_callback:
            self.info_btn.Bind(wx.EVT_BUTTON, on_info_callback)

    def set_label(self, text: str):
        """更新顶部标题"""
        self.target_label.SetLabel(text)

    def set_button_label(self, text: str):
        """更新按钮文字，比如 '详情' → '返回'"""
        self.info_btn.SetLabel(text)
