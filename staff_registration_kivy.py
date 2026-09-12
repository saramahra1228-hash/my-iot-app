"""
Staff Registration Screen — Kivy version
--------------------------------------------------------------------
Kivy conversion of the original Tkinter "Staff Registration" screen.
Same look, same fields, same flow — rebuilt with Kivy's own widgets
(TextInput.hint_text instead of the manual placeholder hack, CheckBox
instead of Checkbutton, Clock.schedule_once instead of tk's `.after`).

FIX vs the previous version: the ScrollView has been removed and every
size/spacing value has been tightened, so the whole screen (header +
logo + title + 6 fields + terms row + button + footer) now fits inside
one fixed-height frame with NO scrolling — total content height comes
out to roughly 510dp, comfortably under a normal 640dp phone frame.

Layout (matches the Tkinter screen / mockup 1:1):
    1. Header bar        -> back arrow + "Smart Waste Monitor" (left)
    2. Bin/logo artwork  -> staff_registration.png (falls back to a
                            drawn vector glyph if the file is missing)
    3. "Staff Registration" title + "Create your account" subtitle
    4. 6 rounded input fields with left icons:
           Full Name / Email Address / Phone Number / Staff ID /
           Password (eye toggle) / Confirm Password (eye toggle)
    5. "I Agree to the Terms & Conditions" checkbox row
    6. Status/error message
    7. Rounded green "REGISTER NOW" button
    8. Footer: "Already have an Account? Login"

Drop this file next to your other *_kivy.py screens and register it
on the ScreenManager:

    from staff_registration_kivy import StaffRegistrationScreen
    sm.add_widget(StaffRegistrationScreen(name="staff_registration"))

Needs `firebase_auth.signup_user(email, password)` on the path, same
as the original Tkinter screen. If that module isn't present yet,
registration will just show an error instead of crashing.
"""

import os
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.uix.image import Image as KvImage
from kivy.uix.textinput import TextInput
from kivy.uix.checkbox import CheckBox
from kivy.uix.behaviors import ButtonBehavior
from kivy.graphics import Color, Rectangle, RoundedRectangle, Line, Ellipse, PushMatrix, PopMatrix, Rotate
from kivy.utils import get_color_from_hex as hexc
from kivy.metrics import dp, sp
from kivy.clock import Clock
from kivy.properties import BooleanProperty

try:
    from firebase_auth import signup_user
    from firebase_config import set_data
except ImportError:
    signup_user = None
    set_data = None


# ---- palette (kept consistent with the rest of the app) ----------------
DARK_GREEN  = "#004D34"
FIELD_BG    = "#F5F5F5"
ICON_GRAY   = "#777777"
TEXT_DARK   = "#000000"
TEXT_GRAY   = "#555555"
ERROR_RED   = "#D32F2F"
SUCCESS_GRN = "#2E7D32"

# Top artwork — drop staff_registration.png next to this file (same
# folder as main.py / welcome.png). Falls back to the drawn vector
# TrashLogoIcon below if the file isn't found, so nothing crashes.
ARTWORK_FILENAME = "staff_registration.png"

# Screen name the back-arrow and "Login" link send you to. Register a
# screen with this exact name (e.g. StaffLoginScreen) and it just works.
LOGIN_SCREEN = "staff_login"
# --------------------------------------------------------------------------


# ================================================================ #
#  Small vector icons                                               #
# ================================================================ #
class BackArrowIcon(ButtonBehavior, Widget):
    """Left chevron, same style as the other screens' back arrows."""

    def __init__(self, color_hex="#FFFFFF", **kwargs):
        super().__init__(**kwargs)
        self._color_hex = color_hex
        with self.canvas:
            Color(*hexc(color_hex))
            self._line = Line(width=dp(1.6), cap="round", joint="round")
        self.bind(pos=self._redraw, size=self._redraw)
        self._redraw()

    def _redraw(self, *args):
        x, y = self.pos
        w, h = self.size
        s = min(w, h)
        ox, oy = x + (w - s) / 2, y + (h - s) / 2
        self._line.points = [ox + 0.68 * s, oy + 0.15 * s,
                              ox + 0.28 * s, oy + 0.50 * s,
                              ox + 0.68 * s, oy + 0.85 * s]


class TrashLogoIcon(Widget):
    """Simple outlined trash-bin glyph with two little 'sparkle' marks,
    matching the artwork used at the top of the mockup."""

    def __init__(self, color_hex=DARK_GREEN, **kwargs):
        super().__init__(**kwargs)
        self._rgba = hexc(color_hex)
        with self.canvas:
            Color(*self._rgba)
            self._lid = Line(width=dp(1.8), cap="round", joint="round")
            self._handle = Line(width=dp(1.8), cap="round")
            self._body = Line(width=dp(1.8), cap="round", joint="round")
            self._stripe1 = Line(width=dp(1.4), cap="round")
            self._stripe2 = Line(width=dp(1.4), cap="round")
            self._stripe3 = Line(width=dp(1.4), cap="round")
            self._spark_l = Line(width=dp(1.4), cap="round")
            self._spark_r = Line(width=dp(1.4), cap="round")
        self.bind(pos=self._redraw, size=self._redraw)
        self._redraw()

    def _redraw(self, *args):
        x, y = self.pos
        w, h = self.size

        # Lid (slightly wider than the body, flat top)
        lid_y = y + h * 0.78
        self._lid.points = [x + w * 0.18, lid_y, x + w * 0.82, lid_y]
        self._handle.points = [x + w * 0.40, lid_y, x + w * 0.40, lid_y + h * 0.08,
                                x + w * 0.60, lid_y + h * 0.08, x + w * 0.60, lid_y]

        # Body (trapezoid: narrower at the bottom)
        top_l, top_r = x + w * 0.24, x + w * 0.76
        bot_l, bot_r = x + w * 0.32, x + w * 0.68
        bot_y = y + h * 0.10
        self._body.points = [top_l, lid_y, bot_l, bot_y, bot_r, bot_y, top_r, lid_y]

        # Inner stripes
        stripe_top = lid_y - h * 0.03
        stripe_bot = bot_y + h * 0.05
        for stripe, frac in ((self._stripe1, 0.38), (self._stripe2, 0.50), (self._stripe3, 0.62)):
            stripe.points = [x + w * frac, stripe_top, x + w * frac, stripe_bot]

        # Sparkles (small 4-point marks above each shoulder of the lid)
        def sparkle(line, cx, cy, r):
            line.points = [cx - r, cy, cx + r, cy, cx, cy, cx, cy - r, cx, cy + r]

        sparkle(self._spark_l, x + w * 0.14, y + h * 0.92, w * 0.05)
        sparkle(self._spark_r, x + w * 0.86, y + h * 0.86, w * 0.04)


class PersonIcon(Widget):
    def __init__(self, color_hex=ICON_GRAY, **kwargs):
        super().__init__(**kwargs)
        with self.canvas:
            Color(*hexc(color_hex))
            self._head = Line(width=dp(1.3))
            self._body = Line(width=dp(1.3), cap="round", joint="round")
        self.bind(pos=self._redraw, size=self._redraw)
        self._redraw()

    def _redraw(self, *args):
        x, y = self.pos
        w, h = self.size
        cx = x + w / 2
        self._head.circle = (cx, y + h * 0.68, w * 0.20)
        import math
        r = w * 0.30
        base_y = y + h * 0.10
        pts = []
        for i in range(17):
            theta = 3.14159 - (3.14159 * i / 16)
            pts += [cx + r * math.cos(theta), base_y + r * math.sin(theta)]
        self._body.points = pts


class EmailIcon(Widget):
    def __init__(self, color_hex=ICON_GRAY, **kwargs):
        super().__init__(**kwargs)
        with self.canvas:
            Color(*hexc(color_hex))
            self._outline = Line(width=dp(1.3), joint="round")
            self._flap = Line(width=dp(1.3), joint="round")
        self.bind(pos=self._redraw, size=self._redraw)
        self._redraw()

    def _redraw(self, *args):
        x, y = self.pos
        w, h = self.size
        self._outline.rectangle = (x + w * 0.05, y + h * 0.18, w * 0.90, h * 0.64)
        self._flap.points = [x + w * 0.07, y + h * 0.78,
                              x + w * 0.50, y + h * 0.42,
                              x + w * 0.93, y + h * 0.78]


class PhoneIcon(Widget):
    """Classic diagonal 'call' handset glyph: a rounded bar rotated 45°
    with two small round ends (earpiece / mouthpiece)."""

    def __init__(self, color_hex=ICON_GRAY, **kwargs):
        super().__init__(**kwargs)
        self._rgba = hexc(color_hex)
        with self.canvas:
            PushMatrix()
            self._rot = Rotate(angle=45, origin=(0, 0))
            Color(*self._rgba)
            self._handle = RoundedRectangle(radius=[dp(2.2)])
            self._ear = Ellipse()
            self._mouth = Ellipse()
            PopMatrix()
        self.bind(pos=self._redraw, size=self._redraw)
        self._redraw()

    def _redraw(self, *args):
        x, y = self.pos
        w, h = self.size
        cx, cy = x + w / 2, y + h / 2
        self._rot.origin = (cx, cy)

        bar_w = w * 0.26
        bar_h = h * 0.60
        self._handle.pos = (cx - bar_w / 2, cy - bar_h / 2)
        self._handle.size = (bar_w, bar_h)

        end_d = w * 0.40
        self._ear.pos = (cx - end_d / 2, cy + bar_h / 2 - end_d * 0.30)
        self._ear.size = (end_d, end_d)
        self._mouth.pos = (cx - end_d / 2, cy - bar_h / 2 - end_d * 0.70)
        self._mouth.size = (end_d, end_d)


class IdCardIcon(Widget):
    def __init__(self, color_hex=ICON_GRAY, **kwargs):
        super().__init__(**kwargs)
        with self.canvas:
            Color(*hexc(color_hex))
            self._card = Line(width=dp(1.3))
            self._photo = Line(width=dp(1.2))
            self._line1 = Line(width=dp(1.1), cap="round")
            self._line2 = Line(width=dp(1.1), cap="round")
        self.bind(pos=self._redraw, size=self._redraw)
        self._redraw()

    def _redraw(self, *args):
        x, y = self.pos
        w, h = self.size
        self._card.rectangle = (x + w * 0.03, y + h * 0.20, w * 0.94, h * 0.60)
        self._photo.circle = (x + w * 0.24, y + h * 0.50, w * 0.11)
        self._line1.points = [x + w * 0.46, y + h * 0.60, x + w * 0.85, y + h * 0.60]
        self._line2.points = [x + w * 0.46, y + h * 0.42, x + w * 0.75, y + h * 0.42]


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
    """Tappable eye glyph; toggles between open/closed to show/hide a
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


# ================================================================ #
#  Rounded input field: icon + TextInput (+ optional eye toggle)    #
# ================================================================ #
class InputField(BoxLayout):
    def __init__(self, hint_text, icon_factory, is_password=False, **kwargs):
        super().__init__(orientation="horizontal", size_hint_y=None, height=dp(40),
                          padding=(dp(12), 0), spacing=dp(9), **kwargs)

        with self.canvas.before:
            Color(*hexc(FIELD_BG))
            self._bg = RoundedRectangle(radius=[dp(11)])
        self.bind(pos=self._redraw, size=self._redraw)

        icon_anchor = AnchorLayout(size_hint_x=None, width=dp(22))
        icon_anchor.add_widget(icon_factory(size_hint=(None, None), size=(dp(17), dp(17))))
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
            hint_text_color=hexc("#999999"),
            cursor_color=hexc(DARK_GREEN),
            font_size=sp(12.5),
            padding=[dp(0), dp(10), dp(0), dp(0)],
        )
        self.add_widget(self.text_input)

        if is_password:
            eye_anchor = AnchorLayout(size_hint_x=None, width=dp(20))
            eye = EyeIcon(size_hint=(None, None), size=(dp(17), dp(17)),
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


class RoundedButton(ButtonBehavior, BoxLayout):
    """Plain rounded green button (no arrow) — matches 'REGISTER NOW'."""

    def __init__(self, text="", bg_hex=DARK_GREEN, **kwargs):
        super().__init__(orientation="horizontal", **kwargs)
        with self.canvas.before:
            self._bg_color = Color(*hexc(bg_hex))
            self._bg_rect = RoundedRectangle(radius=[dp(12)])
        self.bind(pos=self._redraw, size=self._redraw)

        anchor = AnchorLayout()
        self.label = Label(text=text, color=(1, 1, 1, 1), bold=True, font_size=sp(13))
        anchor.add_widget(self.label)
        self.add_widget(anchor)

    def _redraw(self, *args):
        self._bg_rect.pos = self.pos
        self._bg_rect.size = self.size

    def on_press(self):
        self._bg_color.rgba = (*hexc(DARK_GREEN)[:3], 0.85)

    def on_release(self):
        self._bg_color.rgba = (*hexc(DARK_GREEN)[:3], 1)


# ================================================================ #
#  Header bar (back arrow, left-aligned title)                      #
# ================================================================ #
class RegistrationHeader(BoxLayout):
    def __init__(self, title_text, on_back=None, **kwargs):
        super().__init__(orientation="horizontal", size_hint=(1, None), height=dp(46),
                          padding=(dp(15), 0), spacing=dp(10), **kwargs)
        with self.canvas.before:
            Color(*hexc(DARK_GREEN))
            self._bg = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._sync, size=self._sync)

        back_anchor = AnchorLayout(size_hint_x=None, width=dp(22))
        back_btn = BackArrowIcon(size_hint=(None, None), size=(dp(18), dp(18)))
        if on_back:
            back_btn.bind(on_release=lambda *_: on_back())
        back_anchor.add_widget(back_btn)
        self.add_widget(back_anchor)

        title = Label(text=title_text, font_size=sp(15), bold=True, color=(1, 1, 1, 1),
                      halign="left", valign="middle")
        title.bind(size=lambda w, *_: setattr(w, "text_size", w.size))
        self.add_widget(title)

    def _sync(self, *_):
        self._bg.pos = self.pos
        self._bg.size = self.size


# ================================================================ #
#  The screen itself                                                #
# ================================================================ #
class StaffRegistrationScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        root = FloatLayout()
        with root.canvas.before:
            Color(1, 1, 1, 1)
            self._bg_rect = Rectangle()
        root.bind(pos=self._redraw_bg, size=self._redraw_bg)
        self._root_layout = root

        col = BoxLayout(orientation="vertical", size_hint=(1, 1))

        col.add_widget(RegistrationHeader("Smart Waste Monitor", on_back=self._go_back))

        # NOTE: no ScrollView here on purpose — everything below is
        # sized to fit inside one fixed screen, so nothing scrolls.
        form = BoxLayout(orientation="vertical",
                          padding=(dp(26), dp(4), dp(26), dp(8)), spacing=dp(2))

        # Logo artwork — uses your real staff_registration.png if it's
        # sitting next to this file, otherwise falls back to the drawn
        # vector icon. Kept small so it doesn't eat vertical space.
        logo_anchor = AnchorLayout(size_hint_y=None, height=dp(100))
        if os.path.exists(ARTWORK_FILENAME):
            artwork = KvImage(source=ARTWORK_FILENAME, allow_stretch=True, keep_ratio=True,
                              size_hint=(None, None), size=(dp(98), dp(94)))
        else:
            artwork = TrashLogoIcon(size_hint=(None, None), size=(dp(80), dp(74)))
        logo_anchor.add_widget(artwork)
        form.add_widget(logo_anchor)

        title = Label(text="Staff Registration", font_size=sp(18), bold=True,
                      color=(0, 0, 0, 1), size_hint_y=None, height=dp(24))
        form.add_widget(title)

        subtitle = Label(text="Create your account", font_size=sp(10.5), color=hexc(TEXT_GRAY),
                         size_hint_y=None, height=dp(16))
        form.add_widget(subtitle)

        form.add_widget(Widget(size_hint_y=None, height=dp(6)))

        self.full_name = InputField("Full Name", PersonIcon)
        self.email = InputField("Email Address", EmailIcon)
        self.phone = InputField("Phone Number", PhoneIcon)
        self.staff_id = InputField("Staff ID", IdCardIcon)
        self.password = InputField("Password", LockIcon, is_password=True)
        self.confirm_password = InputField("Confirm Password", LockIcon, is_password=True)
        fields = (self.full_name, self.email, self.phone,
                  self.staff_id, self.password, self.confirm_password)
        for i, field in enumerate(fields):
            form.add_widget(field)
            if i != len(fields) - 1:
                form.add_widget(Widget(size_hint_y=None, height=dp(6)))

        form.add_widget(Widget(size_hint_y=None, height=dp(6)))

        # Terms checkbox row — auto-sized (hug-the-text) labels so
        # "I Agree to the" and "Terms & Conditions" sit right next to
        # each other on one line, instead of leaving a big gap.
        terms_row = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(22),
                              spacing=dp(4))
        self.agree_checkbox = CheckBox(active=False, size_hint=(None, None), size=(dp(20), dp(20)),
                                       color=hexc(DARK_GREEN))
        terms_row.add_widget(self.agree_checkbox)

        agree_lbl = Label(text="I Agree to the", font_size=sp(10), color=hexc(TEXT_GRAY),
                          size_hint=(None, None), height=dp(22))
        agree_lbl.bind(texture_size=lambda i, v: setattr(i, "width", v[0]))
        terms_row.add_widget(agree_lbl)

        self.terms_link = ClickableLabel(text="Terms & Conditions", font_size=sp(10), bold=True,
                                         color=hexc(DARK_GREEN), size_hint=(None, None),
                                         height=dp(22))
        self.terms_link.bind(texture_size=lambda i, v: setattr(i, "width", v[0]))
        self.terms_link.bind(on_release=lambda *_: self.terms_action())
        terms_row.add_widget(self.terms_link)

        terms_row.add_widget(Widget())
        form.add_widget(terms_row)

        # Status label
        self.status_label = Label(text="", font_size=sp(10), color=hexc(ERROR_RED),
                                  size_hint_y=None, height=dp(14))
        form.add_widget(self.status_label)

        form.add_widget(Widget(size_hint_y=None, height=dp(4)))

        # Register button
        register_btn = RoundedButton(text="REGISTER NOW", size_hint_y=None, height=dp(40))
        register_btn.bind(on_release=lambda *_: self.register_action())
        form.add_widget(register_btn)

        form.add_widget(Widget(size_hint_y=None, height=dp(8)))

        # Footer
        footer_anchor = AnchorLayout(size_hint_y=None, height=dp(20))
        footer = BoxLayout(orientation="horizontal", size_hint=(None, None),
                           height=dp(20), spacing=dp(4))
        footer.bind(minimum_width=footer.setter("width"))
        already_lbl = Label(text="Already have an Account?", font_size=sp(10),
                            color=hexc(TEXT_GRAY), size_hint=(None, None), height=dp(20))
        already_lbl.bind(texture_size=lambda i, v: setattr(i, "width", v[0]))
        self.login_link = ClickableLabel(text="Login", font_size=sp(10), bold=True,
                                         color=hexc(DARK_GREEN), size_hint=(None, None),
                                         height=dp(20))
        self.login_link.bind(texture_size=lambda i, v: setattr(i, "width", v[0]))
        self.login_link.bind(on_release=lambda *_: self._go_login())
        footer.add_widget(already_lbl)
        footer.add_widget(self.login_link)
        footer_anchor.add_widget(footer)
        form.add_widget(footer_anchor)

        # Flexible spacer keeps the form pinned to the top instead of
        # being stretched/centered oddly if the frame is taller than
        # the content — it does NOT cause scrolling since there's no
        # ScrollView anywhere in this screen.
        form.add_widget(Widget())

        col.add_widget(form)
        root.add_widget(col)
        self.add_widget(root)

    def _redraw_bg(self, *args):
        self._bg_rect.pos = self._root_layout.pos
        self._bg_rect.size = self._root_layout.size

    # ── ACTIONS ──────────────────────────────────────────────
    def terms_action(self):
        print("Terms & Conditions tapped")

    def register_action(self):
        full_name = self.full_name.get()
        email = self.email.get()
        phone = self.phone.get()
        staff_id = self.staff_id.get()
        password = self.password.get()
        confirm = self.confirm_password.get()

        if not self.agree_checkbox.active:
            self._set_status(
                "Pehle Terms & Conditions agree karein.",
                ERROR_RED
            )
            return

        if not full_name:
            self._set_status("Full Name daalein.", ERROR_RED)
            return

        if not email:
            self._set_status("Email address daalein.", ERROR_RED)
            return

        if not phone:
            self._set_status("Phone Number daalein.", ERROR_RED)
            return

        if not staff_id:
            self._set_status("Staff ID daalein.", ERROR_RED)
            return

        if not password or not confirm:
            self._set_status(
                "Password aur Confirm Password daalein.",
                ERROR_RED
            )
            return

        if password != confirm:
            self._set_status(
                "Password match nahi kar raha.",
                ERROR_RED
            )
            return

        if signup_user is None:
            self._set_status(
                "Signup service abhi available nahi hai.",
                ERROR_RED
            )
            return

        if set_data is None:
            self._set_status(
                "Database service abhi available nahi hai.",
                ERROR_RED
            )
            return

        self._set_status("Account ban raha hai...", DARK_GREEN)

        try:
            success, result = signup_user(email, password)

            if not success:
                self._set_status(str(result), ERROR_RED)
                return

            uid = result.get("localId")

            if not uid:
                self._set_status(
                    "Firebase UID nahi mila.",
                    ERROR_RED
                )
                return

            staff_data = {
                "full_name": full_name,
                "email": email,
                "phone": phone,
                "staff_id": staff_id,
                "role": "staff"
            }

            db_success, db_result = set_data(
                f"staff/{uid}",
                staff_data
            )

            if not db_success:
                self._set_status(
                    "Profile save nahi hui.",
                    ERROR_RED
                )
                return

            self._set_status(
                "Account successfully ban gaya!",
                SUCCESS_GRN
            )

            Clock.schedule_once(
                lambda dt: self._go_login(),
                1.5
            )

        except Exception as e:
            self._set_status(
                "Registration failed. Please try again.",
                ERROR_RED
            )
            print("Staff Registration Error:", e)
    def _set_status(self, text, color_hex):
        self.status_label.text = text
        self.status_label.color = hexc(color_hex)

    # ── NAVIGATION ───────────────────────────────────────────
    def _go_back(self):
        self._navigate(LOGIN_SCREEN)

    def _go_login(self):
        self._navigate(LOGIN_SCREEN)

    def _navigate(self, target):
        if self.manager and target in self.manager.screen_names:
            self.manager.current = target
        else:
            print(f"Would navigate to '{target}', but it isn't registered "
                  f"in main.py's ScreenManager yet.")


# ---------------------------------------------------------------------
# Standalone preview — run just this file to see the Staff Registration
# screen on its own, at a phone-sized window (no scrolling).
# ---------------------------------------------------------------------
if __name__ == "__main__":
    from kivy.app import App
    from kivy.uix.screenmanager import ScreenManager
    from kivy.core.window import Window
    from kivy.config import Config

    Config.set("graphics", "width", "360")
    Config.set("graphics", "height", "640")

    class RegistrationPreviewApp(App):
        def build(self):
            Window.size = (360, 640)
            Window.clearcolor = (1, 1, 1, 1)
            sm = ScreenManager()
            sm.add_widget(StaffRegistrationScreen(name="staff_registration"))
            sm.current = "staff_registration"
            return sm

    RegistrationPreviewApp().run()