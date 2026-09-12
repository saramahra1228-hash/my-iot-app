"""
Staff Reset Password Screen — Firebase Connected
------------------------------------------------
Staff password reset screen for the Kivy app.

Firebase behavior:
- User enters New Password + Confirm Password.
- Password rules are validated locally.
- Current Firebase user is taken from firebase_auth.get_current_user().
- Password is updated directly in Firebase Authentication using the
  authenticated user's ID token.
- On success, the user is returned to Staff Login.

Register in main.py with:
    from staff_reset_password_kivy import StaffResetPasswordScreen
    sm.add_widget(StaffResetPasswordScreen(name="staff_reset_password"))
"""

import os
import json
import math
import urllib.request
import urllib.error

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

try:
    from firebase_auth import get_current_user, get_id_token
except ImportError:
    get_current_user = None
    get_id_token = None


ILLUSTRATION_FILENAME = "staff_reset_password.png"
ILLUSTRATION_SIZE = dp(150)
ILLUSTRATION_ANCHOR_HEIGHT = dp(156)

BACK_SCREEN = "staff_login"

GREEN = "#004D34"
CHECK_GREEN = "#1B7D53"
FIELD_BG = "#F4F4F4"
TEXT_GRAY = "#555555"
PLACEHOLDER_GRAY = "#A0A0A0"
ERROR_RED = "#D32F2F"

CHECKLIST_RULES = [
    "At least 8 characters",
    "One uppercase letter",
    "One number",
    "One special character",
]

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def _resolve_illustration_path(filename=ILLUSTRATION_FILENAME):
    candidates = [
        os.path.join(_SCRIPT_DIR, filename),
        os.path.join(_SCRIPT_DIR, "cache", filename),
        os.path.join(_SCRIPT_DIR, "assets", filename),
        os.path.join(os.getcwd(), filename),
        os.path.join(os.getcwd(), "cache", filename),
        filename,
    ]

    for path in candidates:
        if os.path.exists(path):
            print(f"(staff_reset_password) Found illustration at: {path}")
            return path

    print(f"(staff_reset_password) Could NOT find '{filename}'. Tried:")
    for path in candidates:
        print(f"    - {path}")
    return None


def _get_firebase_api_key():
    """
    Read Firebase Web API key from google-services.json.

    This supports the usual Android google-services.json structure and
    also checks a few common project locations.
    """
    candidates = [
        os.path.join(_SCRIPT_DIR, "google-services.json"),
        os.path.join(os.getcwd(), "google-services.json"),
        os.path.join(_SCRIPT_DIR, "android", "app", "google-services.json"),
    ]

    for path in candidates:
        if not os.path.exists(path):
            continue

        try:
            with open(path, "r", encoding="utf-8") as f:
                config = json.load(f)

            clients = config.get("client", [])
            for client in clients:
                api_keys = client.get("api_key", [])
                for item in api_keys:
                    key = item.get("current_key")
                    if key:
                        return key
        except Exception as e:
            print("Could not read google-services.json:", e)

    return None


def _firebase_change_password(new_password):
    """
    Change the currently logged-in Firebase user's password.

    Uses Firebase Authentication REST API:
    POST /v1/accounts:update?key=API_KEY
    """
    if get_current_user is None or get_id_token is None:
        return False, "Firebase authentication module available nahi hai."

    try:
        user = get_current_user()

        if not user:
            return False, "Staff login session nahi mili. Pehle login karein."

        id_token = get_id_token()

        if not id_token:
            return False, "Login session expire ho gayi. Dobara login karein."

        api_key = _get_firebase_api_key()

        if not api_key:
            return False, "Firebase API key nahi mili."

        url = (
            "https://identitytoolkit.googleapis.com/v1/accounts:update"
            f"?key={api_key}"
        )

        payload = {
            "idToken": id_token,
            "password": new_password,
            "returnSecureToken": True,
        }

        request = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        with urllib.request.urlopen(request, timeout=15) as response:
            result = json.loads(response.read().decode("utf-8"))

        # Firebase may return a refreshed token after changing the password.
        # Store it when the existing firebase_auth module supports this.
        try:
            import firebase_auth

            if hasattr(firebase_auth, "_store_session"):
                firebase_auth._store_session(result)
        except Exception:
            pass

        return True, result

    except urllib.error.HTTPError as e:
        try:
            body = e.read().decode("utf-8")
            error_data = json.loads(body)
            message = error_data.get("error", {}).get("message", str(e))
        except Exception:
            message = str(e)

        firebase_messages = {
            "INVALID_ID_TOKEN": "Login session expire ho gayi. Dobara login karein.",
            "TOKEN_EXPIRED": "Login session expire ho gayi. Dobara login karein.",
            "WEAK_PASSWORD": "Password kam az kam 6 characters ka hona chahiye.",
            "CREDENTIAL_TOO_OLD_LOGIN_AGAIN": "Security ke liye dobara login karein.",
            "USER_DISABLED": "Ye account disabled hai.",
        }

        return False, firebase_messages.get(message, message)

    except Exception as e:
        print("Firebase Change Password Error:", e)
        return False, "Password update nahi ho saka. Internet check karke dobara try karein."


class FieldIcon(Widget):
    """Small inline user or lock icon drawn with vector graphics."""

    def __init__(self, icon_type="user", color_hex=TEXT_GRAY, **kwargs):
        super().__init__(**kwargs)
        self.icon_type = icon_type

        with self.canvas:
            Color(*hexc(color_hex))

            if icon_type == "user":
                self._head = Ellipse()
                self._body = Ellipse()
            else:
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
            shackle_base_y = y + h * 0.50
            segments = 16
            pts = []

            for i in range(segments + 1):
                theta = math.pi - (math.pi * i / segments)
                pts += [
                    cx + shackle_r * math.cos(theta),
                    shackle_base_y + shackle_r * math.sin(theta),
                ]

            self._shackle.points = pts

            body_w = w * 0.80
            body_h = h * 0.48
            self._body_rect.pos = (
                cx - body_w / 2,
                y + h * 0.02,
            )
            self._body_rect.size = (body_w, body_h)


class CheckBadge(Widget):
    """Green check-circle badge."""

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

        self._circle.circle = (
            x + w / 2,
            y + h / 2,
            min(w, h) / 2 - dp(0.7),
        )

        pad = w * 0.28

        self._tick.points = [
            x + pad,
            y + h * 0.50,
            x + w * 0.42,
            y + pad,
            x + w - pad * 0.65,
            y + h - pad * 0.75,
        ]


class ClickableLabel(ButtonBehavior, Label):
    """A Label that behaves like a tappable link."""


class RoundedButton(ButtonBehavior, Label):
    """Green rounded button."""

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
    """Vector eye icon with slash while password is hidden."""

    revealed = BooleanProperty(False)

    def __init__(self, color_hex=TEXT_GRAY, **kwargs):
        super().__init__(**kwargs)

        with self.canvas:
            Color(*hexc(color_hex))
            self._eye_line = Line(width=dp(1.3))
            self._pupil = Ellipse()
            self._slash = Line(width=dp(1.3), cap="round")

        self.bind(
            pos=self._redraw,
            size=self._redraw,
            revealed=self._redraw,
        )
        self._redraw()

    def _redraw(self, *args):
        x, y = self.pos
        w, h = self.size
        cy = y + h * 0.5

        lx = x + w * 0.08
        rx = x + w * 0.92
        amp = h * 0.30
        segments = 14

        pts = []

        for i in range(segments + 1):
            t = i / segments
            px = lx + (rx - lx) * t
            pts.append((px, cy + amp * math.sin(math.pi * t)))

        for i in range(segments, -1, -1):
            t = i / segments
            px = lx + (rx - lx) * t
            pts.append((px, cy - amp * math.sin(math.pi * t)))

        flat = []
        for px, py in pts:
            flat += [px, py]

        self._eye_line.points = flat

        pupil_r = min(w, h) * 0.10
        self._pupil.pos = (
            x + w / 2 - pupil_r,
            cy - pupil_r,
        )
        self._pupil.size = (pupil_r * 2, pupil_r * 2)

        if not self.revealed:
            self._slash.points = [
                x + w * 0.14,
                y + h * 0.12,
                x + w * 0.86,
                y + h * 0.88,
            ]
        else:
            self._slash.points = []


class PasswordField(BoxLayout):
    """Rounded password row: icon + input + eye."""

    def __init__(self, icon_type, hint_text, **kwargs):
        super().__init__(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(46),
            padding=(dp(14), 0),
            spacing=dp(10),
            **kwargs,
        )

        with self.canvas.before:
            Color(*hexc(FIELD_BG))
            self._bg_rect = RoundedRectangle(radius=[dp(10)])

        self.bind(pos=self._redraw, size=self._redraw)

        icon_anchor = AnchorLayout(
            size_hint_x=None,
            width=dp(20),
        )

        icon_anchor.add_widget(
            FieldIcon(
                icon_type=icon_type,
                size_hint=(None, None),
                size=(dp(20), dp(20)),
            )
        )

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

        toggle_anchor = AnchorLayout(
            size_hint_x=None,
            width=dp(22),
        )

        self.toggle_btn = EyeToggle(
            size_hint=(None, None),
            size=(dp(17), dp(17)),
        )

        self.toggle_btn.bind(
            on_release=lambda inst: self._toggle_password()
        )

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


class StaffResetPasswordScreen(Screen):
    """Full Firebase-connected Staff Reset Password screen."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        root = FloatLayout()
        self._root_layout = root
        self.add_widget(root)

        with root.canvas.before:
            Color(1, 1, 1, 1)
            self._bg_rect = Rectangle()

        root.bind(
            pos=self._redraw_bg,
            size=self._redraw_bg,
        )

        content = BoxLayout(
            orientation="vertical",
            padding=(dp(28), dp(8), dp(28), dp(16)),
            spacing=dp(6),
            size_hint=(1, 1),
        )

        # Back arrow
        back_row = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(30),
        )

        back_btn = ClickableLabel(
            text="<",
            font_size=sp(20),
            bold=True,
            color=(0, 0, 0, 1),
            size_hint_x=None,
            width=dp(30),
            halign="left",
        )

        back_btn.bind(
            on_release=lambda inst: self._go_back()
        )

        back_row.add_widget(back_btn)
        back_row.add_widget(Widget())
        content.add_widget(back_row)

        # Title
        content.add_widget(
            Label(
                text="Reset Password",
                font_size=sp(24),
                bold=True,
                color=(0, 0, 0, 1),
                size_hint_y=None,
                height=dp(32),
            )
        )

        # Subtitle
        subtitle = Label(
            text="Create a new Password for\nyour Staff account",
            font_size=sp(11),
            color=hexc(TEXT_GRAY),
            size_hint_y=None,
            height=dp(38),
            halign="center",
            valign="middle",
        )

        subtitle.bind(
            size=lambda inst, val: setattr(inst, "text_size", val)
        )

        content.add_widget(subtitle)

        # Illustration
        illustration_anchor = AnchorLayout(
            size_hint_y=None,
            height=ILLUSTRATION_ANCHOR_HEIGHT,
            anchor_y="top",
        )

        image_path = _resolve_illustration_path(
            ILLUSTRATION_FILENAME
        )

        if image_path:
            illustration = KvImage(
                source=image_path,
                allow_stretch=True,
                keep_ratio=True,
                size_hint=(None, None),
                size=(ILLUSTRATION_SIZE, ILLUSTRATION_SIZE),
            )
        else:
            illustration = Label(
                text="[ Illustration ]",
                color=(0.3, 0.3, 0.3, 1),
            )

        illustration_anchor.add_widget(illustration)
        content.add_widget(illustration_anchor)

        # Password fields
        self.new_password_field = PasswordField(
            icon_type="user",
            hint_text="New Password",
        )
        content.add_widget(self.new_password_field)

        self.confirm_password_field = PasswordField(
            icon_type="lock",
            hint_text="Confirm Password",
        )
        content.add_widget(self.confirm_password_field)

        # Password rules
        rules_title = Label(
            text="Password must contains:",
            font_size=sp(12),
            bold=True,
            color=hexc("#333333"),
            size_hint_y=None,
            height=dp(26),
            halign="left",
            valign="middle",
        )

        rules_title.bind(
            size=lambda inst, val: setattr(
                inst, "text_size", val
            )
        )

        content.add_widget(rules_title)

        self.rule_rows = []

        for rule_text in CHECKLIST_RULES:
            row = BoxLayout(
                orientation="horizontal",
                size_hint_y=None,
                height=dp(22),
                spacing=dp(8),
            )

            badge = CheckBadge(
                size_hint=(None, None),
                size=(dp(16), dp(16)),
            )

            row.add_widget(badge)

            label = Label(
                text=rule_text,
                font_size=sp(10),
                color=hexc(TEXT_GRAY),
                halign="left",
                valign="middle",
            )

            label.bind(
                size=lambda inst, val: setattr(
                    inst, "text_size", val
                )
            )

            row.add_widget(label)
            content.add_widget(row)
            self.rule_rows.append(row)

        content.add_widget(
            Widget(
                size_hint_y=None,
                height=dp(10),
            )
        )

        # Status
        self.status_label = Label(
            text="",
            font_size=sp(10),
            color=hexc(ERROR_RED),
            size_hint_y=None,
            height=dp(20),
            halign="center",
            valign="middle",
        )

        self.status_label.bind(
            size=lambda inst, val: setattr(
                inst, "text_size", val
            )
        )

        content.add_widget(self.status_label)

        # Reset button
        reset_btn = RoundedButton(
            text="RESET PASSWORD",
            size_hint_y=None,
            height=dp(46),
        )

        reset_btn.bind(
            on_release=lambda inst: self.handle_reset()
        )

        content.add_widget(reset_btn)

        content.add_widget(Widget())

        # Back to Login
        back_login_lbl = ClickableLabel(
            text="Back to Login",
            font_size=sp(11),
            bold=True,
            color=hexc("#333333"),
            size_hint_y=None,
            height=dp(30),
        )

        back_login_lbl.bind(
            on_release=lambda inst: self._go_back()
        )

        content.add_widget(back_login_lbl)

        root.add_widget(content)

    def _redraw_bg(self, *args):
        self._bg_rect.pos = self._root_layout.pos
        self._bg_rect.size = self._root_layout.size

    def _set_status(self, text, ok=False):
        self.status_label.text = text
        self.status_label.color = (
            hexc(GREEN) if ok else hexc(ERROR_RED)
        )

    def _validate_password(self, password):
        """Validate all four password requirements."""

        if len(password) < 8:
            return False, "Password kam az kam 8 characters ka hona chahiye."

        if not any(ch.isupper() for ch in password):
            return False, "Password mein ek uppercase letter hona chahiye."

        if not any(ch.isdigit() for ch in password):
            return False, "Password mein ek number hona chahiye."

        if not any(not ch.isalnum() for ch in password):
            return False, "Password mein ek special character hona chahiye."

        return True, ""

    def handle_reset(self):
        """Validate and update password in Firebase Authentication."""

        new_pw = self.new_password_field.text.strip()
        confirm_pw = self.confirm_password_field.text.strip()

        if not new_pw or not confirm_pw:
            self._set_status("Dono fields bharein.")
            return

        if new_pw != confirm_pw:
            self._set_status("Passwords match nahi karte.")
            return

        valid, message = self._validate_password(new_pw)

        if not valid:
            self._set_status(message)
            return

        if get_current_user is None or get_id_token is None:
            self._set_status(
                "Firebase authentication service available nahi hai."
            )
            return

        self._set_status("Updating password...", ok=True)

        success, result = _firebase_change_password(new_pw)

        if success:
            self._set_status(
                "Password successfully update ho gaya.",
                ok=True,
            )
            print("Staff Password updated successfully!")

            # Small delay so the success message can be seen.
            from kivy.clock import Clock
            Clock.schedule_once(
                lambda dt: self._go_back(),
                1.0,
            )
        else:
            self._set_status(str(result))

    def _go_back(self):
        if self.manager and BACK_SCREEN in self.manager.screen_names:
            self.manager.current = BACK_SCREEN
        else:
            print(
                f"(staff_reset_password) Would navigate to "
                f"'{BACK_SCREEN}', but it isn't registered in "
                f"main.py's ScreenManager yet."
            )


if __name__ == "__main__":
    from kivy.app import App
    from kivy.uix.screenmanager import ScreenManager
    from kivy.core.window import Window

    class PlaceholderScreen(Screen):
        def __init__(self, label_text, **kwargs):
            super().__init__(**kwargs)
            self.add_widget(
                Label(
                    text=label_text,
                    color=(0, 0, 0, 1),
                )
            )

    class StaffResetPasswordPreviewApp(App):
        def build(self):
            Window.size = (360, 640)
            Window.clearcolor = (1, 1, 1, 1)

            sm = ScreenManager()

            sm.add_widget(
                StaffResetPasswordScreen(
                    name="staff_reset_password"
                )
            )

            sm.add_widget(
                PlaceholderScreen(
                    "Staff Login\n(placeholder)",
                    name="staff_login",
                )
            )

            sm.current = "staff_reset_password"
            return sm

    StaffResetPasswordPreviewApp().run()
