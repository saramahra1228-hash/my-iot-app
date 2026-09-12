"""
Admin Profile Screen — Smart Waste Monitor
--------------------------------------------------------------------
Firebase-connected version of the original Premium Admin Profile UI.

The original UI/design is preserved.

Firebase FIX:
    - Reads the currently logged-in Firebase user.
    - Reads admin/{uid} or admins/{uid}.
    - If no database profile exists, automatically creates
      admin/{uid} using the authenticated user's UID/email.
    - Uses the existing Admin name label; no UI redesign.
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
# Firebase
# ================================================================

try:
    from firebase_auth import get_current_user
except Exception:
    get_current_user = None

try:
    from firebase_config import get_data, set_data
except Exception:
    get_data = None
    set_data = None


# ================================================================
# Shared app components
# ================================================================

from admin_dashboard_kivy import (
    VectorIcon,
    BottomNav,
    BG,
    DARK_GREEN,
    WHITE,
    TEXT_DARK,
    RED_FG,
)


# ================================================================
# Extra colours
# ================================================================

LIGHT_GRAY = (
    234 / 255,
    234 / 255,
    234 / 255,
    1,
)

SILHOUETTE = (
    52 / 255,
    73 / 255,
    94 / 255,
    1,
)

EDIT_GREEN = (
    46 / 255,
    125 / 255,
    50 / 255,
    1,
)


# ================================================================
# Back Arrow
# ================================================================

class BackArrowIcon(ButtonBehavior, Widget):

    color = ListProperty(list(WHITE))

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(
            pos=self.redraw,
            size=self.redraw,
            color=self.redraw,
        )
        self.redraw()

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
                    oy + 0.50 * s,
                    ox + 0.68 * s,
                    oy + 0.85 * s,
                ],
                width=dp(1.5),
                cap="round",
                joint="round",
            )


# ================================================================
# Check Icon
# ================================================================

class CheckIcon(Widget):

    color = ListProperty(list(EDIT_GREEN))

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(
            pos=self.redraw,
            size=self.redraw,
            color=self.redraw,
        )
        self.redraw()

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
# Lock Icon
# ================================================================

class LockIcon(Widget):

    color = ListProperty(list(TEXT_DARK))

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(
            pos=self.redraw,
            size=self.redraw,
            color=self.redraw,
        )
        self.redraw()

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
# Logout Icon
# ================================================================

class LogoutIcon(Widget):

    color = ListProperty(list(RED_FG))

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(
            pos=self.redraw,
            size=self.redraw,
            color=self.redraw,
        )
        self.redraw()

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
                    oy + 0.50 * s,
                    ox + 0.86 * s,
                    oy + 0.50 * s,
                ],
                width=dp(1.6),
                cap="round",
            )

            Line(
                points=[
                    ox + 0.68 * s,
                    oy + 0.32 * s,
                    ox + 0.88 * s,
                    oy + 0.50 * s,
                    ox + 0.68 * s,
                    oy + 0.68 * s,
                ],
                width=dp(1.6),
                cap="round",
                joint="round",
            )


# ================================================================
# Avatar
# ================================================================

class AvatarWidget(Widget):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.bind(
            pos=self._redraw,
            size=self._redraw,
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
                size=(w, h),
            )

            StencilPush()

            Color(1, 1, 1, 1)

            Ellipse(
                pos=(x, y),
                size=(w, h),
            )

            StencilUse()

            Color(*SILHOUETTE)

            Ellipse(
                pos=(
                    x + w * 0.33,
                    y + h * 0.54,
                ),
                size=(
                    w * 0.34,
                    w * 0.34,
                ),
            )

            Ellipse(
                pos=(
                    x + w * 0.04,
                    y - h * 0.30,
                ),
                size=(
                    w * 0.92,
                    h * 0.85,
                ),
            )

            StencilUnUse()

            Color(1, 1, 1, 1)

            Ellipse(
                pos=(x, y),
                size=(w, h),
            )

            StencilPop()


# ================================================================
# Profile Row
# ================================================================

class ProfileRow(ButtonBehavior, BoxLayout):

    def __init__(
        self,
        icon_widget_factory,
        label_text,
        on_press_cb=None,
        **kwargs,
    ):

        super().__init__(
            orientation="vertical",
            size_hint_y=None,
            height=dp(52),
            **kwargs,
        )

        self.label_text = label_text
        self._cb = on_press_cb

        with self.canvas.before:

            self._bg_color = Color(*WHITE)

            self._bg_rect = Rectangle(
                pos=self.pos,
                size=self.size,
            )

        self.bind(
            pos=self._update_bg,
            size=self._update_bg,
        )

        row = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(44),
            padding=(dp(8), 0),
            spacing=dp(14),
        )

        icon_box = AnchorLayout(
            size_hint_x=None,
            width=dp(28),
        )

        icon_box.add_widget(
            icon_widget_factory()
        )

        text_lbl = Label(
            text=label_text,
            color=list(TEXT_DARK),
            font_size=sp(14),
            halign="left",
            valign="middle",
        )

        text_lbl.bind(
            size=lambda inst, val:
            setattr(
                inst,
                "text_size",
                val,
            )
        )

        row.add_widget(icon_box)
        row.add_widget(text_lbl)

        self.add_widget(row)

        divider = Widget(
            size_hint_y=None,
            height=dp(1),
        )

        with divider.canvas:

            Color(*LIGHT_GRAY)

            self._div_rect = Rectangle(
                pos=divider.pos,
                size=divider.size,
            )

        divider.bind(
            pos=self._update_divider,
            size=self._update_divider,
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
            1,
        )

    def on_release(self):

        self._bg_color.rgba = list(WHITE)

        if self._cb:
            self._cb()


# ================================================================
# Profile Header
# ================================================================

class ProfileHeader(FloatLayout):

    def __init__(
        self,
        title_text,
        on_back=None,
        **kwargs,
    ):

        super().__init__(
            size_hint=(1, None),
            height=dp(65),
            **kwargs,
        )

        with self.canvas.before:

            Color(*DARK_GREEN)

            self._bg = Rectangle(
                pos=self.pos,
                size=self.size,
            )

        self.bind(
            pos=self._sync,
            size=self._sync,
        )

        back_btn = BackArrowIcon(
            size_hint=(None, None),
            size=(dp(20), dp(20)),
            pos_hint={
                "x": 0.045,
                "center_y": 0.5,
            },
        )

        if on_back:

            back_btn.bind(
                on_release=lambda *_:
                on_back()
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
                "center_y": 0.5,
            },
            halign="center",
            valign="middle",
        )

        title.bind(
            size=lambda w, *_:
            setattr(
                w,
                "text_size",
                w.size,
            )
        )

        self.add_widget(title)

    def _sync(self, *_):

        self._bg.pos = self.pos
        self._bg.size = self.size


# ================================================================
# ADMIN PROFILE SCREEN
# ================================================================

class AdminProfileScreen(Screen):

    NAV_ROUTES = {
        0: "admin_dashboard",
        1: "admin_map",
        2: "admin_panel",
        3: "admin_profile",
    }

    def __init__(self, **kwargs):

        super().__init__(**kwargs)

        self.firebase_uid = ""
        self.firebase_email = ""
        self.firebase_profile = None

        root = BoxLayout(
            orientation="vertical"
        )

        with root.canvas.before:

            Color(*BG)

            self._root_bg = Rectangle(
                pos=root.pos,
                size=root.size,
            )

        root.bind(
            pos=lambda w, *_:
            setattr(
                self._root_bg,
                "pos",
                w.pos,
            ),

            size=lambda w, *_:
            setattr(
                self._root_bg,
                "size",
                w.size,
            ),
        )

        root.add_widget(
            ProfileHeader(
                "Profile",
                on_back=self._go_back,
            )
        )

        hero = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            height=dp(220),
            padding=(
                0,
                dp(24),
                0,
                dp(16),
            ),
            spacing=dp(12),
        )

        avatar_anchor = AnchorLayout(
            anchor_x="center",
            size_hint_y=None,
            height=dp(120),
        )

        avatar_anchor.add_widget(
            AvatarWidget(
                size_hint=(None, None),
                size=(dp(120), dp(120)),
            )
        )

        self.name_lbl = Label(
            text="Admin",
            color=list(TEXT_DARK),
            font_size=sp(20),
            bold=True,
            size_hint_y=None,
            height=dp(30),
        )

        hero.add_widget(avatar_anchor)
        hero.add_widget(self.name_lbl)

        root.add_widget(hero)

        options = BoxLayout(
            orientation="vertical",
            padding=(
                dp(20),
                dp(8),
            ),
            size_hint_y=None,
        )

        options.bind(
            minimum_height=options.setter(
                "height"
            )
        )

        options.add_widget(
            ProfileRow(
                lambda:
                CheckIcon(
                    size_hint=(None, None),
                    size=(dp(20), dp(20)),
                ),
                "Edit Profile",
                on_press_cb=self._go_edit_profile,
            )
        )

        options.add_widget(
            ProfileRow(
                lambda:
                LockIcon(
                    size_hint=(None, None),
                    size=(dp(20), dp(20)),
                ),
                "Change Password",
                on_press_cb=self._go_change_password,
            )
        )

        options.add_widget(
            ProfileRow(
                lambda:
                VectorIcon(
                    icon_name="bell",
                    icon_color=list(TEXT_DARK),
                    line_width=dp(1.5),
                    size_hint=(None, None),
                    size=(dp(20), dp(20)),
                ),
                "Notification Settings",
                on_press_cb=self._go_notifications,
            )
        )

        options.add_widget(
            ProfileRow(
                lambda:
                LogoutIcon(
                    size_hint=(None, None),
                    size=(dp(20), dp(20)),
                ),
                "Logout",
                on_press_cb=self._go_logout,
            )
        )

        list_area = BoxLayout(
            orientation="vertical"
        )

        list_area.add_widget(options)
        list_area.add_widget(Widget())

        root.add_widget(list_area)

        nav = BottomNav(
            on_nav=self._on_nav
        )

        for i, btn in enumerate(nav.buttons):
            btn.set_active(i == 3)

        root.add_widget(nav)

        self.add_widget(root)

    # ============================================================
    # SCREEN ENTER
    # ============================================================

    def on_pre_enter(self, *args):
        self._load_firebase_profile()

    # ============================================================
    # FIREBASE
    # ============================================================

    def _make_default_name(self, email):

        email = str(email or "").strip()

        if not email:
            return "Admin"

        name = email.split("@", 1)[0].strip()

        if not name:
            return "Admin"

        return (
            name
            .replace(".", " ")
            .replace("_", " ")
            .replace("-", " ")
            .title()
        )

    def _load_firebase_profile(self):

        if get_current_user is None:

            print(
                "[ADMIN PROFILE] "
                "get_current_user is not available."
            )

            self.name_lbl.text = "Admin"
            return

        try:

            user = get_current_user()

            if isinstance(user, tuple):

                if len(user) >= 2:

                    success = user[0]
                    user_data = user[1]

                    if not success:

                        print(
                            "[ADMIN PROFILE] "
                            "No logged-in Firebase user."
                        )

                        self.name_lbl.text = "Admin"
                        return

                    user = user_data

                else:

                    self.name_lbl.text = "Admin"
                    return

            if user is None:

                print(
                    "[ADMIN PROFILE] "
                    "No logged-in Firebase user."
                )

                self.name_lbl.text = "Admin"
                return

            uid = ""
            email = ""

            if isinstance(user, dict):

                uid = (
                    user.get("uid")
                    or user.get("localId")
                    or user.get("id")
                    or ""
                )

                email = user.get("email") or ""

            else:

                uid = (
                    getattr(user, "uid", "")
                    or getattr(user, "localId", "")
                    or getattr(user, "id", "")
                    or ""
                )

                email = getattr(
                    user,
                    "email",
                    "",
                )

            self.firebase_uid = str(uid or "")
            self.firebase_email = str(email or "")

            print(
                "[ADMIN PROFILE] "
                f"Logged-in UID: {self.firebase_uid}"
            )

            print(
                "[ADMIN PROFILE] "
                f"Logged-in email: {self.firebase_email}"
            )

            if not self.firebase_uid:

                print(
                    "[ADMIN PROFILE] "
                    "Firebase user has no UID."
                )

                self.name_lbl.text = "Admin"
                return

            profile_data = None
            profile_path = None

            if get_data is not None:

                possible_paths = [
                    f"admin/{self.firebase_uid}",
                    f"admins/{self.firebase_uid}",
                ]

                for path in possible_paths:

                    try:

                        result = get_data(path)

                        if (
                            isinstance(result, tuple)
                            and len(result) >= 2
                        ):

                            success = result[0]
                            data = result[1]

                            if not success:

                                print(
                                    "[ADMIN PROFILE] "
                                    f"Could not read {path}: {data}"
                                )

                                continue

                            profile_data = data

                        else:

                            profile_data = result

                        if isinstance(
                            profile_data,
                            dict
                        ):

                            profile_path = path

                            print(
                                "[ADMIN PROFILE] "
                                f"Loaded profile from {path}"
                            )

                            break

                    except Exception as exc:

                        print(
                            "[ADMIN PROFILE] "
                            f"Firebase read error "
                            f"{path}: {exc}"
                        )

            # ====================================================
            # MAIN FIX:
            # AUTH USER EXISTS BUT DB PROFILE DOES NOT.
            # CREATE A DEFAULT PROFILE AUTOMATICALLY.
            # ====================================================

            if not isinstance(profile_data, dict):

                default_name = self._make_default_name(
                    self.firebase_email
                )

                new_profile = {
                    "admin_id": self.firebase_uid,
                    "email": self.firebase_email,
                    "full_name": default_name,
                    "phone": "",
                    "role": "admin",
                }

                print(
                    "[ADMIN PROFILE] "
                    "No database profile found. "
                    "Creating default admin profile..."
                )

                if set_data is not None:

                    try:

                        save_result = set_data(
                            f"admin/{self.firebase_uid}",
                            new_profile,
                        )

                        save_ok = True
                        save_data = save_result

                        if (
                            isinstance(save_result, tuple)
                            and len(save_result) >= 2
                        ):

                            save_ok = save_result[0]
                            save_data = save_result[1]

                        if save_ok:

                            profile_data = new_profile
                            profile_path = (
                                f"admin/{self.firebase_uid}"
                            )

                            print(
                                "[ADMIN PROFILE] "
                                "Default profile created at "
                                f"{profile_path}"
                            )

                        else:

                            print(
                                "[ADMIN PROFILE] "
                                "Could not create profile: "
                                f"{save_data}"
                            )

                            # Keep local fallback so the UI
                            # still displays the admin name.
                            profile_data = new_profile

                    except Exception as exc:

                        print(
                            "[ADMIN PROFILE] "
                            f"Profile creation error: {exc}"
                        )

                        profile_data = new_profile

                else:

                    print(
                        "[ADMIN PROFILE] "
                        "set_data is not available."
                    )

                    profile_data = new_profile

            self.firebase_profile = profile_data

            admin_name = None

            if isinstance(
                profile_data,
                dict
            ):

                admin_name = (
                    profile_data.get("name")
                    or profile_data.get("full_name")
                    or profile_data.get("fullName")
                    or profile_data.get("display_name")
                    or profile_data.get("displayName")
                    or profile_data.get("admin_name")
                    or profile_data.get("adminName")
                )

            if not admin_name:

                if isinstance(user, dict):

                    admin_name = (
                        user.get("displayName")
                        or user.get("display_name")
                    )

                else:

                    admin_name = (
                        getattr(
                            user,
                            "display_name",
                            None,
                        )
                        or getattr(
                            user,
                            "displayName",
                            None,
                        )
                    )

            if not admin_name:

                admin_name = self._make_default_name(
                    self.firebase_email
                )

            self.name_lbl.text = str(
                admin_name or "Admin"
            )

            print(
                "[ADMIN PROFILE] "
                f"Displayed admin name: {self.name_lbl.text}"
            )

        except Exception as exc:

            print(
                "[ADMIN PROFILE] "
                f"Firebase profile error: {exc}"
            )

            self.name_lbl.text = "Admin"

    # ============================================================
    # NAVIGATION
    # ============================================================

    def _on_nav(self, index):

        target = self.NAV_ROUTES.get(index)

        if target is None:
            return

        if target == self.name:
            return

        if self.manager is None:

            print(
                f"Navigation item [{index}] tapped, "
                "but screen has no manager yet."
            )

            return

        if target not in self.manager.screen_names:

            print(
                f"Navigation item [{index}] tapped -> "
                f"'{target}' is not registered "
                "in main.py's ScreenManager yet."
            )

            return

        self.manager.current = target

    # ============================================================
    # BACK
    # ============================================================

    def _go_back(self):
        self._on_nav(0)

    # ============================================================
    # 1. EDIT PROFILE
    # ============================================================

    def _go_edit_profile(self):

        if self.manager is None:

            print(
                "[ADMIN PROFILE] "
                "ScreenManager is not available."
            )

            return

        possible_names = [
            "admin_edit_profile",
            "edit_profile",
        ]

        for screen_name in possible_names:

            if screen_name in self.manager.screen_names:

                print(
                    "[ADMIN PROFILE] "
                    f"Opening {screen_name}"
                )

                self.manager.current = screen_name
                return

        print(
            "[ADMIN PROFILE] ERROR: "
            "Edit Profile screen is not registered."
        )

        print(
            "[ADMIN PROFILE] Expected one of:"
        )

        print("    admin_edit_profile")
        print("    edit_profile")

    # ============================================================
    # 2. CHANGE PASSWORD
    # ============================================================

    def _go_change_password(self):

        if self.manager is None:

            print(
                "[ADMIN PROFILE] "
                "ScreenManager is not available."
            )

            return

        possible_names = [
            "reset_password",
            "change_password",
            "admin_change_password",
        ]

        for screen_name in possible_names:

            if screen_name in self.manager.screen_names:

                print(
                    "[ADMIN PROFILE] "
                    f"Opening {screen_name}"
                )

                self.manager.current = screen_name
                return

        print(
            "[ADMIN PROFILE] ERROR: "
            "Change Password screen is not registered."
        )

        print(
            "[ADMIN PROFILE] Expected screen name:"
        )

        print("    reset_password")

    # ============================================================
    # 3. NOTIFICATION SETTINGS
    # ============================================================

    def _go_notifications(self):

        if self.manager is None:

            print(
                "[ADMIN PROFILE] "
                "ScreenManager is not available."
            )

            return

        possible_names = [
            "admin_notification_settings",
            "notification_settings",
            "admin_notifications",
            "notifications",
        ]

        for screen_name in possible_names:

            if screen_name in self.manager.screen_names:

                print(
                    "[ADMIN PROFILE] "
                    f"Opening {screen_name}"
                )

                self.manager.current = screen_name
                return

        print(
            "[ADMIN PROFILE] ERROR: "
            "Notification Settings screen "
            "is not registered in main.py."
        )

        print(
            "[ADMIN PROFILE] "
            "Expected screen name:"
        )

        print("    admin_notification_settings")

    # ============================================================
    # 4. LOGOUT
    # ============================================================

    def _go_logout(self):

        print(
            "[ADMIN PROFILE] Logging out..."
        )

        try:

            import firebase_auth

            logout_function = None

            # IMPORTANT:
            # firebase_auth.py supplied by the user uses
            # logout_user(), so it is checked FIRST.
            for function_name in [
                "logout_user",
                "logout",
                "sign_out",
                "signout",
                "clear_current_user",
            ]:

                candidate = getattr(
                    firebase_auth,
                    function_name,
                    None,
                )

                if callable(candidate):

                    logout_function = candidate
                    break

            if logout_function is not None:

                try:

                    result = logout_function()

                    print(
                        "[ADMIN PROFILE] "
                        f"Firebase logout result: {result}"
                    )

                except Exception as exc:

                    print(
                        "[ADMIN PROFILE] "
                        f"Firebase logout failed: {exc}"
                    )

            else:

                print(
                    "[ADMIN PROFILE] "
                    "No Firebase logout function "
                    "was found in firebase_auth.py."
                )

        except Exception as exc:

            print(
                "[ADMIN PROFILE] "
                f"Could not import firebase_auth: {exc}"
            )

        self.firebase_uid = ""
        self.firebase_email = ""
        self.firebase_profile = None

        if self.manager is None:
            return

        if "role_selection" in self.manager.screen_names:

            self.manager.current = "role_selection"
            return

        if "admin_login" in self.manager.screen_names:

            self.manager.current = "admin_login"
            return

        print(
            "[ADMIN PROFILE] ERROR: "
            "Neither role_selection nor admin_login "
            "is registered in main.py."
        )
