"""
Reset Password Screen — Kivy version
--------------------------------------------------------------------
Recreates the original tkinter "Admin Reset Password" screen, following
the same design system as admin_login_kivy.py / forget_password_kivy.py:
  - Back arrow (top-left) -> Admin Login
  - "Reset Password" title + two-line subtitle
  - Green circular lock illustration (reset_password.png)
  - "New Password" input (person icon) + "Confirm Password" input (lock icon),
    each with a tappable eye (Show/Hide) toggle — matches the reference design
  - "Password must contains:" checklist with green check-circle badges
  - Rounded "RESET PASSWORD" button
  - "Back to Login" link at the bottom

Drop this file into your Kivy project (e.g. screens/reset_password.py) and
register it on your ScreenManager with the name "admin_reset_password" so
forget_password_kivy.py's "Send Reset Link" button lands here automatically:

    from reset_password_kivy import ResetPasswordScreen
    sm.add_widget(ResetPasswordScreen(name="admin_reset_password"))

Make sure ILLUSTRATION_FILENAME below matches your saved image
(default: "reset_password.png", placed next to this file).
"""

import os
import math
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.image import Image as KvImage
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.widget import Widget
from kivy.uix.behaviors import ButtonBehavior
from kivy.graphics import Color, Rectangle, RoundedRectangle, Line, Ellipse
from kivy.utils import get_color_from_hex as hexc
from kivy.metrics import dp, sp
from kivy.properties import BooleanProperty

ILLUSTRATION_FILENAME       = "reset_password.png"
ILLUSTRATION_SIZE           = dp(150)   # <-- illustration ka size, yahan se adjust karein
ILLUSTRATION_ANCHOR_HEIGHT  = dp(156)
BACK_SCREEN         = "admin_login"
GREEN               = "#004D34"
CHECK_GREEN         = "#1B7D53"
FIELD_BG            = "#F4F4F4"
TEXT_GRAY           = "#555555"
PLACEHOLDER_GRAY    = "#A0A0A0"
ERROR_RED           = "#D32F2F"

CHECKLIST_RULES = [
    "At least 8 characters",
    "One uppercase letter",
    "One number",
    "One special character",
]


class FieldIcon(Widget):
    """Small inline icon for input fields: a person silhouette or a
    simple padlock — matches the icon style used in admin_login_kivy.py."""

    def __init__(self, icon_type="user", color_hex=TEXT_GRAY, **kwargs):
        super().__init__(**kwargs)
        self.icon_type = icon_type
        with self.canvas:
            Color(*hexc(color_hex))
            if icon_type == "user":
                from kivy.graphics import Ellipse
                self._head = Ellipse()
                self._body = Ellipse()
            else:  # "lock"
                import math
                self._math = math
                self._shackle = Line(width=dp(1.6))
                self._body_rect = RoundedRectangle(radius=[dp(2)])
        self.bind(pos=self._redraw, size=self._redraw)
        self._redraw()

    def _redraw(self, *args):
        import math
        x, y = self.pos
        w, h = self.size
        cx = x + w / 2

        if self.icon_type == "user":
            head_d = h * 0.42
            self._head.size = (head_d, head_d)
            self._head.pos = (cx - head_d / 2, y + h * 0.46)
            body_w = w * 0.80
            body_h = h * 0.42
            self._body.size = (body_w, body_h)
            self._body.pos = (cx - body_w / 2, y + h * 0.02)
        else:
            shackle_r = w * 0.24
            shackle_base_y = y + h * 0.50
            segments = 16
            pts = []
            for i in range(segments + 1):
                theta = math.pi - (math.pi * i / segments)
                pts += [cx + shackle_r * math.cos(theta),
                        shackle_base_y + shackle_r * math.sin(theta)]
            self._shackle.points = pts

            body_w = w * 0.80
            body_h = h * 0.48
            self._body_rect.pos = (cx - body_w / 2, y + h * 0.02)
            self._body_rect.size = (body_w, body_h)


class CheckBadge(Widget):
    """Small green check-circle badge used in the password rules checklist."""

    def __init__(self, color_hex=CHECK_GREEN, **kwargs):
        super().__init__(**kwargs)
        with self.canvas:
            self._circle_color = Color(*hexc(color_hex))
            self._circle = Line(width=dp(1.3))
            self._tick_color = Color(*hexc(color_hex))
            self._tick = Line(width=dp(1.5), cap="round", joint="round")
        self.bind(pos=self._redraw, size=self._redraw)
        self._redraw()

    def _redraw(self, *args):
        x, y = self.pos
        w, h = self.size
        self._circle.circle = (x + w / 2, y + h / 2, min(w, h) / 2 - dp(0.7))
        pad = w * 0.28
        self._tick.points = [
            x + pad,            y + h * 0.50,
            x + w * 0.42,       y + pad,
            x + w - pad * 0.65, y + h - pad * 0.75,
        ]


class ClickableLabel(ButtonBehavior, Label):
    """A Label that behaves like a tappable link/icon."""
    pass


class RoundedButton(ButtonBehavior, Label):
    """A green, rounded, tappable button (used for RESET PASSWORD)."""

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


class EyeToggle(ButtonBehavior, Widget):
    """A tappable show/hide eye icon drawn entirely with vector graphics —
    a proper almond eye shape (not a plain oval), so it reads clearly as
    an eye icon even at small sizes. No emoji font dependency, so it
    always renders correctly. A diagonal slash is drawn across it while
    the password is hidden."""

    revealed = BooleanProperty(False)

    def __init__(self, color_hex=TEXT_GRAY, **kwargs):
        super().__init__(**kwargs)
        with self.canvas:
            Color(*hexc(color_hex))
            self._eye_line = Line(width=dp(1.3))
            self._pupil = Ellipse()
            self._slash = Line(width=dp(1.3), cap="round")
        self.bind(pos=self._redraw, size=self._redraw, revealed=self._redraw)
        self._redraw()

    def _redraw(self, *args):
        x, y = self.pos
        w, h = self.size
        cy = y + h * 0.5
        lx = x + w * 0.08
        rx = x + w * 0.92
        amp = h * 0.30
        segments = 14

        # Top lid: left corner to right corner, arching upward
        pts = []
        for i in range(segments + 1):
            t = i / segments
            px = lx + (rx - lx) * t
            pts.append((px, cy + amp * math.sin(math.pi * t)))
        # Bottom lid: right corner back to left corner, arching downward
        # (this naturally closes the loop back at the starting point)
        for i in range(segments, -1, -1):
            t = i / segments
            px = lx + (rx - lx) * t
            pts.append((px, cy - amp * math.sin(math.pi * t)))

        flat = []
        for px, py in pts:
            flat += [px, py]
        self._eye_line.points = flat

        pupil_r = min(w, h) * 0.10
        self._pupil.pos = (x + w / 2 - pupil_r, cy - pupil_r)
        self._pupil.size = (pupil_r * 2, pupil_r * 2)

        if not self.revealed:
            self._slash.points = [x + w * 0.14, y + h * 0.12, x + w * 0.86, y + h * 0.88]
        else:
            self._slash.points = []


class PasswordField(BoxLayout):
    """A rounded, light-gray password row: [icon] [text input] [eye toggle] —
    matches the New Password / Confirm Password fields in the reference design."""

    def __init__(self, icon_type, hint_text, **kwargs):
        super().__init__(orientation="horizontal", size_hint_y=None, height=dp(46),
                          padding=(dp(14), 0), spacing=dp(10), **kwargs)

        with self.canvas.before:
            Color(*hexc(FIELD_BG))
            self._bg_rect = RoundedRectangle(radius=[dp(10)])
        self.bind(pos=self._redraw, size=self._redraw)

        icon_anchor = AnchorLayout(size_hint_x=None, width=dp(20))
        icon_anchor.add_widget(FieldIcon(icon_type=icon_type, size_hint=(None, None),
                                          size=(dp(20), dp(20))))
        self.add_widget(icon_anchor)

        self.text_input = TextInput(
            hint_text=hint_text,
            password=True,
            multiline=False,
            background_normal="",
            background_active="",
            background_color=(0, 0, 0, 0),
            foreground_color=hexc("#333333"),
            hint_text_color=hexc(PLACEHOLDER_GRAY),
            cursor_color=hexc(GREEN),
            font_size=sp(12),
            padding=(0, dp(12), 0, 0),
            size_hint=(1, 1),
        )
        self.add_widget(self.text_input)

        toggle_anchor = AnchorLayout(size_hint_x=None, width=dp(22))
        self.toggle_btn = EyeToggle(size_hint=(None, None), size=(dp(17), dp(17)))
        self.toggle_btn.bind(on_release=lambda inst: self._toggle_password())
        toggle_anchor.add_widget(self.toggle_btn)
        self.add_widget(toggle_anchor)

    def _toggle_password(self):
        self.text_input.password = not self.text_input.password
        self.toggle_btn.revealed = not self.text_input.password

    def _redraw(self, *args):
        self._bg_rect.pos = self.pos
        self._bg_rect.size = self.size

    @property
    def text(self):
        return self.text_input.text


class ResetPasswordScreen(Screen):
    """Full Reset Password screen."""

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
        content.add_widget(Label(text="Reset Password", font_size=sp(24), bold=True,
                                  color=(0, 0, 0, 1), size_hint_y=None, height=dp(32)))

        # ---- two-line subtitle, centered ----
        subtitle = Label(
            text="Create a new Password for\nyour Admin account",
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

        # ---- password fields ----
        self.new_password_field = PasswordField(icon_type="user", hint_text="New Password")
        content.add_widget(self.new_password_field)

        self.confirm_password_field = PasswordField(icon_type="lock", hint_text="Confirm Password")
        content.add_widget(self.confirm_password_field)

        # ---- password rules checklist ----
        content.add_widget(Label(text="Password must contains:", font_size=sp(12), bold=True,
                                  color=hexc("#333333"), size_hint_y=None, height=dp(26),
                                  halign="left", valign="middle",
                                  text_size=(None, None)))
        # left-align the rules header (BoxLayout children are centered by default)
        rules_header = content.children[0]
        rules_header.bind(size=lambda inst, val: setattr(inst, "text_size", val))

        self.rule_rows = []
        for rule_text in CHECKLIST_RULES:
            row = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(22),
                             spacing=dp(8))
            badge = CheckBadge(size_hint=(None, None), size=(dp(16), dp(16)))
            row.add_widget(badge)
            label = Label(text=rule_text, font_size=sp(10), color=hexc(TEXT_GRAY),
                          halign="left", valign="middle")
            label.bind(size=lambda inst, val: setattr(inst, "text_size", val))
            row.add_widget(label)
            content.add_widget(row)
            self.rule_rows.append(row)

        content.add_widget(Widget(size_hint_y=None, height=dp(10)))

        # ---- status message ----
        self.status_label = Label(text="", font_size=sp(10), color=hexc(ERROR_RED),
                                   size_hint_y=None, height=dp(20))
        content.add_widget(self.status_label)

        # ---- reset password button ----
        reset_btn = RoundedButton(text="RESET PASSWORD", size_hint_y=None, height=dp(46))
        reset_btn.bind(on_release=lambda inst: self.handle_reset())
        content.add_widget(reset_btn)

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

    def handle_reset(self):
        new_pw = self.new_password_field.text.strip()
        confirm_pw = self.confirm_password_field.text.strip()

        if not new_pw or not confirm_pw:
            self._set_status("Dono fields bharein.")
            return
        if new_pw != confirm_pw:
            self._set_status("Passwords match nahi karte.")
            return

        self._set_status("Password successfully update ho gaya.", ok=True)
        print("Admin Password updated successfully!")

    def _go_back(self):
        if self.manager:
            self.manager.current = BACK_SCREEN
        else:
            print(f"(standalone) would navigate to: {BACK_SCREEN}")


if __name__ == "__main__":
    from kivy.app import App
    from kivy.uix.screenmanager import ScreenManager
    from kivy.core.window import Window

    class PlaceholderScreen(Screen):
        def __init__(self, label_text, **kwargs):
            super().__init__(**kwargs)
            self.add_widget(Label(text=label_text, color=(0, 0, 0, 1)))

    class ResetPasswordPreviewApp(App):
        def build(self):
            Window.size = (360, 640)
            Window.clearcolor = (1, 1, 1, 1)
            sm = ScreenManager()
            sm.add_widget(ResetPasswordScreen(name="admin_reset_password"))
            sm.add_widget(PlaceholderScreen("Admin Login\n(placeholder)", name="admin_login"))
            sm.current = "admin_reset_password"
            return sm

    ResetPasswordPreviewApp().run()