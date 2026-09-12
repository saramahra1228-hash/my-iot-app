"""
Admin Edit Profile Screen — Smart Waste Monitor
------------------------------------------------------------

Dedicated Edit Profile screen for ADMIN only.

Firebase:
    admin/<uid>
    OR
    admins/<uid>

Editable:
    - Full Name
    - Phone

Read-only:
    - Admin ID
    - Email

Back:
    -> admin_profile
"""

from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.widget import Widget

from kivy.graphics import Color, Rectangle
from kivy.metrics import dp, sp
from kivy.clock import Clock


# =========================================================
# FIREBASE
# =========================================================

try:
    from firebase_auth import get_current_user
except ImportError:
    get_current_user = None

try:
    from firebase_config import get_data, update_data
except ImportError:
    get_data = None
    update_data = None


# =========================================================
# COLORS
# =========================================================

DARK_GREEN = (
    0 / 255,
    77 / 255,
    52 / 255,
    1,
)

WHITE = (1, 1, 1, 1)

BG = (1, 1, 1, 1)

TEXT_DARK = (
    51 / 255,
    51 / 255,
    51 / 255,
    1,
)

GREEN = (
    46 / 255,
    125 / 255,
    50 / 255,
    1,
)

RED = (
    211 / 255,
    47 / 255,
    47 / 255,
    1,
)

GRAY_TEXT = (
    110 / 255,
    110 / 255,
    110 / 255,
    1,
)


# =========================================================
# ADMIN EDIT PROFILE SCREEN
# =========================================================

class AdminEditProfileScreen(Screen):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Firebase profile path actually found
        self.firebase_profile_path = None

        # -------------------------------------------------
        # ROOT
        # -------------------------------------------------

        root = BoxLayout(
            orientation="vertical"
        )

        # Background
        with root.canvas.before:
            Color(*BG)

            self.bg_rect = Rectangle(
                pos=root.pos,
                size=root.size
            )

        root.bind(
            pos=lambda w, *_: setattr(
                self.bg_rect,
                "pos",
                w.pos
            ),

            size=lambda w, *_: setattr(
                self.bg_rect,
                "size",
                w.size
            ),
        )

        # =================================================
        # HEADER
        # =================================================

        header = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(65),
            padding=(dp(16), 0),
        )

        with header.canvas.before:
            Color(*DARK_GREEN)

            self.header_bg = Rectangle(
                pos=header.pos,
                size=header.size
            )

        header.bind(
            pos=lambda w, *_: setattr(
                self.header_bg,
                "pos",
                w.pos
            ),

            size=lambda w, *_: setattr(
                self.header_bg,
                "size",
                w.size
            ),
        )

        # -------------------------------------------------
        # BACK BUTTON
        # -------------------------------------------------

        back_btn = Button(
            text="‹",
            font_size=sp(34),
            color=list(WHITE),
            background_normal="",
            background_color=(0, 0, 0, 0),
            size_hint_x=None,
            width=dp(45),
        )

        back_btn.bind(
            on_release=self._go_back
        )

        # -------------------------------------------------
        # TITLE
        # -------------------------------------------------
        # Slightly lower inside the header to avoid
        # overlapping with the content heading below.

        title = Label(
            text="Edit Profile",
            font_size=sp(19),
            bold=True,
            color=list(WHITE),
            halign="center",
            valign="middle",
            size_hint_y=None,
            height=dp(65),
            padding_y=dp(5),
        )

        title.bind(
            size=lambda w, *_: setattr(
                w,
                "text_size",
                w.size
            )
        )

        header.add_widget(back_btn)
        header.add_widget(title)

        # Right-side spacing
        header.add_widget(
            Widget(
                size_hint_x=None,
                width=dp(45)
            )
        )

        root.add_widget(header)

        # =================================================
        # CONTENT
        # =================================================

        content = BoxLayout(
            orientation="vertical",
            padding=(
                dp(24),
                dp(24)
            ),
            spacing=dp(8),
        )

        # -------------------------------------------------
        # HEADING
        # -------------------------------------------------

        heading = Label(
            text="Update your admin profile",
            color=(
                0.55,
                0.55,
                0.55,
                1
            ),
            font_size=sp(17),
            bold=True,
            size_hint_y=None,
            height=dp(35),
            halign="center",
            valign="middle",
        )

        # Keep the heading centered and vertically aligned.
        heading.bind(
            size=lambda w, *_: setattr(
                w,
                "text_size",
                w.size
            )
        )

        content.add_widget(heading)

        # -------------------------------------------------
        # SUBTITLE
        # -------------------------------------------------

        subtitle = Label(
            text="Change your personal information below.",
            color=list(GRAY_TEXT),
            font_size=sp(13),
            size_hint_y=None,
            height=dp(28),
            halign="left",
            valign="middle",
            padding_y=dp(3),
        )

        # Move subtitle slightly upward / align it properly.
        subtitle.bind(
            size=lambda w, *_: setattr(
                w,
                "text_size",
                w.size
            )
        )

        content.add_widget(subtitle)

        content.add_widget(
            Widget(
                size_hint_y=None,
                height=dp(12)
            )
        )

        # =================================================
        # FULL NAME
        # =================================================

        content.add_widget(
            self._make_label("Full Name")
        )

        self.full_name = self._make_input(
            "Full Name"
        )

        content.add_widget(
            self.full_name
        )

        content.add_widget(
            Widget(
                size_hint_y=None,
                height=dp(12)
            )
        )

        # =================================================
        # PHONE
        # =================================================

        content.add_widget(
            self._make_label("Phone")
        )

        self.phone = self._make_input(
            "Phone Number"
        )

        content.add_widget(
            self.phone
        )

        content.add_widget(
            Widget(
                size_hint_y=None,
                height=dp(12)
            )
        )

        # =================================================
        # ADMIN ID
        # =================================================

        content.add_widget(
            self._make_label("Admin ID")
        )

        self.admin_id = self._make_input(
            "Admin ID"
        )

        self.admin_id.readonly = True

        self.admin_id.background_color = (
            0.94,
            0.94,
            0.94,
            1
        )

        content.add_widget(
            self.admin_id
        )

        content.add_widget(
            Widget(
                size_hint_y=None,
                height=dp(12)
            )
        )

        # =================================================
        # EMAIL
        # =================================================

        content.add_widget(
            self._make_label("Email")
        )

        self.email = self._make_input(
            "Email"
        )

        self.email.readonly = True

        self.email.background_color = (
            0.94,
            0.94,
            0.94,
            1
        )

        content.add_widget(
            self.email
        )

        content.add_widget(
            Widget(
                size_hint_y=None,
                height=dp(18)
            )
        )

        # =================================================
        # STATUS
        # =================================================

        self.status_lbl = Label(
            text="",
            color=list(RED),
            font_size=sp(13),
            size_hint_y=None,
            height=dp(30),
            halign="center",
            valign="middle",
        )

        self.status_lbl.bind(
            size=lambda w, *_: setattr(
                w,
                "text_size",
                w.size
            )
        )

        content.add_widget(
            self.status_lbl
        )

        # =================================================
        # SAVE BUTTON
        # =================================================

        save_btn = Button(
            text="Save Changes",
            font_size=sp(15),
            bold=True,
            color=list(WHITE),
            background_normal="",
            background_color=list(DARK_GREEN),
            size_hint_y=None,
            height=dp(50),
        )

        save_btn.bind(
            on_release=self._save_profile
        )

        content.add_widget(save_btn)

        # Add content
        root.add_widget(content)

        # Add root to screen
        self.add_widget(root)

    # =====================================================
    # INPUT HELPERS
    # =====================================================

    def _make_label(self, text):

        lbl = Label(
            text=text,
            color=list(TEXT_DARK),
            font_size=sp(13),
            bold=True,
            size_hint_y=None,
            height=dp(25),
            halign="left",
        )

        lbl.bind(
            size=lambda w, *_: setattr(
                w,
                "text_size",
                w.size
            )
        )

        return lbl

    def _make_input(self, hint):

        return TextInput(
            hint_text=hint,
            font_size=sp(14),
            multiline=False,
            padding=(
                dp(12),
                dp(12)
            ),
            size_hint_y=None,
            height=dp(46),
            background_normal="",
            background_active="",
            background_color=list(WHITE),
            foreground_color=list(TEXT_DARK),
            hint_text_color=(
                0.55,
                0.55,
                0.55,
                1
            ),
            cursor_color=list(DARK_GREEN),
        )

    # =====================================================
    # SCREEN ENTER
    # =====================================================

    def on_enter(self, *args):

        self._load_admin_profile()

    # =====================================================
    # LOAD ADMIN PROFILE
    # =====================================================

    def _load_admin_profile(self):

        self.status_lbl.text = ""
        self.status_lbl.color = list(RED)

        self.firebase_profile_path = None

        if (
            get_current_user is None
            or get_data is None
        ):

            self.status_lbl.text = (
                "Firebase service unavailable."
            )

            return

        try:

            user = get_current_user()

            if not user:

                self.status_lbl.text = (
                    "Please login again."
                )

                return

            uid = user.get("localId")

            if not uid:
                uid = user.get("uid")

            if not uid:

                self.status_lbl.text = (
                    "Firebase user ID not found."
                )

                return

            candidate_paths = [
                f"admin/{uid}",
                f"admins/{uid}",
            ]

            profile_found = False

            for path in candidate_paths:

                try:
                    success, data = get_data(path)

                except Exception as e:

                    print(
                        f"Firebase read error "
                        f"for {path}:",
                        e
                    )

                    continue

                if (
                    success
                    and isinstance(data, dict)
                ):

                    self.firebase_profile_path = path

                    self._fill_admin_profile(
                        data,
                        user,
                        uid
                    )

                    profile_found = True

                    print(
                        "Admin Edit Profile: "
                        f"Loaded from {path}"
                    )

                    break

            if not profile_found:

                self.status_lbl.text = (
                    "Admin profile not found."
                )

                return

        except Exception as e:

            print(
                "Admin Edit Profile Load Error:",
                e
            )

            self.status_lbl.text = (
                "Unable to load profile."
            )

    # =====================================================
    # FILL ADMIN PROFILE
    # =====================================================

    def _fill_admin_profile(
        self,
        data,
        user,
        uid
    ):

        full_name = (
            data.get("full_name")
            or data.get("name")
            or data.get("fullName")
            or data.get("display_name")
            or data.get("displayName")
            or ""
        )

        self.full_name.text = str(
            full_name
        )

        phone = (
            data.get("phone")
            or data.get("phone_number")
            or data.get("phoneNumber")
            or ""
        )

        self.phone.text = str(
            phone
        )

        admin_id = (
            data.get("admin_id")
            or data.get("adminId")
            or data.get("id")
            or data.get("user_id")
            or data.get("userId")
            or uid
        )

        self.admin_id.text = str(
            admin_id
        )

        email = (
            data.get("email")
            or user.get("email")
            or ""
        )

        self.email.text = str(
            email
        )

    # =====================================================
    # SAVE ADMIN PROFILE
    # =====================================================

    def _save_profile(self, *_):

        full_name = (
            self.full_name.text.strip()
        )

        phone = (
            self.phone.text.strip()
        )

        if not full_name:

            self.status_lbl.text = (
                "Full Name is required."
            )

            self.status_lbl.color = list(
                RED
            )

            return

        if not phone:

            self.status_lbl.text = (
                "Phone number is required."
            )

            self.status_lbl.color = list(
                RED
            )

            return

        if (
            get_current_user is None
            or update_data is None
        ):

            self.status_lbl.text = (
                "Firebase service unavailable."
            )

            self.status_lbl.color = list(
                RED
            )

            return

        try:

            user = get_current_user()

            if not user:

                self.status_lbl.text = (
                    "Please login again."
                )

                self.status_lbl.color = list(
                    RED
                )

                return

            uid = user.get("localId")

            if not uid:
                uid = user.get("uid")

            if not uid:

                self.status_lbl.text = (
                    "Firebase user ID not found."
                )

                self.status_lbl.color = list(
                    RED
                )

                return

            if self.firebase_profile_path:

                profile_path = (
                    self.firebase_profile_path
                )

            else:

                profile_path = (
                    f"admin/{uid}"
                )

            updates = {
                "full_name": full_name,
                "phone": phone,
            }

            success, result = update_data(
                profile_path,
                updates
            )

            if success:

                self.full_name.text = full_name
                self.phone.text = phone

                self.status_lbl.text = (
                    "Profile updated successfully!"
                )

                self.status_lbl.color = list(
                    GREEN
                )

                print(
                    "Admin profile updated:",
                    profile_path,
                    updates
                )

                Clock.schedule_once(
                    lambda dt:
                    self._go_back_after_save(),
                    0.8
                )

            else:

                if result:

                    self.status_lbl.text = str(
                        result
                    )

                else:

                    self.status_lbl.text = (
                        "Unable to update profile."
                    )

                self.status_lbl.color = list(
                    RED
                )

        except Exception as e:

            print(
                "Admin Edit Profile Save Error:",
                e
            )

            self.status_lbl.text = (
                "Unable to save profile."
            )

            self.status_lbl.color = list(
                RED
            )

    # =====================================================
    # NAVIGATION
    # =====================================================

    def _go_back(self, *_):

        self._return_to_admin_profile()

    def _go_back_after_save(self):

        self._return_to_admin_profile()

    def _return_to_admin_profile(self):

        if not self.manager:
            return

        if (
            "admin_profile"
            in self.manager.screen_names
        ):

            self.manager.current = (
                "admin_profile"
            )

            return

        print(
            "admin_profile screen not registered."
        )


# =========================================================
# TEST
# =========================================================

if __name__ == "__main__":
    pass
