"""
Staff Forget Password Screen — Kivy version
--------------------------------------------------------------------
Same design system as forget_password_kivy.py (the admin version),
just re-wired for the Staff flow:
  - Back arrow (top-left)         -> Staff Login
  - "Forget Password" title + two-line subtitle
  - Illustration image (staff_forget_password.png), falls back to a
    plain text placeholder if the file isn't found — never crashes
  - "Email or Staff ID" input (centered, no icon)
  - Rounded "Send Reset Link" button -> Staff Reset Password screen
  - "Back to Login" link at the bottom -> Staff Login

Drop this file into your Kivy project next to staff_login_kivy.py and
register it on your ScreenManager with the exact name staff_login_kivy.py
already expects for its "Forget password?" link:

    from staff_forget_password_kivy import StaffForgetPasswordScreen
    sm.add_widget(StaffForgetPasswordScreen(name="staff_forgot_password"))

(main.py has already been updated for you — see the accompanying file.)

Navigation to the reset-password screen uses a SAFE helper: if you
haven't built/registered "staff_reset_password" yet, tapping "Send
Reset Link" just prints a console message instead of crashing the app,
exactly like staff_login_kivy.py's own _navigate() helper.

--------------------------------------------------------------------
IMAGE NOT SHOWING? READ THIS:
--------------------------------------------------------------------
Kivy apps are usually launched with `python main.py` from your PROJECT
ROOT folder. A plain relative filename like "staff_forget_password.png"
is resolved against the CURRENT WORKING DIRECTORY at runtime, NOT
against the folder this .py file lives in. So if your image is sitting
inside a "cache" subfolder (as it was in your screenshot: cache >
staff_forget_password.png) instead of right next to this script, the
old os.path.exists() check silently fails and you get the placeholder.

This version fixes that by searching several likely locations
automatically (next to this script, in a "cache" folder, in the
project root) and printing which one it found (or didn't find) to the
terminal, so you can see exactly what's going on.

Simplest permanent fix: just move staff_forget_password.png so it sits
in the SAME folder as this .py file. But the search list below means
you don't have to — it'll find it in "cache" too.
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

ILLUSTRATION_FILENAME       = "staff_forget_password.png"
ILLUSTRATION_SIZE           = dp(190)   # <-- illustration ka size, yahan se adjust karein
ILLUSTRATION_ANCHOR_HEIGHT  = dp(196)   # <-- iske gird ki space

# Screen names — update these if your ScreenManager uses different ones.
BACK_SCREEN         = "staff_login"
RESET_SCREEN        = "staff_reset_password"

GREEN               = "#004D34"
FIELD_BG            = "#F4F4F4"
TEXT_GRAY           = "#555555"
PLACEHOLDER_GRAY    = "#A0A0A0"
ERROR_RED           = "#D32F2F"

# Folder this script lives in (works no matter what your current
# working directory is when you launch the app).
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def _resolve_illustration_path(filename=ILLUSTRATION_FILENAME):
    """Try a handful of likely locations for the illustration and
    return the first one that actually exists. Prints what it tried,
    so you can see in the terminal exactly why an image is/isn't
    loading instead of it failing silently."""
    candidates = [
        os.path.join(_SCRIPT_DIR, filename),                 # next to this .py file
        os.path.join(_SCRIPT_DIR, "cache", filename),         # your "cache" subfolder
        os.path.join(_SCRIPT_DIR, "assets", filename),        # common "assets" subfolder
        os.path.join(os.getcwd(), filename),                  # wherever python was run from
        os.path.join(os.getcwd(), "cache", filename),
        filename,                                             # last resort, as originally written
    ]
    for path in candidates:
        if os.path.exists(path):
            print(f"(staff_forget_password) Found illustration at: {path}")
            return path

    print(f"(staff_forget_password) Could NOT find '{filename}'. Tried:")
    for path in candidates:
        print(f"    - {path}")
    return None


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
    matches the plain 'Email or Staff ID' field in the reference design."""

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


class StaffForgetPasswordScreen(Screen):
    """Full Staff Forget Password screen."""

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
            text="Enter your registered Staff ID or Email\nto reset the password",
            font_size=sp(11), color=hexc(TEXT_GRAY), size_hint_y=None, height=dp(38),
            halign="center", valign="middle",
        )
        subtitle.bind(size=lambda inst, val: setattr(inst, "text_size", val))
        content.add_widget(subtitle)

        # ---- illustration ----
        illustration_anchor = AnchorLayout(size_hint_y=None, height=ILLUSTRATION_ANCHOR_HEIGHT,
                                            anchor_y="top")
        image_path = _resolve_illustration_path(ILLUSTRATION_FILENAME)
        if image_path:
            illustration = KvImage(source=image_path, allow_stretch=True, keep_ratio=True,
                                    size_hint=(None, None),
                                    size=(ILLUSTRATION_SIZE, ILLUSTRATION_SIZE))
        else:
            illustration = Label(text="[ Illustration ]", color=(0.3, 0.3, 0.3, 1))
        illustration_anchor.add_widget(illustration)
        content.add_widget(illustration_anchor)

        # ---- input field ----
        self.staff_id_field = InputField(hint_text="Email or Staff ID")
        content.add_widget(self.staff_id_field)

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
        # dega — sirf UI flow test karne ke liye. Jab Firebase se
        # staff ID/email verify + reset-link bhejne wala real backend
        # jorenge, is jagah asli validation + login_user()-jaisi call
        # daal dein.
        value = self.staff_id_field.text.strip()
        if value:
            self._set_status("Reset link bhej diya gaya hai.", ok=True)
        else:
            self._set_status("")
        self._go_reset()

    # ── NAVIGATION ───────────────────────────────────────────
    def _go_back(self):
        self._navigate(BACK_SCREEN)

    def _go_reset(self):
        self._navigate(RESET_SCREEN)

    def _navigate(self, target):
        """Safe navigation: never crashes if `target` isn't registered
        in main.py's ScreenManager yet — just logs it to the console.
        (Same pattern as staff_login_kivy.py / staff_registration_kivy.py.)"""
        if self.manager and target in self.manager.screen_names:
            self.manager.current = target
        else:
            print(f"(staff_forgot_password) Would navigate to '{target}', but it isn't "
                  f"registered in main.py's ScreenManager yet.")


if __name__ == "__main__":
    from kivy.app import App
    from kivy.uix.screenmanager import ScreenManager
    from kivy.core.window import Window

    class PlaceholderScreen(Screen):
        def __init__(self, label_text, **kwargs):
            super().__init__(**kwargs)
            self.add_widget(Label(text=label_text, color=(0, 0, 0, 1)))

    class StaffForgetPasswordPreviewApp(App):
        def build(self):
            Window.size = (360, 640)
            Window.clearcolor = (1, 1, 1, 1)
            sm = ScreenManager()
            sm.add_widget(StaffForgetPasswordScreen(name="staff_forgot_password"))
            sm.add_widget(PlaceholderScreen("Staff Login\n(placeholder)", name="staff_login"))
            sm.add_widget(PlaceholderScreen("Staff Reset Password\n(placeholder)", name="staff_reset_password"))
            sm.current = "staff_forgot_password"
            return sm

    StaffForgetPasswordPreviewApp().run()