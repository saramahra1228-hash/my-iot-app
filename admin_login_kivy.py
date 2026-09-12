"""
Admin Login Screen — Kivy version
--------------------------------------------------------------------
Recreates the original tkinter "Admin Login" screen:
  - Back arrow (top-left) -> Role Selection
  - "Admin Login" title + subtitle
  - Circular avatar image (adminlogin.png)
  - "Email Address" input (with a person icon)
  - "Password" input (with a lock icon + Show/Hide toggle)
  - "Remember me" checkbox + "Forgot password?" link
  - Status message line (errors / "Checking...")
  - Rounded "LOGIN" button, wired to firebase_auth.login_user(...)

Drop this file into your Kivy project (e.g. screens/admin_login.py) and
register it on your ScreenManager:

    from admin_login_kivy import AdminLoginScreen
    sm.add_widget(AdminLoginScreen(name="admin_login"))

Make sure AVATAR_FILENAME below matches your saved avatar image
(default: "adminlogin.png", placed next to this file).
"""

import os
import math
import threading
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.image import Image as KvImage
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.widget import Widget
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.button import Button
from kivy.graphics import Color, Rectangle, RoundedRectangle, Ellipse, Line
from kivy.utils import get_color_from_hex as hexc
from kivy.metrics import dp, sp
from kivy.clock import Clock
from kivy.properties import BooleanProperty

try:
    from firebase_auth import login_user
except ImportError as exc:
    login_user = None
    FIREBASE_IMPORT_ERROR = str(exc)
else:
    FIREBASE_IMPORT_ERROR = ""


AVATAR_FILENAME     = "adminlogin.png"
AVATAR_SIZE         = dp(190)   # <-- size same rakha (aap ne kaha yeh theek hai)
AVATAR_ANCHOR_HEIGHT = dp(196)  # <-- container tight kiya gaya hai (extra khali space hataya)
CHECKBOX_SIZE       = dp(20)    # <-- "Remember me" checkbox ka size (isay yahan se adjust karein)
BACK_SCREEN         = "role_selection"
FORGOT_PWD_SCREEN   = "forgot_password"
DASHBOARD_SCREEN    = "admin_dashboard"
GREEN               = "#004D34"
FIELD_BG            = "#F4F4F4"
TEXT_GRAY           = "#555555"
PLACEHOLDER_GRAY    = "#A0A0A0"
ERROR_RED           = "#D32F2F"


class FieldIcon(Widget):
    """Small inline icon for input fields: a person silhouette for
    email/username, a simple padlock for password."""

    def __init__(self, icon_type="user", color_hex=TEXT_GRAY, **kwargs):
        super().__init__(**kwargs)
        self.icon_type = icon_type
        with self.canvas:
            Color(*hexc(color_hex))
            if icon_type == "user":
                self._head = Ellipse()
                self._body = Ellipse()
            else:  # "lock"
                self._shackle = Line(width=dp(1.6))
                self._body_rect = RoundedRectangle(radius=[dp(2)])
        self.bind(pos=self._redraw, size=self._redraw)
        self._redraw()

    def _redraw(self, *args):
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
            shackle_cx = cx
            shackle_base_y = y + h * 0.50
            segments = 16
            pts = []
            for i in range(segments + 1):
                theta = math.pi - (math.pi * i / segments)
                pts += [shackle_cx + shackle_r * math.cos(theta),
                        shackle_base_y + shackle_r * math.sin(theta)]
            self._shackle.points = pts

            body_w = w * 0.80
            body_h = h * 0.48
            self._body_rect.pos = (cx - body_w / 2, y + h * 0.02)
            self._body_rect.size = (body_w, body_h)


class ClickableLabel(ButtonBehavior, Label):
    """A Label that behaves like a tappable link."""
    pass


class RoundedButton(Button):
    """Standard Kivy Button with custom drawing; reliable on_release dispatch."""

    def __init__(self, radius=dp(10), bg_hex=GREEN, **kwargs):
        super().__init__(**kwargs)
        self.background_normal = ""
        self.background_down = ""
        self.background_color = (0, 0, 0, 0)
        self.color = (1, 1, 1, 1)
        self.bold = True
        self.font_size = sp(14)
        self.halign = "center"
        self.valign = "middle"
        self._normal_hex = bg_hex
        with self.canvas.before:
            self._bg_color = Color(*hexc(bg_hex))
            self._bg_rect = RoundedRectangle(radius=[radius])
        self.bind(pos=self._redraw, size=self._redraw, state=self._state_changed)
        self._redraw()

    def _redraw(self, *args):
        self._bg_rect.pos = self.pos
        self._bg_rect.size = self.size
        self.text_size = self.size

    def _state_changed(self, *args):
        if self.state == "down":
            self._bg_color.rgba = (*hexc(GREEN)[:3], 0.82)
        else:
            self._bg_color.rgba = (*hexc(self._normal_hex)[:3], 1)


class SquareCheckBox(ButtonBehavior, Widget):
    """A clean, sharp-cornered square checkbox drawn with our own graphics
    so the checkmark always stays neatly inside — size is fully adjustable
    via CHECKBOX_SIZE at the top of this file."""

    active = BooleanProperty(False)

    def __init__(self, box_hex=TEXT_GRAY, check_hex=GREEN, **kwargs):
        super().__init__(**kwargs)
        with self.canvas:
            self._border_color = Color(*hexc(box_hex))
            self._border = Line(width=dp(1.2))
            self._check_color = Color(*hexc(check_hex))
            self._check_color.a = 0
            self._check_line = Line(width=dp(1.8), cap="round", joint="round")
        self.bind(pos=self._redraw, size=self._redraw, active=self._redraw)
        self._redraw()

    def on_release(self):
        self.active = not self.active

    def _redraw(self, *args):
        x, y = self.pos
        w, h = self.size
        # Plain sharp-cornered square border (no rounding)
        self._border.rectangle = (x, y, w, h)

        if self.active:
            pad = w * 0.24
            self._check_color.a = 1
            self._check_line.points = [
                x + pad,           y + h * 0.50,
                x + w * 0.42,      y + pad,
                x + w - pad * 0.7, y + h - pad * 0.85,
            ]
        else:
            self._check_color.a = 0
            self._check_line.points = []


class InputField(BoxLayout):
    """A rounded, light-gray input row: [icon] [text input] (+ optional
    Show/Hide toggle for passwords)."""

    def __init__(self, icon_type, hint_text, is_password=False, **kwargs):
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
            password=is_password,
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

        self.toggle_btn = None
        if is_password:
            self.toggle_btn = ClickableLabel(text="Show", font_size=sp(10), bold=True,
                                              color=hexc(TEXT_GRAY),
                                              size_hint_x=None, width=dp(38))
            self.toggle_btn.bind(on_release=lambda inst: self._toggle_password())
            self.add_widget(self.toggle_btn)

    def _toggle_password(self):
        self.text_input.password = not self.text_input.password
        self.toggle_btn.text = "Hide" if not self.text_input.password else "Show"

    def _redraw(self, *args):
        self._bg_rect.pos = self.pos
        self._bg_rect.size = self.size

    @property
    def text(self):
        return self.text_input.text


class AdminLoginScreen(Screen):
    """Full Admin Login screen."""

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

        # ---- title + subtitle ----
        content.add_widget(Label(text="Admin Login", font_size=sp(24), bold=True,
                                  color=(0, 0, 0, 1), size_hint_y=None, height=dp(32)))
        content.add_widget(Label(text="Login to your administrator account", font_size=sp(11),
                                  color=hexc(TEXT_GRAY), size_hint_y=None, height=dp(20)))

        # ---- avatar (upar shift kiya gaya, spacing tight ki gayi) ----
        avatar_anchor = AnchorLayout(size_hint_y=None, height=AVATAR_ANCHOR_HEIGHT, anchor_y="top")
        if os.path.exists(AVATAR_FILENAME):
            avatar = KvImage(source=AVATAR_FILENAME, allow_stretch=True, keep_ratio=True,
                              size_hint=(None, None), size=(AVATAR_SIZE, AVATAR_SIZE))
        else:
            avatar = Label(text="[ Avatar ]", color=(0.3, 0.3, 0.3, 1))
        avatar_anchor.add_widget(avatar)
        content.add_widget(avatar_anchor)

        # ---- input fields ----
        self.user_id_field = InputField(icon_type="user", hint_text="Email Address")
        content.add_widget(self.user_id_field)

        self.password_field = InputField(icon_type="lock", hint_text="Password", is_password=True)
        content.add_widget(self.password_field)

        # ---- remember me / forgot password ----
        options_row = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(30),
                                 spacing=dp(6))
        remember_box = BoxLayout(orientation="horizontal", size_hint_x=None, width=dp(140),
                                  spacing=dp(4))
        self.remember_checkbox = SquareCheckBox(size_hint=(None, None),
                                                 size=(CHECKBOX_SIZE, CHECKBOX_SIZE))
        remember_box.add_widget(self.remember_checkbox)
        remember_box.add_widget(Label(text="Remember me", font_size=sp(10),
                                       color=hexc("#333333")))
        options_row.add_widget(remember_box)
        options_row.add_widget(Widget())
        forgot_btn = ClickableLabel(text="Forgot password?", font_size=sp(10), bold=True,
                                     color=hexc(GREEN), size_hint_x=None, width=dp(110))
        forgot_btn.bind(on_release=lambda inst: self._go_forgot())
        options_row.add_widget(forgot_btn)
        content.add_widget(options_row)

        # ---- status message ----
        self.status_label = Label(text="", font_size=sp(10), color=hexc(ERROR_RED),
                                   size_hint_y=None, height=dp(20))
        content.add_widget(self.status_label)

        content.add_widget(Widget(size_hint_y=None, height=dp(4)))

        # ---- login button ----
        self.login_btn = RoundedButton(
            text="LOGIN",
            size_hint_y=None,
            height=dp(46),
        )
        # Bind directly to the screen method. This avoids lambda/event
        # binding issues and makes the button reliably trigger navigation.
        self.login_btn.bind(on_release=self._on_login_button_release)
        content.add_widget(self.login_btn)

        content.add_widget(Widget())

        root.add_widget(content)

    def _redraw_bg(self, *args):
        self._bg_rect.pos = self._root_layout.pos
        self._bg_rect.size = self._root_layout.size

    def _set_status(self, text, ok=False):
        self.status_label.text = text
        self.status_label.color = hexc(GREEN) if ok else hexc(ERROR_RED)

    def _on_login_button_release(self, *_):
        """Handle the actual LOGIN touch event."""
        print("[ADMIN LOGIN] LOGIN button pressed")
        self.handle_login()

    def handle_login(self):
        """Validate credentials with Firebase without freezing the UI."""
        if getattr(self, "_login_running", False):
            return

        email = self.user_id_field.text.strip()
        password = self.password_field.text

        if not email:
            self._set_status("Email address daalein.")
            return
        if not password:
            self._set_status("Password daalein.")
            return

        if login_user is None:
            self._set_status("Firebase authentication module not found.")
            print(f"[ADMIN LOGIN] {FIREBASE_IMPORT_ERROR}")
            return

        self._login_running = True
        self.login_btn.disabled = True
        self._set_status("Checking...", ok=True)

        threading.Thread(
            target=self._login_worker,
            args=(email, password),
            daemon=True,
        ).start()

    def _login_worker(self, email, password):
        try:
            success, result = login_user(email, password)
        except Exception as exc:
            success, result = False, str(exc)

        Clock.schedule_once(
            lambda dt: self._finish_login(success, result),
            0,
        )

    def _finish_login(self, success, result):
        self._login_running = False
        self.login_btn.disabled = False

        if success:
            self._set_status("")
            self._go_dashboard()
        else:
            self._set_status(str(result))

    def on_enter(self, *args):
        # Clear any previous status when the login screen becomes visible.
        self._set_status("")

    def _go_dashboard(self):
        """Reliably switch from Admin Login to the real dashboard."""
        manager = self.manager
        print(f"[ADMIN LOGIN] manager={manager!r}")
        if manager is None:
            self._set_status("Dashboard navigation error")
            print("[ADMIN LOGIN] ERROR: ScreenManager is None")
            return

        try:
            target = DASHBOARD_SCREEN
            if manager.has_screen(target):
                print(f"[ADMIN LOGIN] opening {target}")
                manager.transition.direction = "left"
                manager.current = target
                # Verify on the next frame and recover if another screen
                # unexpectedly became current.
                from kivy.clock import Clock
                Clock.schedule_once(
                    lambda dt: self._verify_dashboard(manager, target),
                    0,
                )
            else:
                self._set_status(f"Screen not found: {target}")
                print(f"[ADMIN LOGIN] ERROR: {target} is not registered")
        except Exception as exc:
            self._set_status("Could not open dashboard")
            print(f"[ADMIN LOGIN] navigation error: {exc}")

    def _verify_dashboard(self, manager, target):
        try:
            if manager.current != target and manager.has_screen(target):
                print(
                    f"[ADMIN LOGIN] current screen is {manager.current}; "
                    f"forcing {target}"
                )
                manager.current = target
        except Exception as exc:
            print(f"[ADMIN LOGIN] verification error: {exc}")

    def _go_back(self):
        if self.manager:
            self.manager.current = BACK_SCREEN
        else:
            print(f"(standalone) would navigate to: {BACK_SCREEN}")

    def _go_forgot(self):
        if self.manager:
            self.manager.current = FORGOT_PWD_SCREEN
        else:
            print(f"(standalone) would navigate to: {FORGOT_PWD_SCREEN}")


