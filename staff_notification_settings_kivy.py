"""
Staff Notification Settings — Smart Waste Monitor

Working notification-preference screen for the Kivy Staff app.

Features:
- Back button returns to Staff Profile.
- Four notification switches.
- Preferences are saved locally with Kivy JsonStore.
- Settings remain saved after closing/reopening the app.
- Designed to work on Windows and Android.
"""

from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.uix.button import Button
from kivy.uix.switch import Switch
from kivy.graphics import Color, Rectangle, RoundedRectangle, Line
from kivy.metrics import dp, sp
from kivy.storage.jsonstore import JsonStore


# ---------------------------------------------------------
# COLORS
# ---------------------------------------------------------
DARK_GREEN = (0 / 255, 77 / 255, 52 / 255, 1)
WHITE = (1, 1, 1, 1)
BG = (1, 1, 1, 1)
TEXT_DARK = (51 / 255, 51 / 255, 51 / 255, 1)
TEXT_GRAY = (110 / 255, 110 / 255, 110 / 255, 1)
LIGHT_GRAY = (234 / 255, 234 / 255, 234 / 255, 1)
GREEN = (46 / 255, 125 / 255, 50 / 255, 1)


# ---------------------------------------------------------
# HEADER
# ---------------------------------------------------------
class NotificationHeader(FloatLayout):

    def __init__(self, on_back=None, **kwargs):
        super().__init__(
            size_hint=(1, None),
            height=dp(65),
            **kwargs
        )

        with self.canvas.before:
            Color(*DARK_GREEN)
            self.bg = Rectangle(pos=self.pos, size=self.size)

        self.bind(pos=self._sync, size=self._sync)

        back = Button(
            text="‹",
            font_size=sp(38),
            bold=True,
            color=WHITE,
            background_normal="",
            background_color=(0, 0, 0, 0),
            size_hint=(None, None),
            size=(dp(45), dp(55)),
            pos_hint={"x": 0.02, "center_y": 0.5},
        )

        if on_back:
            back.bind(on_release=lambda *_: on_back())

        self.add_widget(back)

        title = Label(
            text="Notification Settings",
            color=WHITE,
            font_size=sp(18),
            bold=True,
            size_hint=(None, None),
            size=(dp(270), dp(40)),
            pos_hint={"center_x": 0.5, "center_y": 0.5},
            halign="center",
            valign="middle",
        )
        title.bind(size=lambda w, *_: setattr(w, "text_size", w.size))
        self.add_widget(title)

    def _sync(self, *_):
        self.bg.pos = self.pos
        self.bg.size = self.size


# ---------------------------------------------------------
# NOTIFICATION ROW
# ---------------------------------------------------------
class NotificationRow(BoxLayout):

    def __init__(self, title, description, active, on_change, **kwargs):
        super().__init__(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(76),
            padding=(dp(18), dp(8)),
            spacing=dp(10),
            **kwargs
        )

        with self.canvas.before:
            Color(*WHITE)
            self.bg = RoundedRectangle(
                pos=self.pos,
                size=self.size,
                radius=[dp(8)]
            )

        self.bind(pos=self._sync, size=self._sync)

        text_box = BoxLayout(
            orientation="vertical",
            spacing=dp(2)
        )

        title_lbl = Label(
            text=title,
            color=TEXT_DARK,
            font_size=sp(15),
            bold=True,
            halign="left",
            valign="middle",
            size_hint_y=None,
            height=dp(28),
        )
        title_lbl.bind(
            size=lambda w, *_: setattr(w, "text_size", w.size)
        )

        desc_lbl = Label(
            text=description,
            color=TEXT_GRAY,
            font_size=sp(11.5),
            halign="left",
            valign="top",
        )
        desc_lbl.bind(
            size=lambda w, *_: setattr(w, "text_size", w.size)
        )

        text_box.add_widget(title_lbl)
        text_box.add_widget(desc_lbl)

        self.add_widget(text_box)

        switch_box = BoxLayout(
            size_hint_x=None,
            width=dp(55),
            padding=(dp(5), dp(12))
        )

        self.switch = Switch(
            active=bool(active),
            size_hint=(None, None),
            size=(dp(45), dp(30))
        )
        self.switch.bind(
            active=lambda instance, value: on_change(value)
        )

        switch_box.add_widget(self.switch)
        self.add_widget(switch_box)

    def _sync(self, *_):
        self.bg.pos = self.pos
        self.bg.size = self.size


# ---------------------------------------------------------
# STAFF NOTIFICATION SETTINGS SCREEN
# ---------------------------------------------------------
class StaffNotificationSettingsScreen(Screen):

    STORE_KEY = "staff_notification_settings"

    DEFAULTS = {
        "push_notifications": True,
        "bin_full_alerts": True,
        "task_notifications": True,
        "route_alerts": True,
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.store = JsonStore("staff_notification_settings.json")

        root = BoxLayout(orientation="vertical")

        with root.canvas.before:
            Color(*BG)
            self.root_bg = Rectangle(
                pos=root.pos,
                size=root.size
            )

        root.bind(
            pos=lambda w, *_: setattr(self.root_bg, "pos", w.pos),
            size=lambda w, *_: setattr(self.root_bg, "size", w.size),
        )

        # Header
        root.add_widget(
            NotificationHeader(on_back=self._go_back)
        )

        # Content
        content = BoxLayout(
            orientation="vertical",
            padding=(dp(16), dp(16)),
            spacing=dp(10)
        )

        heading = Label(
            text="Manage Notifications",
            color=TEXT_DARK,
            font_size=sp(19),
            bold=True,
            size_hint_y=None,
            height=dp(34),
            halign="left",
            valign="middle",
        )
        heading.bind(
            size=lambda w, *_: setattr(w, "text_size", w.size)
        )
        content.add_widget(heading)

        info = Label(
            text="Choose which alerts you want to receive.",
            color=TEXT_GRAY,
            font_size=sp(12),
            size_hint_y=None,
            height=dp(28),
            halign="left",
            valign="middle",
        )
        info.bind(
            size=lambda w, *_: setattr(w, "text_size", w.size)
        )
        content.add_widget(info)

        content.add_widget(Widget(size_hint_y=None, height=dp(4)))

        self.switches = {}

        rows = [
            (
                "push_notifications",
                "Push Notifications",
                "Receive important app notifications."
            ),
            (
                "bin_full_alerts",
                "Bin Full Alerts",
                "Get an alert when a waste bin is full."
            ),
            (
                "task_notifications",
                "Task Notifications",
                "Receive staff task and collection updates."
            ),
            (
                "route_alerts",
                "Route / Location Alerts",
                "Receive route and location related updates."
            ),
        ]

        for key, title, description in rows:
            row = NotificationRow(
                title=title,
                description=description,
                active=self._get_value(key),
                on_change=lambda value, k=key: self._save_value(k, value)
            )
            content.add_widget(row)
            self.switches[key] = row.switch

        content.add_widget(Widget())

        status = Label(
            text="Settings are saved automatically.",
            color=TEXT_GRAY,
            font_size=sp(11),
            size_hint_y=None,
            height=dp(24),
            halign="center",
            valign="middle",
        )
        status.bind(
            size=lambda w, *_: setattr(w, "text_size", w.size)
        )
        content.add_widget(status)

        root.add_widget(content)

        self.add_widget(root)

    # -----------------------------------------------------
    # STORAGE
    # -----------------------------------------------------
    def _get_value(self, key):
        if self.store.exists(self.STORE_KEY):
            data = self.store.get(self.STORE_KEY)
            return bool(
                data.get(
                    key,
                    self.DEFAULTS.get(key, True)
                )
            )

        return self.DEFAULTS.get(key, True)

    def _save_value(self, key, value):
        current = {}

        if self.store.exists(self.STORE_KEY):
            current = dict(self.store.get(self.STORE_KEY))

        current[key] = bool(value)
        self.store.put(self.STORE_KEY, **current)

        print(
            f"Notification setting changed: {key} = {bool(value)}"
        )

    # -----------------------------------------------------
    # NAVIGATION
    # -----------------------------------------------------
    def _go_back(self):
        if self.manager and "staff_profile" in self.manager.screen_names:
            self.manager.current = "staff_profile"
        else:
            print("Staff Profile screen is not registered.")

    def on_enter(self, *args):
        # Reload saved values whenever the screen is opened.
        for key, switch in self.switches.items():
            switch.active = self._get_value(key)
