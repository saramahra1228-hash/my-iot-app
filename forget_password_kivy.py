"""
Forget Password Screen — Kivy version
--------------------------------------------------------------------
Recreates the original tkinter "Forget Password" screen, following the
same design system as admin_login_kivy.py:
  - Back arrow (top-left) -> Admin Login
  - "Forget Password" title + two-line subtitle
  - Illustration image (forget_password.png) instead of hand-drawn canvas art
  - "Email or User ID" input (centered, no icon — matches the reference design)
  - Rounded "Send Reset Link" button
  - "Back to Login" link at the bottom

Drop this file into your Kivy project (e.g. screens/forget_password.py) and
register it on your ScreenManager:

    from forget_password_kivy import ForgetPasswordScreen
    sm.add_widget(ForgetPasswordScreen(name="forget_password"))

Make sure ILLUSTRATION_FILENAME below matches your saved image
(default: "forget_password.png", placed next to this file).
"""

import os
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.image import Image as KvImage
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.widget import Widget
from kivy.uix.behaviors import ButtonBehavior
from kivy.graphics import Color, Rectangle, RoundedRectangle
from kivy.utils import get_color_from_hex as hexc
from kivy.metrics import dp, sp

ILLUSTRATION_FILENAME       = "forget_password.png"
ILLUSTRATION_SIZE           = dp(190)   # <-- illustration ka size, yahan se adjust karein
ILLUSTRATION_ANCHOR_HEIGHT  = dp(196)   # <-- iske gird ki space
BACK_SCREEN         = "admin_login"
RESET_SCREEN        = "admin_reset_password"
GREEN               = "#004D34"
FIELD_BG            = "#F4F4F4"
TEXT_GRAY           = "#555555"
PLACEHOLDER_GRAY    = "#A0A0A0"
ERROR_RED           = "#D32F2F"


class ClickableLabel(ButtonBehavior, Label):
    """A Label that behaves like a tappable link."""
    pass


class RoundedButton(ButtonBehavior, Label):
    """A green, rounded, tappable button (used for "Send Reset Link")."""

    def __init__(self, radius=dp(10), bg_hex=GREEN, **kwargs):
        super().__init__(**kwargs)
        self.color = (1, 1, 1, 1)
        self.bold = True
        self.font_size = sp(14)
        self.halign = "center"
        self.valign = "middle"
        with self.canvas.before:
            self._bg_color = Color(*hexc(bg_hex))
            self._bg_rect = RoundedRectangle(radius=[radius])
        self.bind(pos=self._redraw, size=self._redraw)

    def _redraw(self, *args):
        self._bg_rect.pos = self.pos
        self._bg_rect.size = self.size
        self.text_size = self.size

    def on_press(self):
        self._bg_color.rgba = (*hexc(GREEN)[:3], 0.85)

    def on_release(self):
        self._bg_color.rgba = (*hexc(GREEN)[:3], 1)


class InputField(BoxLayout):
    """A rounded, light-gray, center-aligned input row with no icon —
    matches the plain 'Email or User ID' field in the reference design."""

    def __init__(self, hint_text, is_password=False, **kwargs):
        super().__init__(orientation="horizontal", size_hint_y=None, height=dp(46),
                          padding=(dp(20), 0), **kwargs)

        with self.canvas.before:
            Color(*hexc(FIELD_BG))
            self._bg_rect = RoundedRectangle(radius=[dp(10)])
        self.bind(pos=self._redraw, size=self._redraw)

        self.text_input = TextInput(
            hint_text=hint_text,
            password=is_password,
            multiline=False,
            background_normal="",
            background_active="",
            background_color=(0, 0, 0, 0),
            foreground_color=hexc("#333333"),
            hint_text_color=hexc(PLACEHOLDER_GRAY),
            cursor_color=hexc(GREEN),
            font_size=sp(12),
            halign="center",
            padding=(0, dp(12), 0, 0),
            size_hint=(1, 1),
        )
        self.add_widget(self.text_input)

    def _redraw(self, *args):
        self._bg_rect.pos = self.pos
        self._bg_rect.size = self.size

    @property
    def text(self):
        return self.text_input.text


class ForgetPasswordScreen(Screen):
    """Full Forget Password screen."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        root = FloatLayout()
        self._root_layout = root
        self.add_widget(root)

        with root.canvas.before:
            Color(1, 1, 1, 1)
            self._bg_rect = Rectangle()
        root.bind(pos=self._redraw_bg, size=self._redraw_bg)

        content = BoxLayout(orientation="vertical", padding=(dp(28), dp(8), dp(28), dp(16)),
                             spacing=dp(6), size_hint=(1, 1))

        # ---- back arrow ----
        back_row = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(30))
        back_btn = ClickableLabel(text="<", font_size=sp(20), bold=True, color=(0, 0, 0, 1),
                                   size_hint_x=None, width=dp(30), halign="left")
        back_btn.bind(on_release=lambda inst: self._go_back())
        back_row.add_widget(back_btn)
        back_row.add_widget(Widget())
        content.add_widget(back_row)

        # ---- title ----
        content.add_widget(Label(text="Forget Password", font_size=sp(24), bold=True,
                                  color=(0, 0, 0, 1), size_hint_y=None, height=dp(32)))

        # ---- two-line subtitle, centered ----
        subtitle = Label(
            text="Enter your registered email or User ID\nto reset the password",
            font_size=sp(11), color=hexc(TEXT_GRAY), size_hint_y=None, height=dp(38),
            halign="center", valign="middle",
        )
        subtitle.bind(size=lambda inst, val: setattr(inst, "text_size", val))
        content.add_widget(subtitle)

        # ---- illustration ----
        illustration_anchor = AnchorLayout(size_hint_y=None, height=ILLUSTRATION_ANCHOR_HEIGHT,
                                            anchor_y="top")
        if os.path.exists(ILLUSTRATION_FILENAME):
            illustration = KvImage(source=ILLUSTRATION_FILENAME, allow_stretch=True, keep_ratio=True,
                                    size_hint=(None, None),
                                    size=(ILLUSTRATION_SIZE, ILLUSTRATION_SIZE))
        else:
            illustration = Label(text="[ Illustration ]", color=(0.3, 0.3, 0.3, 1))
        illustration_anchor.add_widget(illustration)
        content.add_widget(illustration_anchor)

        # ---- input field ----
        self.email_field = InputField(hint_text="Email or User ID")
        content.add_widget(self.email_field)

        content.add_widget(Widget(size_hint_y=None, height=dp(10)))

        # ---- status message ----
        self.status_label = Label(text="", font_size=sp(10), color=hexc(ERROR_RED),
                                   size_hint_y=None, height=dp(20))
        content.add_widget(self.status_label)

        # ---- send reset link button ----
        send_btn = RoundedButton(text="Send Reset Link", size_hint_y=None, height=dp(46))
        send_btn.bind(on_release=lambda inst: self.handle_send())
        content.add_widget(send_btn)

        content.add_widget(Widget())

        # ---- back to login link ----
        back_login_lbl = ClickableLabel(text="Back to Login", font_size=sp(11), bold=True,
                                         color=hexc("#333333"), size_hint_y=None, height=dp(30))
        back_login_lbl.bind(on_release=lambda inst: self._go_back())
        content.add_widget(back_login_lbl)

        root.add_widget(content)

    def _redraw_bg(self, *args):
        self._bg_rect.pos = self._root_layout.pos
        self._bg_rect.size = self._root_layout.size

    def _set_status(self, text, ok=False):
        self.status_label.text = text
        self.status_label.color = hexc(GREEN) if ok else hexc(ERROR_RED)

    def handle_send(self):
        # NOTE: Firebase abhi connect nahi hua, is liye filhaal koi bhi
        # (khali ya bhara) input Reset Password screen par navigate kar
        # dega — sirf UI flow test karne ke liye. Jab Firebase se email
        # verify/reset-link bhejne wala real backend jorenge, is jagah
        # asli validation + login_user()-jaisi call daal dein.
        value = self.email_field.text.strip()
        if value:
            self._set_status("Reset link bhej diya gaya hai.", ok=True)
        else:
            self._set_status("")
        self._go_reset()

    def _go_back(self):
        if self.manager:
            self.manager.current = BACK_SCREEN
        else:
            print(f"(standalone) would navigate to: {BACK_SCREEN}")

    def _go_reset(self):
        if self.manager:
            self.manager.current = RESET_SCREEN
        else:
            print(f"(standalone) would navigate to: {RESET_SCREEN}")


if __name__ == "__main__":
    from kivy.app import App
    from kivy.uix.screenmanager import ScreenManager
    from kivy.core.window import Window

    class PlaceholderScreen(Screen):
        def __init__(self, label_text, **kwargs):
            super().__init__(**kwargs)
            self.add_widget(Label(text=label_text, color=(0, 0, 0, 1)))

    class ForgetPasswordPreviewApp(App):
        def build(self):
            Window.size = (360, 640)
            Window.clearcolor = (1, 1, 1, 1)
            sm = ScreenManager()
            sm.add_widget(ForgetPasswordScreen(name="forget_password"))
            sm.add_widget(PlaceholderScreen("Admin Login\n(placeholder)", name="admin_login"))
            sm.add_widget(PlaceholderScreen("Reset Password\n(placeholder)", name="admin_reset_password"))
            sm.current = "forget_password"
            return sm

    ForgetPasswordPreviewApp().run()