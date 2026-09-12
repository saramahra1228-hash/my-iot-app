"""
Edit Profile Screen — Smart Waste Monitor
Firebase-connected Kivy screen.

Editable:
- Full Name
- Phone

Read-only:
- Staff ID
- Email

Updates:
    Firebase Realtime Database -> staff/<current_user_uid>
"""

from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.widget import Widget
from kivy.graphics import Color, Rectangle
from kivy.metrics import dp, sp


# ---------------------------------------------------------
# FIREBASE
# ---------------------------------------------------------
try:
    from firebase_auth import get_current_user
    from firebase_config import get_data, update_data

except ImportError:
    get_current_user = None
    get_data = None
    update_data = None


# ---------------------------------------------------------
# COLORS
# ---------------------------------------------------------
DARK_GREEN = (0 / 255, 77 / 255, 52 / 255, 1)
WHITE = (1, 1, 1, 1)
BG = (1, 1, 1, 1)

TEXT_DARK = (
    51 / 255,
    51 / 255,
    51 / 255,
    1
)

LIGHT_GRAY = (
    234 / 255,
    234 / 255,
    234 / 255,
    1
)

GREEN = (
    46 / 255,
    125 / 255,
    50 / 255,
    1
)

RED = (
    211 / 255,
    47 / 255,
    47 / 255,
    1
)

GRAY_TEXT = (
    110 / 255,
    110 / 255,
    110 / 255,
    1
)


# ---------------------------------------------------------
# EDIT PROFILE SCREEN
# ---------------------------------------------------------
class EditProfileScreen(Screen):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # -------------------------------------------------
        # ROOT
        # -------------------------------------------------
        root = BoxLayout(
            orientation="vertical"
        )

        with root.canvas.before:
            Color(*BG)
            self._bg = Rectangle(
                pos=root.pos,
                size=root.size
            )

        root.bind(
            pos=lambda w, *_: setattr(
                self._bg,
                "pos",
                w.pos
            ),
            size=lambda w, *_: setattr(
                self._bg,
                "size",
                w.size
            ),
        )

        # -------------------------------------------------
        # HEADER
        # -------------------------------------------------
        header = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(65),
            padding=(dp(16), 0),
        )

        with header.canvas.before:
            Color(*DARK_GREEN)

            header_bg = Rectangle(
                pos=header.pos,
                size=header.size
            )

        header.bind(
            pos=lambda w, *_: setattr(
                header_bg,
                "pos",
                w.pos
            ),
            size=lambda w, *_: setattr(
                header_bg,
                "size",
                w.size
            ),
        )

        # Back button
        back_btn = Button(
            text="‹",
            font_size=sp(34),
            color=WHITE,
            background_normal="",
            background_color=(0, 0, 0, 0),
            size_hint_x=None,
            width=dp(45),
        )

        back_btn.bind(
            on_release=self._go_back
        )

        # Header title
        title = Label(
            text="Edit Profile",
            font_size=sp(19),
            bold=True,
            color=WHITE,
            halign="center",
            valign="middle",
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

        # -------------------------------------------------
        # CONTENT
        # -------------------------------------------------
        content = BoxLayout(
            orientation="vertical",
            padding=(dp(24), dp(24)),
            spacing=dp(8),
        )

        # -------------------------------------------------
        # PAGE HEADING
        # -------------------------------------------------
        # Changed:
        # - Color = GRAY_TEXT
        # - Alignment = CENTER
        heading = Label(
            text="Update your profile",
            color=list(GRAY_TEXT),
            font_size=sp(20),
            bold=True,
            size_hint_y=None,
            height=dp(35),
            halign="center",
            valign="middle",
        )

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
        sub = Label(
            text="Change your personal information below.",
            color=list(GRAY_TEXT),
            font_size=sp(13),
            size_hint_y=None,
            height=dp(28),
            halign="left",
            valign="middle",
        )

        sub.bind(
            size=lambda w, *_: setattr(
                w,
                "text_size",
                w.size
            )
        )

        content.add_widget(sub)

        content.add_widget(
            Widget(
                size_hint_y=None,
                height=dp(12)
            )
        )

        # -------------------------------------------------
        # FULL NAME
        # -------------------------------------------------
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

        # -------------------------------------------------
        # PHONE
        # -------------------------------------------------
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

        # -------------------------------------------------
        # STAFF ID
        # -------------------------------------------------
        content.add_widget(
            self._make_label("Staff ID")
        )

        self.staff_id = self._make_input(
            "Staff ID"
        )

        self.staff_id.readonly = True

        self.staff_id.background_color = (
            0.94,
            0.94,
            0.94,
            1
        )

        content.add_widget(
            self.staff_id
        )

        content.add_widget(
            Widget(
                size_hint_y=None,
                height=dp(12)
            )
        )

        # -------------------------------------------------
        # EMAIL
        # -------------------------------------------------
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

        # -------------------------------------------------
        # STATUS LABEL
        # -------------------------------------------------
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

        # -------------------------------------------------
        # SAVE BUTTON
        # -------------------------------------------------
        save_btn = Button(
            text="Save Changes",
            font_size=sp(15),
            bold=True,
            color=WHITE,
            background_normal="",
            background_color=list(DARK_GREEN),
            size_hint_y=None,
            height=dp(50),
        )

        save_btn.bind(
            on_release=self._save_profile
        )

        content.add_widget(
            save_btn
        )

        root.add_widget(content)

        self.add_widget(root)

    # =====================================================
    # LABEL
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
            valign="middle",
        )

        lbl.bind(
            size=lambda w, *_: setattr(
                w,
                "text_size",
                w.size
            )
        )

        return lbl

    # =====================================================
    # TEXT INPUT
    # =====================================================
    def _make_input(self, hint):

        return TextInput(
            hint_text=hint,
            font_size=sp(14),
            multiline=False,
            padding=(dp(12), dp(12)),
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
    # FIREBASE
    # =====================================================

    def on_enter(self, *args):
        self._load_profile()

    # -----------------------------------------------------
    # LOAD PROFILE
    # -----------------------------------------------------
    def _load_profile(self):

        self.status_lbl.text = ""

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
                self.status_lbl.text = (
                    "Firebase user ID not found."
                )
                return

            success, data = get_data(
                f"staff/{uid}"
            )

            if not success or not data:
                self.status_lbl.text = (
                    "Staff profile not found."
                )
                return

            self.full_name.text = str(
                data.get(
                    "full_name",
                    ""
                )
            )

            self.phone.text = str(
                data.get(
                    "phone",
                    ""
                )
            )

            self.staff_id.text = str(
                data.get(
                    "staff_id",
                    ""
                )
            )

            self.email.text = str(
                data.get(
                    "email",
                    user.get(
                        "email",
                        ""
                    )
                )
            )

            print(
                "Edit Profile: data loaded."
            )

        except Exception as e:

            print(
                "Edit Profile Load Error:",
                e
            )

            self.status_lbl.text = (
                "Unable to load profile."
            )

    # -----------------------------------------------------
    # SAVE PROFILE
    # -----------------------------------------------------
    def _save_profile(self, *_):

        full_name = (
            self.full_name.text.strip()
        )

        phone = (
            self.phone.text.strip()
        )

        # Required full name
        if not full_name:

            self.status_lbl.text = (
                "Full Name is required."
            )

            self.status_lbl.color = list(
                RED
            )

            return

        # Required phone
        if not phone:

            self.status_lbl.text = (
                "Phone number is required."
            )

            self.status_lbl.color = list(
                RED
            )

            return

        # Firebase check
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

                self.status_lbl.text = (
                    "Firebase user ID not found."
                )

                self.status_lbl.color = list(
                    RED
                )

                return

            # Only editable fields are updated
            updates = {
                "full_name": full_name,
                "phone": phone,
            }

            success, result = update_data(
                f"staff/{uid}",
                updates
            )

            if success:

                self.status_lbl.text = (
                    "Profile updated successfully!"
                )

                self.status_lbl.color = list(
                    GREEN
                )

                print(
                    "Profile updated:",
                    updates
                )

                from kivy.clock import Clock

                Clock.schedule_once(
                    lambda dt:
                    self._go_profile(),
                    0.8
                )

            else:

                self.status_lbl.text = str(
                    result
                )

                self.status_lbl.color = list(
                    RED
                )

        except Exception as e:

            print(
                "Edit Profile Save Error:",
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
        self._go_profile()

    def _go_profile(self):

        if (
            self.manager
            and "staff_profile"
            in self.manager.screen_names
        ):

            self.manager.current = (
                "staff_profile"
            )

        else:

            print(
                "staff_profile screen "
                "not registered."
            )


# ---------------------------------------------------------
# DIRECT RUN
# ---------------------------------------------------------
if __name__ == "__main__":
    pass
