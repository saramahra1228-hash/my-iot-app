"""
Staff Login Screen — Kivy version
--------------------------------------------------------------------
Kivy conversion of the original Tkinter "Staff Login" screen. Same
look, same fields, same flow.

Layout (matches the mockup 1:1):
    1. Plain white background, small "‹" back arrow top-left
    2. "Staff Login" bold title (centered)
    3. "Login to your Staff account" subtitle (centered, gray)
    4. Big circular avatar (mint-green circle + dark-green person glyph)
    5. "Staff ID" rounded input field (person icon)
    6. "Password" rounded input field (lock icon + eye toggle)
    7. "Remember me" checkbox (left) / "Forget password?" link (right)
    8. Status/error message
    9. Dark-green "LOGIN" button (full width)
    10. "— OR —" divider
    11. Footer: "Don't have an account? Register"

Drop this file next to your other *_kivy.py screens and register it
on the ScreenManager:

    from staff_login_kivy import StaffLoginScreen
    sm.add_widget(StaffLoginScreen(name="staff_login"))

--------------------------------------------------------------------
FIREBASE STATUS (TEMPORARY):
--------------------------------------------------------------------
Firebase isn't wired up yet, so `handle_login()` currently skips the
`firebase_auth.login_user(email, password)` call and the Staff
ID / Password checks entirely — tapping LOGIN just navigates straight
to the dashboard, no matter what's (or isn't) typed in the fields.

Once Firebase is connected, replace the body of `handle_login()` with
the commented-out block right below it (kept in place for you) to
bring back real email/password validation.

All navigation goes through a safe _navigate() helper that checks
self.manager.screen_names first, so tapping a link to a screen that
isn't registered yet logs a console message instead of crashing the
whole app.
"""

from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.checkbox import CheckBox
from kivy.uix.behaviors import ButtonBehavior
from kivy.graphics import Color, Rectangle, RoundedRectangle, Line, Ellipse
from kivy.graphics.stencil_instructions import StencilPush, StencilPop, StencilUse, StencilUnUse
from kivy.utils import get_color_from_hex as hexc
from kivy.metrics import dp, sp
from kivy.properties import BooleanProperty

try:
    from firebase_auth import login_user
except ImportError:
    login_user = None


# ---- palette (kept consistent with the rest of the app) ----------------
DARK_GREEN   = "#004D34"
MINT_GREEN   = "#D3ECE1"
FIELD_BG     = "#F4F4F4"
ICON_GRAY    = "#777777"
TEXT_DARK    = "#000000"
TEXT_GRAY    = "#555555"
LINE_GRAY    = "#DDDDDD"
ERROR_RED    = "#D32F2F"
SUCCESS_GRN  = "#2E7D32"

# Screen names for navigation — update these once the real screens exist.
BACK_SCREEN       = "role_selection"
FORGOT_SCREEN     = "staff_forgot_password"
DASHBOARD_SCREEN  = "staff_dashboard"
REGISTER_SCREEN   = "staff_registration"
# --------------------------------------------------------------------------


# ================================================================ #
#  Small vector icons                                               #
# ================================================================ #
class BackChevronIcon(ButtonBehavior, Widget):
    """Plain black '‹' chevron (not on a colored bar, matches the mockup)."""

    def __init__(self, color_hex=TEXT_DARK, **kwargs):
        super().__init__(**kwargs)
        with self.canvas:
            Color(*hexc(color_hex))
            self._line = Line(width=dp(1.8), cap="round", joint="round")
        self.bind(pos=self._redraw, size=self._redraw)
        self._redraw()

    def _redraw(self, *args):
        x, y = self.pos
        w, h = self.size
        s = min(w, h)
        ox, oy = x + (w - s) / 2, y + (h - s) / 2
        self._line.points = [ox + 0.66 * s, oy + 0.14 * s,
                              ox + 0.30 * s, oy + 0.50 * s,
                              ox + 0.66 * s, oy + 0.86 * s]


class PersonIcon(Widget):
    """Small outline person glyph (used inside the Staff ID field)."""

    def __init__(self, color_hex=ICON_GRAY, **kwargs):
        super().__init__(**kwargs)
        with self.canvas:
            Color(*hexc(color_hex))
            self._head = Line(width=dp(1.3))
            self._body = Line(width=dp(1.3), cap="round", joint="round")
        self.bind(pos=self._redraw, size=self._redraw)
        self._redraw()

    def _redraw(self, *args):
        import math
        x, y = self.pos
        w, h = self.size
        cx = x + w / 2
        self._head.circle = (cx, y + h * 0.68, w * 0.20)
        r = w * 0.30
        base_y = y + h * 0.10
        pts = []
        for i in range(17):
            theta = 3.14159 - (3.14159 * i / 16)
            pts += [cx + r * math.cos(theta), base_y + r * math.sin(theta)]
        self._body.points = pts


class LockIcon(Widget):
    """Proper closed padlock: rounded body + an arch (shackle) sitting
    right on top, legs meeting the body's top edge."""

    def __init__(self, color_hex=ICON_GRAY, **kwargs):
        super().__init__(**kwargs)
        with self.canvas:
            Color(*hexc(color_hex))
            self._shackle = Line(width=dp(1.5), cap="round")
            self._body = RoundedRectangle(radius=[dp(1.8)])
        self.bind(pos=self._redraw, size=self._redraw)
        self._redraw()

    def _redraw(self, *args):
        x, y = self.pos
        w, h = self.size
        cx = x + w * 0.5

        body_w = w * 0.58
        body_h = h * 0.44
        body_x = cx - body_w / 2
        body_y = y + h * 0.08
        self._body.pos = (body_x, body_y)
        self._body.size = (body_w, body_h)

        shackle_r = w * 0.19
        shackle_cy = body_y + body_h
        # angle 0 -> 180 (counter-clockwise, east to west through north)
        # draws the upper-half arch, legs landing exactly on the body top.
        self._shackle.circle = (cx, shackle_cy, shackle_r, 0, 180)


class EyeIcon(ButtonBehavior, Widget):
    """Tappable eye glyph; toggles between open/closed to show/hide the
    password field's text."""

    closed = BooleanProperty(False)

    def __init__(self, color_hex=ICON_GRAY, on_toggle=None, **kwargs):
        super().__init__(**kwargs)
        self._rgba = hexc(color_hex)
        self._on_toggle = on_toggle
        with self.canvas:
            Color(*self._rgba)
            self._outline = Line(width=dp(1.3), joint="round")
            self._pupil = Ellipse()
        self.bind(pos=self._redraw, size=self._redraw, closed=self._redraw)
        self._redraw()

    def _redraw(self, *args):
        x, y = self.pos
        w, h = self.size
        cy = y + h * 0.5
        if self.closed:
            self._outline.points = [x + w * 0.10, cy, x + w * 0.90, cy]
            self._pupil.size = (0, 0)
        else:
            self._outline.ellipse = (x + w * 0.06, y + h * 0.18, w * 0.88, h * 0.64)
            r = w * 0.13
            self._pupil.pos = (x + w * 0.5 - r, cy - r)
            self._pupil.size = (r * 2, r * 2)

    def on_release(self):
        self.closed = not self.closed
        if self._on_toggle:
            self._on_toggle(self.closed)


class AvatarIcon(Widget):
    """Big circular avatar: mint-green circle + dark-green person
    silhouette, clipped to the circle with a stencil mask — same
    technique as admin_profile_kivy.py's AvatarWidget, just re-colored
    to match this screen's mockup."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(pos=self._redraw, size=self._redraw)
        self._redraw()

    def _redraw(self, *args):
        self.canvas.clear()
        x, y = self.pos
        w, h = self.size
        with self.canvas:
            Color(*hexc(MINT_GREEN))
            Ellipse(pos=(x, y), size=(w, h))

            StencilPush()
            Color(1, 1, 1, 1)
            Ellipse(pos=(x, y), size=(w, h))
            StencilUse()

            Color(*hexc(DARK_GREEN))
            Ellipse(pos=(x + w * 0.33, y + h * 0.54), size=(w * 0.34, w * 0.34))
            Ellipse(pos=(x + w * 0.04, y - h * 0.30), size=(w * 0.92, h * 0.85))

            StencilUnUse()
            Color(*hexc(MINT_GREEN))
            Ellipse(pos=(x, y), size=(w, h))
            StencilPop()


# ================================================================ #
#  Rounded input field: icon + TextInput (+ optional eye toggle)    #
# ================================================================ #
class InputField(BoxLayout):
    def __init__(self, hint_text, icon_factory, is_password=False, **kwargs):
        super().__init__(orientation="horizontal", size_hint_y=None, height=dp(46),
                          padding=(dp(14), 0), spacing=dp(10), **kwargs)

        with self.canvas.before:
            Color(*hexc(FIELD_BG))
            self._bg = RoundedRectangle(radius=[dp(12)])
        self.bind(pos=self._redraw, size=self._redraw)

        icon_anchor = AnchorLayout(size_hint_x=None, width=dp(24))
        icon_anchor.add_widget(icon_factory(size_hint=(None, None), size=(dp(19), dp(19))))
        self.add_widget(icon_anchor)

        self.text_input = TextInput(
            hint_text=hint_text,
            multiline=False,
            write_tab=False,
            password=is_password,
            background_normal="",
            background_active="",
            background_color=(0, 0, 0, 0),
            foreground_color=hexc(TEXT_DARK),
            hint_text_color=hexc("#A0A0A0"),
            cursor_color=hexc(DARK_GREEN),
            font_size=sp(13),
            padding=[dp(0), dp(12), dp(0), dp(0)],
        )
        self.add_widget(self.text_input)

        if is_password:
            eye_anchor = AnchorLayout(size_hint_x=None, width=dp(22))
            eye = EyeIcon(size_hint=(None, None), size=(dp(18), dp(18)),
                          on_toggle=lambda closed: setattr(self.text_input, "password", not closed))
            eye_anchor.add_widget(eye)
            self.add_widget(eye_anchor)

    def _redraw(self, *args):
        self._bg.pos = self.pos
        self._bg.size = self.size

    def get(self):
        return self.text_input.text.strip()


class ClickableLabel(ButtonBehavior, Label):
    """A Label that behaves like a tappable link."""
    pass


class LoginButton(ButtonBehavior, BoxLayout):
    """Full-width rounded dark-green LOGIN button."""

    def __init__(self, text="LOGIN", bg_hex=DARK_GREEN, **kwargs):
        super().__init__(orientation="horizontal", **kwargs)
        with self.canvas.before:
            self._bg_color = Color(*hexc(bg_hex))
            self._bg_rect = RoundedRectangle(radius=[dp(10)])
        self.bind(pos=self._redraw, size=self._redraw)

        anchor = AnchorLayout()
        self.label = Label(text=text, color=(1, 1, 1, 1), bold=True, font_size=sp(14))
        anchor.add_widget(self.label)
        self.add_widget(anchor)

    def _redraw(self, *args):
        self._bg_rect.pos = self.pos
        self._bg_rect.size = self.size

    def on_press(self):
        self._bg_color.rgba = (*hexc(DARK_GREEN)[:3], 0.85)

    def on_release(self):
        self._bg_color.rgba = (*hexc(DARK_GREEN)[:3], 1)


class DividerLine(Widget):
    def __init__(self, color_hex=LINE_GRAY, **kwargs):
        super().__init__(**kwargs)
        with self.canvas:
            Color(*hexc(color_hex))
            self._line = Line(width=dp(1))
        self.bind(pos=self._redraw, size=self._redraw)

    def _redraw(self, *args):
        x, y = self.pos
        w, h = self.size
        self._line.points = [x, y + h / 2, x + w, y + h / 2]


# ================================================================ #
#  The screen itself                                                #
# ================================================================ #
class StaffLoginScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        root = FloatLayout()
        with root.canvas.before:
            Color(1, 1, 1, 1)
            self._bg_rect = Rectangle()
        root.bind(pos=self._redraw_bg, size=self._redraw_bg)
        self._root_layout = root

        col = BoxLayout(orientation="vertical", padding=(dp(28), dp(18), dp(28), dp(18)),
                         spacing=dp(4))

        # Back arrow
        back_anchor = AnchorLayout(size_hint_y=None, height=dp(30), anchor_x="left")
        back_btn = BackChevronIcon(size_hint=(None, None), size=(dp(20), dp(20)))
        back_btn.bind(on_release=lambda *_: self._go_back())
        back_anchor.add_widget(back_btn)
        col.add_widget(back_anchor)

        # Title + subtitle
        title = Label(text="Staff Login", font_size=sp(23), bold=True, color=(0, 0, 0, 1),
                      size_hint_y=None, height=dp(34))
        col.add_widget(title)

        subtitle = Label(text="Login to your Staff account", font_size=sp(11.5),
                         color=hexc(TEXT_GRAY), size_hint_y=None, height=dp(24))
        col.add_widget(subtitle)

        col.add_widget(Widget(size_hint_y=None, height=dp(10)))

        # Avatar
        avatar_anchor = AnchorLayout(size_hint_y=None, height=dp(110), anchor_x="center")
        avatar_anchor.add_widget(AvatarIcon(size_hint=(None, None), size=(dp(100), dp(100))))
        col.add_widget(avatar_anchor)

        col.add_widget(Widget(size_hint_y=None, height=dp(14)))

        # Fields
        self.staff_id = InputField("Staff ID", PersonIcon)
        col.add_widget(self.staff_id)
        col.add_widget(Widget(size_hint_y=None, height=dp(8)))

        self.password = InputField("Password", LockIcon, is_password=True)
        col.add_widget(self.password)
        col.add_widget(Widget(size_hint_y=None, height=dp(10)))

        # Remember me / Forgot password row
        options_row = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(28))
        remember_box = BoxLayout(orientation="horizontal", size_hint=(None, None),
                                 size=(dp(140), dp(28)), spacing=dp(2))
        self.remember_checkbox = CheckBox(active=True, size_hint=(None, None), size=(dp(22), dp(22)),
                                          color=hexc(DARK_GREEN))
        remember_box.add_widget(self.remember_checkbox)
        remember_box.add_widget(Label(text="Remember me", font_size=sp(10.5),
                                      color=hexc(TEXT_DARK), size_hint=(None, None),
                                      size=(dp(100), dp(28))))
        options_row.add_widget(remember_box)

        forgot_anchor = AnchorLayout(anchor_x="right")
        self.forgot_link = ClickableLabel(text="Forget password?", font_size=sp(10.5), bold=True,
                                          color=hexc(DARK_GREEN), size_hint=(None, None),
                                          size=(dp(120), dp(28)))
        self.forgot_link.bind(on_release=lambda *_: self._go_forgot())
        forgot_anchor.add_widget(self.forgot_link)
        options_row.add_widget(forgot_anchor)
        col.add_widget(options_row)

        # Status label
        self.status_label = Label(text="", font_size=sp(10.5), color=hexc(ERROR_RED),
                                  size_hint_y=None, height=dp(20))
        col.add_widget(self.status_label)

        col.add_widget(Widget(size_hint_y=None, height=dp(4)))

        # LOGIN button
        login_btn = LoginButton(size_hint_y=None, height=dp(46))
        login_btn.bind(on_release=lambda *_: self.handle_login())
        col.add_widget(login_btn)

        col.add_widget(Widget(size_hint_y=None, height=dp(16)))

        # OR divider
        or_row = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(20), spacing=dp(10))
        or_row.add_widget(DividerLine())
        or_row.add_widget(Label(text="OR", font_size=sp(11), bold=True, color=hexc(TEXT_GRAY),
                                size_hint=(None, None), size=(dp(28), dp(20))))
        or_row.add_widget(DividerLine())
        col.add_widget(or_row)

        col.add_widget(Widget(size_hint_y=None, height=dp(12)))

        # Footer
        footer_anchor = AnchorLayout(size_hint_y=None, height=dp(24))
        footer = BoxLayout(orientation="horizontal", size_hint=(None, None), height=dp(24),
                           spacing=dp(4))
        footer.bind(minimum_width=footer.setter("width"))
        already_lbl = Label(text="Don't have an account?", font_size=sp(10.5),
                            color=hexc(TEXT_GRAY), size_hint=(None, None), height=dp(24))
        already_lbl.bind(texture_size=lambda i, v: setattr(i, "width", v[0]))
        self.register_link = ClickableLabel(text="Register", font_size=sp(10.5), bold=True,
                                            color=hexc(DARK_GREEN), size_hint=(None, None),
                                            height=dp(24))
        self.register_link.bind(texture_size=lambda i, v: setattr(i, "width", v[0]))
        self.register_link.bind(on_release=lambda *_: self._go_register())
        footer.add_widget(already_lbl)
        footer.add_widget(self.register_link)
        footer_anchor.add_widget(footer)
        col.add_widget(footer_anchor)

        col.add_widget(Widget())  # flexible bottom spacer

        root.add_widget(col)
        self.add_widget(root)

    def _redraw_bg(self, *args):
        self._bg_rect.pos = self._root_layout.pos
        self._bg_rect.size = self._root_layout.size
    # ── ACTIONS ──────────────────────────────────────────────
    def handle_login(self):
        email = self.staff_id.get()
        password = self.password.get()

        if not email:
            self._set_status("Email address daalein.", ERROR_RED)
            return

        if not password:
            self._set_status("Password daalein.", ERROR_RED)
            return

        if login_user is None:
            self._set_status(
                "Login service abhi available nahi hai.",
                ERROR_RED
            )
            return

        self._set_status("Checking...", DARK_GREEN)

        try:
            success, result = login_user(email, password)

            if success:
                self._set_status("Login successful!", SUCCESS_GRN)
                self._go_dashboard()
            else:
                self._set_status(str(result), ERROR_RED)

        except Exception as e:
            self._set_status(
                "Login failed. Please try again.",
                ERROR_RED
            )
            print("Staff Login Error:", e)

        # --------------------------------------------------------
        # ONCE FIREBASE IS CONNECTED: delete the two lines above and
        # uncomment this block instead to restore real validation.
        # --------------------------------------------------------
        # email = self.staff_id.get()
        # password = self.password.get()
        #
        # if not email:
        #     self._set_status("Email address daalein.", ERROR_RED)
        #     return
        # if not password:
        #     self._set_status("Password daalein.", ERROR_RED)
        #     return
        #
        # self._set_status("Checking...", DARK_GREEN)
        #
        # if login_user is None:
        #     self._set_status("Login service abhi available nahi hai.", ERROR_RED)
        #     return
        #
        # success, result = login_user(email, password)
        # if success:
        #     self._set_status("", ERROR_RED)
        #     self._go_dashboard()
        # else:
        #     self._set_status(str(result), ERROR_RED)

    def _set_status(self, text, color_hex):
        self.status_label.text = text
        self.status_label.color = hexc(color_hex)

    # ── NAVIGATION ───────────────────────────────────────────
    def _go_back(self):
        self._navigate(BACK_SCREEN)

    def _go_forgot(self):
        self._navigate(FORGOT_SCREEN)

    def _go_dashboard(self):
        self._navigate(DASHBOARD_SCREEN)

    def _go_register(self):
        self._navigate(REGISTER_SCREEN)

    def _navigate(self, target):
        """Safe navigation: never crashes if `target` isn't registered
        in main.py's ScreenManager yet — just logs it to the console."""
        if self.manager and target in self.manager.screen_names:
            self.manager.current = target
        else:
            print(f"(staff_login) Would navigate to '{target}', but it isn't "
                  f"registered in main.py's ScreenManager yet.")


# ---------------------------------------------------------------------
# Standalone preview — run just this file to see the Staff Login
# screen on its own, at a phone-sized window.
# ---------------------------------------------------------------------
if __name__ == "__main__":
    from kivy.app import App
    from kivy.uix.screenmanager import ScreenManager
    from kivy.core.window import Window
    from kivy.config import Config

    Config.set("graphics", "width", "360")
    Config.set("graphics", "height", "640")

    class LoginPreviewApp(App):
        def build(self):
            Window.size = (360, 640)
            Window.clearcolor = (1, 1, 1, 1)
            sm = ScreenManager()
            sm.add_widget(StaffLoginScreen(name="staff_login"))
            sm.current = "staff_login"
            return sm

    LoginPreviewApp().run()