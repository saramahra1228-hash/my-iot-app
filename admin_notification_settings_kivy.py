# admin_notification_settings_kivy.py
# Admin Notification Settings
# Same UI concept as Staff Notification Settings,
# but settings are stored in Firebase for the logged-in admin.

from kivy.app import App
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.switch import Switch
from kivy.uix.button import Button
from kivy.graphics import Color, RoundedRectangle
from kivy.metrics import dp


# ---------------------------------------------------------
# Firebase imports
# ---------------------------------------------------------
try:
    from firebase_auth import get_current_user
except Exception:
    get_current_user = None

try:
    from firebase_config import get_data, set_data
except Exception:
    get_data = None
    set_data = None


# ---------------------------------------------------------
# Colors / UI helpers
# ---------------------------------------------------------
BG_COLOR = (0.96, 0.97, 0.96, 1)
GREEN = (0.0, 0.30, 0.20, 1)
TEXT_COLOR = (0.10, 0.12, 0.11, 1)
SUBTEXT_COLOR = (0.42, 0.45, 0.43, 1)
WHITE = (1, 1, 1, 1)


class RoundedBox(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        with self.canvas.before:
            Color(*WHITE)
            self.bg = RoundedRectangle(
                pos=self.pos,
                size=self.size,
                radius=[dp(14)]
            )

        self.bind(pos=self._update_bg, size=self._update_bg)

    def _update_bg(self, *_):
        self.bg.pos = self.pos
        self.bg.size = self.size


class AdminNotificationSettingsScreen(Screen):

    DEFAULT_SETTINGS = {
        "push_notifications": True,
        "bin_full_alerts": True,
        "task_notifications": True,
        "route_alerts": True,
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.firebase_uid = None
        self.settings_path = None
        self.settings = dict(self.DEFAULT_SETTINGS)
        self._loading = False
        self.switches = {}

        self._build_ui()

    # -----------------------------------------------------
    # UI
    # -----------------------------------------------------
    def _build_ui(self):
        root = BoxLayout(
            orientation="vertical",
            padding=[dp(18), dp(18), dp(18), dp(18)],
            spacing=dp(14)
        )

        with root.canvas.before:
            Color(*BG_COLOR)
            self.bg = RoundedRectangle(
                pos=root.pos,
                size=root.size
            )

        root.bind(
            pos=lambda obj, value: setattr(self.bg, "pos", value),
            size=lambda obj, value: setattr(self.bg, "size", value)
        )

        # Header
        header = BoxLayout(
            size_hint_y=None,
            height=dp(55),
            spacing=dp(8)
        )

        back_btn = Button(
            text="‹",
            font_size=dp(32),
            size_hint_x=None,
            width=dp(45),
            background_normal="",
            background_color=(0, 0, 0, 0),
            color=GREEN
        )
        back_btn.bind(on_release=self._go_back)

        title = Label(
            text="Notification Settings",
            font_size=dp(22),
            bold=True,
            color=TEXT_COLOR,
            halign="left",
            valign="middle"
        )
        title.bind(size=lambda obj, value: setattr(obj, "text_size", value))

        header.add_widget(back_btn)
        header.add_widget(title)

        root.add_widget(header)

        # Information text
        info = Label(
            text="Manage notification preferences for your admin account.",
            font_size=dp(13),
            color=SUBTEXT_COLOR,
            size_hint_y=None,
            height=dp(40),
            halign="left",
            valign="middle"
        )
        info.bind(size=lambda obj, value: setattr(obj, "text_size", value))
        root.add_widget(info)

        # Notification rows
        self._add_notification_row(
            root,
            "push_notifications",
            "Push Notifications",
            "Receive important app notifications."
        )

        self._add_notification_row(
            root,
            "bin_full_alerts",
            "Bin Full Alerts",
            "Get an alert when a waste bin is full."
        )

        self._add_notification_row(
            root,
            "task_notifications",
            "Task Notifications",
            "Receive staff task and collection updates."
        )

        self._add_notification_row(
            root,
            "route_alerts",
            "Route / Location Alerts",
            "Receive route and location related updates."
        )

        # Firebase status
        self.status_label = Label(
            text="Settings are saved automatically.",
            font_size=dp(12),
            color=SUBTEXT_COLOR,
            size_hint_y=None,
            height=dp(30),
            halign="center",
            valign="middle"
        )
        self.status_label.bind(
            size=lambda obj, value: setattr(obj, "text_size", value)
        )
        root.add_widget(self.status_label)

        # Spacer
        root.add_widget(
            Label(text="", size_hint_y=1)
        )

        self.add_widget(root)

    def _add_notification_row(self, parent, key, title_text, subtitle_text):
        row = RoundedBox(
            orientation="horizontal",
            padding=[dp(16), dp(10), dp(12), dp(10)],
            spacing=dp(10),
            size_hint_y=None,
            height=dp(72)
        )

        text_box = BoxLayout(
            orientation="vertical",
            spacing=dp(2)
        )

        title = Label(
            text=title_text,
            font_size=dp(15),
            bold=True,
            color=TEXT_COLOR,
            halign="left",
            valign="bottom"
        )
        title.bind(size=lambda obj, value: setattr(obj, "text_size", value))

        subtitle = Label(
            text=subtitle_text,
            font_size=dp(11.5),
            color=SUBTEXT_COLOR,
            halign="left",
            valign="top"
        )
        subtitle.bind(size=lambda obj, value: setattr(obj, "text_size", value))

        text_box.add_widget(title)
        text_box.add_widget(subtitle)

        switch = Switch(
            active=self.DEFAULT_SETTINGS.get(key, True),
            size_hint_x=None,
            width=dp(55)
        )
        switch.bind(active=lambda instance, value, k=key: self._save_value(k, value))

        self.switches[key] = switch

        row.add_widget(text_box)
        row.add_widget(switch)

        parent.add_widget(row)

    # -----------------------------------------------------
    # Firebase user / UID
    # -----------------------------------------------------
    def _get_firebase_uid(self):
        if get_current_user is None:
            return None

        try:
            result = get_current_user()

            # Supports: (success, user_data)
            if isinstance(result, tuple):
                if len(result) >= 2:
                    success, user_data = result[0], result[1]
                    if success is False:
                        return None
                    result = user_data
                elif len(result) == 1:
                    result = result[0]

            if isinstance(result, dict):
                return (
                    result.get("uid")
                    or result.get("localId")
                    or result.get("id")
                )

            return (
                getattr(result, "uid", None)
                or getattr(result, "localId", None)
                or getattr(result, "id", None)
            )

        except Exception as e:
            print("Firebase user error:", e)
            return None

    # -----------------------------------------------------
    # Firebase load
    # -----------------------------------------------------
    def _load_settings(self):
        uid = self._get_firebase_uid()

        if not uid:
            self.status_label.text = "Firebase user not found."
            return dict(self.DEFAULT_SETTINGS)

        self.firebase_uid = uid
        self.settings_path = f"admin/{uid}/notification_settings"

        if get_data is None:
            self.status_label.text = "Firebase connection is unavailable."
            return dict(self.DEFAULT_SETTINGS)

        try:
            data = get_data(self.settings_path)

            # Some Firebase helper implementations may return:
            # (success, data)
            if isinstance(data, tuple):
                if len(data) >= 2:
                    success, firebase_data = data[0], data[1]
                    if success is False:
                        firebase_data = None
                    data = firebase_data
                elif len(data) == 1:
                    data = data[0]

            if isinstance(data, dict):
                loaded = dict(self.DEFAULT_SETTINGS)

                for key in self.DEFAULT_SETTINGS:
                    if key in data:
                        loaded[key] = bool(data[key])

                self.status_label.text = "Settings loaded from Firebase."
                return loaded

            # First time: create default settings in Firebase
            defaults = dict(self.DEFAULT_SETTINGS)
            self._write_settings(defaults)

            self.status_label.text = "Default settings saved to Firebase."
            return defaults

        except Exception as e:
            print("Notification settings load error:", e)
            self.status_label.text = "Could not load Firebase settings."
            return dict(self.DEFAULT_SETTINGS)

    # -----------------------------------------------------
    # Firebase save
    # -----------------------------------------------------
    def _write_settings(self, settings):
        if not self.settings_path:
            return False

        if set_data is None:
            self.status_label.text = "Firebase save function unavailable."
            return False

        try:
            result = set_data(self.settings_path, dict(settings))

            # If helper returns success boolean/tuple, handle it.
            if isinstance(result, tuple):
                if len(result) > 0 and result[0] is False:
                    self.status_label.text = "Could not save settings."
                    return False

            if result is False:
                self.status_label.text = "Could not save settings."
                return False

            self.status_label.text = "Settings saved to Firebase."
            return True

        except Exception as e:
            print("Notification settings save error:", e)
            self.status_label.text = "Could not save settings."
            return False

    def _save_value(self, key, value):
        # Prevent Firebase writes while loading switches from Firebase.
        if self._loading:
            return

        if key not in self.DEFAULT_SETTINGS:
            return

        self.settings[key] = bool(value)
        self._write_settings(self.settings)

    # -----------------------------------------------------
    # Screen lifecycle
    # -----------------------------------------------------
    def on_enter(self, *args):
        self._loading = True

        self.settings = self._load_settings()

        for key, switch in self.switches.items():
            switch.active = bool(
                self.settings.get(
                    key,
                    self.DEFAULT_SETTINGS.get(key, True)
                )
            )

        self._loading = False

    # -----------------------------------------------------
    # Navigation
    # -----------------------------------------------------
    def _go_back(self, *_):
        try:
            if self.manager:
                self.manager.current = "admin_profile"
        except Exception as e:
            print("Admin profile navigation error:", e)


# ---------------------------------------------------------
# Optional standalone run
# ---------------------------------------------------------
class AdminNotificationSettingsApp(App):
    def build(self):
        from kivy.uix.screenmanager import ScreenManager

        manager = ScreenManager()
        manager.add_widget(
            AdminNotificationSettingsScreen(
                name="admin_notification_settings"
            )
        )
        return manager


if __name__ == "__main__":
    AdminNotificationSettingsApp().run()
