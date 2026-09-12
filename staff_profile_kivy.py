"""
Staff Profile Screen — Smart Waste Monitor
--------------------------------------------------------------------
Kivy conversion of the Tkinter `ProfileScreenStaff`.

Firebase-connected version:
- Loads the currently logged-in staff member from Firebase.
- Shows the staff's full name from Realtime Database.
- Uses Firebase logout when Logout is pressed.
- Keeps the existing vector-icon UI and navigation unchanged.
"""

from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.uix.behaviors import ButtonBehavior
from kivy.graphics import (
    Color,
    Ellipse,
    Rectangle,
    RoundedRectangle,
    Line,
)
from kivy.graphics.stencil_instructions import (
    StencilPush,
    StencilPop,
    StencilUse,
    StencilUnUse,
)
from kivy.properties import ListProperty
from kivy.metrics import dp, sp


# ================================================================
# FIREBASE
# ================================================================

try:
    from firebase_auth import get_current_user, logout_user
    from firebase_config import get_data
except ImportError:
    get_current_user = None
    logout_user = None
    get_data = None


# ================================================================
# PALETTE
# ================================================================

DARK_GREEN = (0 / 255, 77 / 255, 52 / 255, 1)
WHITE = (1, 1, 1, 1)
BG = (1, 1, 1, 1)
TEXT_DARK = (51 / 255, 51 / 255, 51 / 255, 1)
LIGHT_GRAY = (234 / 255, 234 / 255, 234 / 255, 1)
SILHOUETTE = (52 / 255, 73 / 255, 94 / 255, 1)
EDIT_GREEN = (46 / 255, 125 / 255, 50 / 255, 1)
RED_FG = (211 / 255, 47 / 255, 47 / 255, 1)
NAV_INACTIVE = (163 / 255, 196 / 255, 183 / 255, 1)


# ================================================================
# BACK ARROW ICON
# ================================================================

class BackArrowIcon(ButtonBehavior, Widget):
    color = ListProperty(list(WHITE))

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(
            pos=self.redraw,
            size=self.redraw,
            color=self.redraw
        )

    def redraw(self, *_):
        self.canvas.clear()

        with self.canvas:
            Color(*self.color)

            x, y = self.pos
            w, h = self.size

            s = min(w, h)
            ox = x + (w - s) / 2
            oy = y + (h - s) / 2

            Line(
                points=[
                    ox + 0.68 * s,
                    oy + 0.15 * s,
                    ox + 0.28 * s,
                    oy + 0.5 * s,
                    ox + 0.68 * s,
                    oy + 0.85 * s,
                ],
                width=dp(1.5),
                cap="round",
                joint="round",
            )


# ================================================================
# CHECK ICON
# ================================================================

class CheckIcon(Widget):
    color = ListProperty(list(EDIT_GREEN))

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(
            pos=self.redraw,
            size=self.redraw,
            color=self.redraw
        )

    def redraw(self, *_):
        self.canvas.clear()

        with self.canvas:
            Color(*self.color)

            x, y = self.pos
            w, h = self.size

            s = min(w, h)
            ox = x + (w - s) / 2
            oy = y + (h - s) / 2

            Line(
                points=[
                    ox + 0.15 * s,
                    oy + 0.50 * s,
                    ox + 0.42 * s,
                    oy + 0.22 * s,
                    ox + 0.88 * s,
                    oy + 0.78 * s,
                ],
                width=dp(1.7),
                cap="round",
                joint="round",
            )


# ================================================================
# LOCK ICON
# ================================================================

class LockIcon(Widget):
    color = ListProperty(list(TEXT_DARK))

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(
            pos=self.redraw,
            size=self.redraw,
            color=self.redraw
        )

    def redraw(self, *_):
        self.canvas.clear()

        with self.canvas:
            Color(*self.color)

            x, y = self.pos
            w, h = self.size

            s = min(w, h)
            ox = x + (w - s) / 2
            oy = y + (h - s) / 2

            Line(
                circle=(
                    ox + 0.5 * s,
                    oy + 0.62 * s,
                    0.20 * s,
                    20,
                    160,
                ),
                width=dp(1.6),
            )

            RoundedRectangle(
                pos=(
                    ox + 0.24 * s,
                    oy + 0.10 * s,
                ),
                size=(
                    0.52 * s,
                    0.42 * s,
                ),
                radius=[dp(2)],
            )


# ================================================================
# BELL ICON
# ================================================================

class BellIcon(Widget):
    color = ListProperty(list(TEXT_DARK))

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(
            pos=self.redraw,
            size=self.redraw,
            color=self.redraw
        )

    def redraw(self, *_):
        self.canvas.clear()

        with self.canvas:
            Color(*self.color)

            x, y = self.pos
            w, h = self.size

            s = min(w, h)
            ox = x + (w - s) / 2
            oy = y + (h - s) / 2

            Line(
                circle=(
                    ox + 0.5 * s,
                    oy + 0.58 * s,
                    0.28 * s,
                    0,
                    180,
                ),
                width=dp(1.6),
            )

            Line(
                points=[
                    ox + 0.22 * s,
                    oy + 0.58 * s,
                    ox + 0.22 * s,
                    oy + 0.30 * s,
                ],
                width=dp(1.6),
            )

            Line(
                points=[
                    ox + 0.78 * s,
                    oy + 0.58 * s,
                    ox + 0.78 * s,
                    oy + 0.30 * s,
                ],
                width=dp(1.6),
            )

            Line(
                points=[
                    ox + 0.16 * s,
                    oy + 0.30 * s,
                    ox + 0.84 * s,
                    oy + 0.30 * s,
                ],
                width=dp(1.6),
                cap="round",
            )

            Line(
                circle=(
                    ox + 0.5 * s,
                    oy + 0.20 * s,
                    0.07 * s,
                ),
                width=dp(1.6),
            )


# ================================================================
# LOGOUT ICON
# ================================================================

class LogoutIcon(Widget):
    color = ListProperty(list(RED_FG))

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(
            pos=self.redraw,
            size=self.redraw,
            color=self.redraw
        )

    def redraw(self, *_):
        self.canvas.clear()

        with self.canvas:
            Color(*self.color)

            x, y = self.pos
            w, h = self.size

            s = min(w, h)
            ox = x + (w - s) / 2
            oy = y + (h - s) / 2

            Line(
                rectangle=(
                    ox + 0.18 * s,
                    oy + 0.20 * s,
                    0.32 * s,
                    0.60 * s,
                ),
                width=dp(1.6),
            )

            Line(
                points=[
                    ox + 0.42 * s,
                    oy + 0.5 * s,
                    ox + 0.86 * s,
                    oy + 0.5 * s,
                ],
                width=dp(1.6),
                cap="round",
            )

            Line(
                points=[
                    ox + 0.68 * s,
                    oy + 0.32 * s,
                    ox + 0.88 * s,
                    oy + 0.5 * s,
                    ox + 0.68 * s,
                    oy + 0.68 * s,
                ],
                width=dp(1.6),
                cap="round",
                joint="round",
            )


# ================================================================
# NAVIGATION HOME ICON
# ================================================================

class NavHomeIcon(Widget):
    color = ListProperty(list(WHITE))

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(
            pos=self.redraw,
            size=self.redraw,
            color=self.redraw
        )

    def redraw(self, *_):
        self.canvas.clear()

        with self.canvas:
            Color(*self.color)

            x, y = self.pos
            w, h = self.size

            s = min(w, h)
            ox = x + (w - s) / 2
            oy = y + (h - s) / 2

            Line(
                points=[
                    ox + 0.5 * s,
                    oy + 0.88 * s,
                    ox + 0.12 * s,
                    oy + 0.52 * s,
                    ox + 0.30 * s,
                    oy + 0.52 * s,
                    ox + 0.30 * s,
                    oy + 0.14 * s,
                    ox + 0.70 * s,
                    oy + 0.14 * s,
                    ox + 0.70 * s,
                    oy + 0.52 * s,
                    ox + 0.88 * s,
                    oy + 0.52 * s,
                    ox + 0.5 * s,
                    oy + 0.88 * s,
                ],
                width=dp(1.6),
                joint="round",
                close=False,
            )


# ================================================================
# NAVIGATION PIN ICON
# ================================================================

class NavPinIcon(Widget):
    color = ListProperty(list(NAV_INACTIVE))

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(
            pos=self.redraw,
            size=self.redraw,
            color=self.redraw
        )

    def redraw(self, *_):
        self.canvas.clear()

        with self.canvas:
            Color(*self.color)

            x, y = self.pos
            w, h = self.size

            s = min(w, h)
            ox = x + (w - s) / 2
            oy = y + (h - s) / 2

            Line(
                circle=(
                    ox + 0.5 * s,
                    oy + 0.65 * s,
                    0.24 * s,
                ),
                width=dp(1.6),
            )

            Line(
                points=[
                    ox + 0.5 * s,
                    oy + 0.42 * s,
                    ox + 0.5 * s,
                    oy + 0.10 * s,
                ],
                width=dp(1.6),
                cap="round",
            )

            Line(
                circle=(
                    ox + 0.5 * s,
                    oy + 0.65 * s,
                    0.07 * s,
                ),
                width=dp(1.4),
            )


# ================================================================
# NAVIGATION CLOCK ICON
# ================================================================

class NavClockIcon(Widget):
    color = ListProperty(list(NAV_INACTIVE))

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(
            pos=self.redraw,
            size=self.redraw,
            color=self.redraw
        )

    def redraw(self, *_):
        self.canvas.clear()

        with self.canvas:
            Color(*self.color)

            x, y = self.pos
            w, h = self.size

            s = min(w, h)
            ox = x + (w - s) / 2
            oy = y + (h - s) / 2

            Line(
                circle=(
                    ox + 0.5 * s,
                    oy + 0.5 * s,
                    0.38 * s,
                ),
                width=dp(1.6),
            )

            Line(
                points=[
                    ox + 0.5 * s,
                    oy + 0.5 * s,
                    ox + 0.5 * s,
                    oy + 0.76 * s,
                ],
                width=dp(1.5),
                cap="round",
            )

            Line(
                points=[
                    ox + 0.5 * s,
                    oy + 0.5 * s,
                    ox + 0.70 * s,
                    oy + 0.5 * s,
                ],
                width=dp(1.5),
                cap="round",
            )


# ================================================================
# NAVIGATION PERSON ICON
# ================================================================

class NavPersonIcon(Widget):
    color = ListProperty(list(NAV_INACTIVE))

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(
            pos=self.redraw,
            size=self.redraw,
            color=self.redraw
        )

    def redraw(self, *_):
        self.canvas.clear()

        with self.canvas:
            Color(*self.color)

            x, y = self.pos
            w, h = self.size

            s = min(w, h)
            ox = x + (w - s) / 2
            oy = y + (h - s) / 2

            Line(
                circle=(
                    ox + 0.5 * s,
                    oy + 0.68 * s,
                    0.16 * s,
                ),
                width=dp(1.6),
            )

            Line(
                circle=(
                    ox + 0.5 * s,
                    oy + 0.16 * s,
                    0.34 * s,
                    20,
                    160,
                ),
                width=dp(1.6),
            )


# ================================================================
# AVATAR
# ================================================================

class AvatarWidget(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.bind(
            pos=self._redraw,
            size=self._redraw
        )

        self._redraw()

    def _redraw(self, *args):
        self.canvas.clear()

        x, y = self.pos
        w, h = self.size

        with self.canvas:
            Color(*LIGHT_GRAY)

            Ellipse(
                pos=(x, y),
                size=(w, h)
            )

            StencilPush()

            Color(1, 1, 1, 1)

            Ellipse(
                pos=(x, y),
                size=(w, h)
            )

            StencilUse()

            Color(*SILHOUETTE)

            Ellipse(
                pos=(x + w * 0.33, y + h * 0.54),
                size=(w * 0.34, w * 0.34)
            )

            Ellipse(
                pos=(x + w * 0.04, y - h * 0.30),
                size=(w * 0.92, h * 0.85)
            )

            StencilUnUse()

            Color(1, 1, 1, 1)

            Ellipse(
                pos=(x, y),
                size=(w, h)
            )

            StencilPop()


# ================================================================
# PROFILE ROW
# ================================================================

class ProfileRow(ButtonBehavior, BoxLayout):

    def __init__(
        self,
        icon_widget_factory,
        label_text,
        on_press_cb=None,
        **kwargs
    ):
        super().__init__(
            orientation="vertical",
            size_hint_y=None,
            height=dp(52),
            **kwargs
        )

        self.label_text = label_text
        self._cb = on_press_cb

        with self.canvas.before:
            self._bg_color = Color(*WHITE)
            self._bg_rect = Rectangle(
                pos=self.pos,
                size=self.size
            )

        self.bind(
            pos=self._update_bg,
            size=self._update_bg
        )

        row = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(44),
            padding=(dp(8), 0),
            spacing=dp(14)
        )

        icon_box = AnchorLayout(
            size_hint_x=None,
            width=dp(28)
        )

        icon_box.add_widget(
            icon_widget_factory()
        )

        text_lbl = Label(
            text=label_text,
            color=list(TEXT_DARK),
            font_size=sp(14),
            halign="left",
            valign="middle"
        )

        text_lbl.bind(
            size=lambda inst, val:
            setattr(inst, "text_size", val)
        )

        row.add_widget(icon_box)
        row.add_widget(text_lbl)

        self.add_widget(row)

        divider = Widget(
            size_hint_y=None,
            height=dp(1)
        )

        with divider.canvas:
            Color(*LIGHT_GRAY)

            self._div_rect = Rectangle(
                pos=divider.pos,
                size=divider.size
            )

        divider.bind(
            pos=self._update_divider,
            size=self._update_divider
        )

        self.add_widget(divider)

    def _update_bg(self, instance, value):
        self._bg_rect.pos = instance.pos
        self._bg_rect.size = instance.size

    def _update_divider(self, instance, value):
        self._div_rect.pos = instance.pos
        self._div_rect.size = instance.size

    def on_press(self):
        self._bg_color.rgba = (
            0.973,
            0.976,
            0.980,
            1
        )

    def on_release(self):
        self._bg_color.rgba = list(WHITE)

        if self._cb:
            self._cb()


# ================================================================
# PROFILE HEADER
# ================================================================

class ProfileHeader(FloatLayout):

    def __init__(
        self,
        title_text,
        on_back=None,
        **kwargs
    ):
        super().__init__(
            size_hint=(1, None),
            height=dp(65),
            **kwargs
        )

        with self.canvas.before:
            Color(*DARK_GREEN)

            self._bg = Rectangle(
                pos=self.pos,
                size=self.size
            )

        self.bind(
            pos=self._sync,
            size=self._sync
        )

        back_btn = BackArrowIcon(
            size_hint=(None, None),
            size=(dp(20), dp(20)),
            pos_hint={
                "x": 0.045,
                "center_y": 0.5
            }
        )

        if on_back:
            back_btn.bind(
                on_release=lambda *_: on_back()
            )

        self.add_widget(back_btn)

        title = Label(
            text=title_text,
            font_size="19sp",
            bold=True,
            color=WHITE,
            size_hint=(None, None),
            size=(dp(220), dp(30)),
            pos_hint={
                "center_x": 0.5,
                "center_y": 0.5
            },
            halign="center",
            valign="middle"
        )

        title.bind(
            size=lambda w, *_:
            setattr(w, "text_size", w.size)
        )

        self.add_widget(title)

    def _sync(self, *_):
        self._bg.pos = self.pos
        self._bg.size = self.size


# ================================================================
# STAFF BOTTOM NAVIGATION
# ================================================================

class StaffBottomNav(BoxLayout):

    def __init__(
        self,
        on_nav=None,
        active_index=3,
        **kwargs
    ):
        super().__init__(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(65),
            **kwargs
        )

        self._on_nav = on_nav

        with self.canvas.before:
            Color(*DARK_GREEN)

            self._bg = Rectangle(
                pos=self.pos,
                size=self.size
            )

        self.bind(
            pos=self._sync,
            size=self._sync
        )

        icon_factories = [
            NavHomeIcon,
            NavPinIcon,
            NavClockIcon,
            NavPersonIcon,
        ]

        self.buttons = []

        for i, factory in enumerate(icon_factories):
            cell = _NavButton(
                factory,
                active=(i == active_index)
            )

            cell.bind(
                on_release=lambda inst, idx=i:
                self._fire(idx)
            )

            self.add_widget(cell)
            self.buttons.append(cell)

    def _fire(self, idx):
        if self._on_nav:
            self._on_nav(idx)

    def _sync(self, *_):
        self._bg.pos = self.pos
        self._bg.size = self.size


# ================================================================
# NAVIGATION BUTTON
# ================================================================

class _NavButton(ButtonBehavior, AnchorLayout):

    def __init__(
        self,
        icon_factory,
        active=False,
        **kwargs
    ):
        super().__init__(**kwargs)

        self._icon = icon_factory(
            size_hint=(None, None),
            size=(dp(22), dp(22))
        )

        self.add_widget(self._icon)

        self.set_active(active)

    def set_active(self, active):
        self._icon.color = (
            list(WHITE)
            if active
            else list(NAV_INACTIVE)
        )


# ================================================================
# STAFF PROFILE SCREEN
# ================================================================

class StaffProfileScreen(Screen):

    NAV_ROUTES = {
        0: "staff_dashboard",
        1: "staff_route",

        # FIX:
        # Main.py registers this screen as
        # "staff_task_history", not "task_history".
        2: "staff_task_history",

        3: "staff_profile",
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        root = BoxLayout(
            orientation="vertical"
        )

        with root.canvas.before:
            Color(*BG)

            self._root_bg = Rectangle(
                pos=root.pos,
                size=root.size
            )

        root.bind(
            pos=lambda w, *_:
            setattr(self._root_bg, "pos", w.pos),

            size=lambda w, *_:
            setattr(self._root_bg, "size", w.size),
        )

        # --------------------------------------------------------
        # HEADER
        # --------------------------------------------------------

        root.add_widget(
            ProfileHeader(
                "Profile",
                on_back=self._go_back
            )
        )

        # --------------------------------------------------------
        # HERO / AVATAR + FIREBASE STAFF NAME
        # --------------------------------------------------------

        hero = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            height=dp(220),
            padding=(
                0,
                dp(24),
                0,
                dp(16)
            ),
            spacing=dp(12)
        )

        avatar_anchor = AnchorLayout(
            anchor_x="center",
            size_hint_y=None,
            height=dp(120)
        )

        avatar_anchor.add_widget(
            AvatarWidget(
                size_hint=(None, None),
                size=(dp(120), dp(120))
            )
        )

        self.name_lbl = Label(
            text="Staff",
            color=list(TEXT_DARK),
            font_size=sp(20),
            bold=True,
            size_hint_y=None,
            height=dp(30)
        )

        hero.add_widget(avatar_anchor)
        hero.add_widget(self.name_lbl)

        root.add_widget(hero)

        # --------------------------------------------------------
        # PROFILE OPTIONS
        # --------------------------------------------------------

        options = BoxLayout(
            orientation="vertical",
            padding=(
                dp(20),
                dp(8)
            ),
            size_hint_y=None
        )

        options.bind(
            minimum_height=options.setter("height")
        )

        # Edit Profile
        options.add_widget(
            ProfileRow(
                lambda: CheckIcon(
                    size_hint=(None, None),
                    size=(dp(20), dp(20))
                ),
                "Edit Profile",
                on_press_cb=self._edit_profile,
            )
        )

        # Change Password
        options.add_widget(
            ProfileRow(
                lambda: LockIcon(
                    size_hint=(None, None),
                    size=(dp(20), dp(20))
                ),
                "Change Password",
                on_press_cb=self._change_password,
            )
        )

        # Notification Settings
        options.add_widget(
            ProfileRow(
                lambda: BellIcon(
                    size_hint=(None, None),
                    size=(dp(20), dp(20))
                ),
                "Notification Settings",
                on_press_cb=self._notif_settings,
            )
        )

        # Logout
        options.add_widget(
            ProfileRow(
                lambda: LogoutIcon(
                    size_hint=(None, None),
                    size=(dp(20), dp(20))
                ),
                "Logout",
                on_press_cb=self._logout,
            )
        )

        list_area = BoxLayout(
            orientation="vertical"
        )

        list_area.add_widget(options)
        list_area.add_widget(Widget())

        root.add_widget(list_area)

        # --------------------------------------------------------
        # BOTTOM NAVIGATION
        # --------------------------------------------------------

        nav = StaffBottomNav(
            on_nav=self._on_nav,
            active_index=3
        )

        root.add_widget(nav)

        self.add_widget(root)

    # ============================================================
    # FIREBASE PROFILE
    # ============================================================

    def on_enter(self, *args):
        self._load_staff_profile()

    def _load_staff_profile(self):
        """Load current logged-in staff profile from Firebase."""

        if get_current_user is None or get_data is None:
            print("Firebase profile service unavailable.")
            return

        try:
            user = get_current_user()

            if not user:
                print("No logged-in Firebase user.")
                self.name_lbl.text = "Staff"
                return

            uid = user.get("localId")

            if not uid:
                print("Firebase UID not found.")
                self.name_lbl.text = "Staff"
                return

            success, data = get_data(
                f"staff/{uid}"
            )

            if not success or not data:
                print(
                    "Staff profile not found:",
                    data
                )

                self.name_lbl.text = "Staff"
                return

            name = data.get(
                "full_name",
                "Staff"
            )

            self.name_lbl.text = name

            print(
                "Staff profile loaded successfully."
            )

            print(
                "Name:",
                name
            )

            print(
                "Staff ID:",
                data.get(
                    "staff_id",
                    ""
                )
            )

            print(
                "Email:",
                data.get(
                    "email",
                    user.get(
                        "email",
                        ""
                    )
                )
            )

        except Exception as e:
            print(
                "Profile Firebase Error:",
                e
            )

            self.name_lbl.text = "Staff"

    # ============================================================
    # NAVIGATION
    # ============================================================

    def _on_nav(self, index):
        target = self.NAV_ROUTES.get(index)

        if target is None or target == self.name:
            return

        if self.manager is None:
            print(
                f"Navigation item [{index}] tapped, "
                f"but screen has no manager yet."
            )
            return

        if target not in self.manager.screen_names:
            print(
                f"Navigation item [{index}] tapped -> "
                f"'{target}' is not registered in "
                f"main.py's ScreenManager yet."
            )
            return

        self.manager.current = target

    def _go_back(self):
        self._on_nav(0)

    # ============================================================
    # LIST ROW ACTIONS
    # ============================================================

    def _edit_profile(self):
        """Open the Firebase-connected Edit Profile screen."""

        if (
            self.manager
            and "edit_profile" in self.manager.screen_names
        ):
            self.manager.current = "edit_profile"
        else:
            print(
                "Edit Profile screen is not registered "
                "in main.py."
            )

    def _notif_settings(self):
        """
        Open Staff Notification Settings screen.
        """

        if (
            self.manager
            and "staff_notification_settings"
            in self.manager.screen_names
        ):
            self.manager.current = (
                "staff_notification_settings"
            )
        else:
            print(
                "Notification Settings screen is not "
                "registered in main.py."
            )

    def _change_password(self):
        if (
            self.manager
            and "staff_reset_password"
            in self.manager.screen_names
        ):
            self.manager.current = (
                "staff_reset_password"
            )
        else:
            print(
                "Routing to Change Password... "
                "('staff_reset_password' not registered yet)"
            )

    def _logout(self):
        """Logout from Firebase, then return to role selection."""

        try:
            if logout_user is not None:
                logout_user()
                print(
                    "Firebase logout successful."
                )
            else:
                print(
                    "Firebase logout service unavailable."
                )

        except Exception as e:
            print(
                "Logout Error:",
                e
            )

        if (
            self.manager
            and "role_selection"
            in self.manager.screen_names
        ):
            self.manager.current = "role_selection"
        else:
            print(
                "Role selection screen not registered."
            )