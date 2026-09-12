"""
staff_route_kivy.py
--------------------------------------------------------------------
Updated Staff Route screen for the Smart Waste Monitoring System.

Features
--------
- Real OpenStreetMap map using kivy_garden.mapview
- B-001 / B-002 / B-003 route markers
- Dotted route line
- "You" live-location marker
- Android GPS through Plyer
- Firebase location update in a background thread
- Google Maps navigation for the next stop
- Staff Dashboard / Route / History / Profile bottom navigation
- Safe navigation so missing screens do not crash the app
- Android-only jnius import is hidden from Pylance
"""

from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.uix.behaviors import ButtonBehavior
from kivy.graphics import Color, Rectangle, RoundedRectangle, Line, Ellipse, Triangle
from kivy.utils import get_color_from_hex as hexc
from kivy.metrics import dp, sp
from kivy.clock import Clock
from kivy.utils import platform
import math
import webbrowser
import json
from pathlib import Path
import threading


# -----------------------------------------------------------------
# Optional Android GPS
# -----------------------------------------------------------------
try:
    from plyer import gps  # type: ignore[import-not-found]
except Exception:
    gps = None


_request_android_location_permission = None

if platform == "android":
    def _request_android_location_permission():
        try:
            # Dynamic import prevents the Windows/Pylance
            # "Import jnius could not be resolved" warning.
            jnius_module = __import__("jnius")
            autoclass = getattr(jnius_module, "autoclass")

            PythonActivity = autoclass(
                "org.kivy.android.PythonActivity"
            )
            ActivityCompat = autoclass(
                "androidx.core.app.ActivityCompat"
            )
            ManifestPermission = autoclass(
                "android.Manifest$permission"
            )

            ActivityCompat.requestPermissions(
                PythonActivity.mActivity,
                [
                    ManifestPermission.ACCESS_FINE_LOCATION,
                    ManifestPermission.ACCESS_COARSE_LOCATION,
                ],
                1001,
            )
        except Exception as exc:
            print("Android GPS permission request failed:", exc)


# -----------------------------------------------------------------
# MapView
# -----------------------------------------------------------------
try:
    from kivy_garden.mapview import MapView, MapMarker, MapLayer  # type: ignore[import-not-found]
except Exception as exc:
    MapView = None
    MapMarker = None
    MapLayer = None
    print("kivy_garden.mapview is not available:", exc)


# -----------------------------------------------------------------
# Firebase helpers
# -----------------------------------------------------------------
try:
    from firebase_config import update_location
except Exception:
    def update_location(*args, **kwargs):
        print("firebase_config.update_location is not available")
        return False, "Firebase update_location is unavailable"


try:
    from firebase_auth import get_current_user
except Exception:
    get_current_user = None


# -----------------------------------------------------------------
# Screen names
# -----------------------------------------------------------------
BACK_SCREEN = "staff_dashboard"
DASHBOARD_SCREEN = "staff_dashboard"
HISTORY_SCREEN = "staff_task_history"
PROFILE_SCREEN = "staff_profile"


# -----------------------------------------------------------------
# Colours
# -----------------------------------------------------------------
GREEN = "#004D34"
TEXT_GRAY = "#777777"
NAV_ACTIVE = "#FFFFFF"
NAV_INACTIVE = "#A3C4B7"

STATUS_GREEN = "#2E7D32"
STATUS_PENDING = "#D32F2F"
STATUS_NEXT = "#F2A900"
YOU_COLOR = "#1E88E5"


# -----------------------------------------------------------------
# Default route area
# -----------------------------------------------------------------
# Wah Cantt demo coordinates.
# Replace these later with Firebase bin coordinates.
WAH_LAT = 33.7714
WAH_LNG = 72.7518


# (label, latitude, longitude, colour)
ROUTE_PINS = [
    ("B-001", WAH_LAT + 0.0020, WAH_LNG - 0.0015, STATUS_GREEN),
    ("B-002", WAH_LAT - 0.0010, WAH_LNG + 0.0035, STATUS_NEXT),
    ("B-003", WAH_LAT - 0.0040, WAH_LNG + 0.0010, STATUS_PENDING),
]


# =================================================================
# ICONS
# =================================================================

class BackArrowIcon(ButtonBehavior, Widget):
    def __init__(self, color_hex="#FFFFFF", **kwargs):
        super().__init__(**kwargs)
        with self.canvas:
            Color(*hexc(color_hex))
            self._line = Line(
                width=dp(1.6),
                cap="round",
                joint="round",
            )
        self.bind(pos=self._redraw, size=self._redraw)
        self._redraw()

    def _redraw(self, *args):
        x, y = self.pos
        w, h = self.size
        self._line.points = [
            x + w * 0.68, y + h * 0.12,
            x + w * 0.28, y + h * 0.50,
            x + w * 0.68, y + h * 0.88,
        ]


class TrashBinIcon(Widget):
    def __init__(self, color_hex="#FFFFFF", **kwargs):
        super().__init__(**kwargs)
        with self.canvas:
            Color(*hexc(color_hex))
            self._lid = Line(width=dp(1.1), cap="round")
            self._body = Line(
                width=dp(1.1),
                cap="round",
                joint="round",
            )
        self.bind(pos=self._redraw, size=self._redraw)
        self._redraw()

    def _redraw(self, *args):
        x, y = self.pos
        w, h = self.size

        self._lid.points = [
            x + w * 0.20, y + h * 0.72,
            x + w * 0.80, y + h * 0.72,
        ]

        self._body.points = [
            x + w * 0.30, y + h * 0.68,
            x + w * 0.28, y + h * 0.18,
            x + w * 0.72, y + h * 0.18,
            x + w * 0.70, y + h * 0.68,
        ]


class InfoCircleIcon(Widget):
    def __init__(self, color_hex="#333333", **kwargs):
        super().__init__(**kwargs)
        with self.canvas:
            Color(*hexc(color_hex))
            self._ring = Line(width=dp(1.3))
            self._dot = Ellipse()

        self.bind(pos=self._redraw, size=self._redraw)
        self._redraw()

    def _redraw(self, *args):
        x, y = self.pos
        w, h = self.size
        cx = x + w / 2
        cy = y + h / 2
        r = min(w, h) * 0.42

        self._ring.circle = (cx, cy, r)

        dot_r = r * 0.28
        self._dot.pos = (
            cx - dot_r,
            cy - dot_r,
        )
        self._dot.size = (
            dot_r * 2,
            dot_r * 2,
        )


class NavHomeIcon(Widget):
    def __init__(self, color_hex=NAV_INACTIVE, **kwargs):
        super().__init__(**kwargs)
        with self.canvas:
            Color(*hexc(color_hex))
            self._roof = Line(
                width=dp(1.3),
                joint="round",
                cap="round",
            )
            self._body = Line(width=dp(1.3))

        self.bind(pos=self._redraw, size=self._redraw)
        self._redraw()

    def _redraw(self, *args):
        x, y = self.pos
        w, h = self.size
        cx = x + w / 2

        self._roof.points = [
            x + w * 0.08, y + h * 0.48,
            cx, y + h * 0.90,
            x + w * 0.92, y + h * 0.48,
        ]

        self._body.rectangle = (
            x + w * 0.22,
            y + h * 0.10,
            w * 0.56,
            h * 0.42,
        )


class NavPinIcon(Widget):
    def __init__(self, color_hex=NAV_ACTIVE, **kwargs):
        super().__init__(**kwargs)
        with self.canvas:
            Color(*hexc(color_hex))
            self._outline = Line(
                width=dp(1.3),
                joint="round",
                cap="round",
            )
            self._hole = Line(width=dp(1.1))

        self.bind(pos=self._redraw, size=self._redraw)
        self._redraw()

    def _redraw(self, *args):
        x, y = self.pos
        w, h = self.size
        cx = x + w / 2

        r = w * 0.34
        cy = y + h * 0.92 - r

        segments = 16
        pts = []

        for i in range(segments + 1):
            theta = math.pi * (i / segments)
            pts += [
                cx - r * math.cos(theta),
                cy + r * math.sin(theta),
            ]

        pts += [
            cx - r,
            cy,
            cx,
            y + h * 0.06,
            cx + r,
            cy,
        ]

        self._outline.points = pts
        self._hole.circle = (cx, cy, r * 0.38)


class NavClockIcon(Widget):
    def __init__(self, color_hex=NAV_INACTIVE, **kwargs):
        super().__init__(**kwargs)
        with self.canvas:
            Color(*hexc(color_hex))
            self._face = Line(width=dp(1.3))
            self._hands = Line(
                width=dp(1.1),
                cap="round",
            )

        self.bind(pos=self._redraw, size=self._redraw)
        self._redraw()

    def _redraw(self, *args):
        x, y = self.pos
        w, h = self.size
        cx = x + w / 2
        cy = y + h / 2
        r = min(w, h) * 0.42

        self._face.circle = (cx, cy, r)

        self._hands.points = [
            cx, cy,
            cx, cy + r * 0.55,
            cx, cy,
            cx + r * 0.45, cy,
        ]


class NavPersonIcon(Widget):
    def __init__(self, color_hex=NAV_INACTIVE, **kwargs):
        super().__init__(**kwargs)
        with self.canvas:
            Color(*hexc(color_hex))
            self._head = Ellipse()
            self._body = Ellipse()

        self.bind(pos=self._redraw, size=self._redraw)
        self._redraw()

    def _redraw(self, *args):
        x, y = self.pos
        w, h = self.size
        cx = x + w / 2

        head_d = h * 0.40
        self._head.size = (head_d, head_d)
        self._head.pos = (
            cx - head_d / 2,
            y + h * 0.48,
        )

        body_w = w * 0.78
        body_h = h * 0.42

        self._body.size = (
            body_w,
            body_h,
        )
        self._body.pos = (
            cx - body_w / 2,
            y + h * 0.02,
        )


class NavButton(ButtonBehavior, AnchorLayout):
    def __init__(
        self,
        icon_widget,
        on_tap,
        icon_size=dp(16),
        **kwargs
    ):
        super().__init__(**kwargs)

        icon_widget.size_hint = (None, None)
        icon_widget.size = (
            icon_size,
            icon_size,
        )

        self.add_widget(icon_widget)
        self.bind(
            on_release=lambda inst: on_tap()
        )


# =================================================================
# MAP MARKERS
# =================================================================

if MapMarker is not None:

    class ColorPinMarker(MapMarker):
        """Colour-coded bin marker."""

        def __init__(
            self,
            color_hex=STATUS_PENDING,
            pin_size=None,
            **kwargs
        ):
            super().__init__(**kwargs)

            self.color = (
                0, 0, 0, 0
            )

            w = pin_size or dp(30)
            h = w * 34.0 / 30.0

            self.size = (
                w,
                h,
            )

            self.anchor_x = 0.5
            self.anchor_y = 0.0

            with self.canvas.after:
                Color(*hexc(color_hex))
                self._tail = Triangle()
                self._head = Ellipse()

                Color(1, 1, 1, 1)
                self._ring = Line(width=dp(1.6))

            self._bin_icon = TrashBinIcon(
                color_hex="#FFFFFF"
            )

            self.add_widget(self._bin_icon)

            self.bind(
                pos=self._redraw,
                size=self._redraw,
            )

            self._redraw()

        def _redraw(self, *args):
            x, y = self.pos
            w, h = self.size

            cx = x + w / 2
            r = w * 0.42
            head_cy = y + h - r

            self._tail.points = [
                cx - r * 0.55,
                head_cy - r * 0.15,
                cx + r * 0.55,
                head_cy - r * 0.15,
                cx,
                y,
            ]

            self._head.pos = (
                cx - r,
                head_cy - r,
            )

            self._head.size = (
                r * 2,
                r * 2,
            )

            self._ring.circle = (
                cx,
                head_cy,
                r * 0.98,
            )

            icon_size = r * 1.1

            self._bin_icon.size = (
                icon_size,
                icon_size,
            )

            self._bin_icon.pos = (
                cx - icon_size / 2,
                head_cy - icon_size / 2,
            )


    class YouMarker(MapMarker):
        """Blue marker for the staff member's current location."""

        def __init__(
            self,
            color_hex=YOU_COLOR,
            dot_size=None,
            **kwargs
        ):
            super().__init__(**kwargs)

            self.color = (
                0, 0, 0, 0
            )

            d = dot_size or dp(20)

            self.size = (
                d,
                d,
            )

            self.anchor_x = 0.5
            self.anchor_y = 0.5

            with self.canvas.after:
                self._halo_color = Color(
                    *hexc(color_hex)
                )
                self._halo_color.a = 0.25
                self._halo = Ellipse()

                self._dot_color = Color(
                    *hexc(color_hex)
                )
                self._dot = Ellipse()

                Color(1, 1, 1, 1)
                self._ring = Line(
                    width=dp(1.6)
                )

            self.bind(
                pos=self._redraw,
                size=self._redraw,
            )

            self._redraw()

        def _redraw(self, *args):
            x, y = self.pos
            w, h = self.size

            cx = x + w / 2
            cy = y + h / 2
            r = min(w, h) / 2

            self._halo.pos = (
                cx - r,
                cy - r,
            )

            self._halo.size = (
                r * 2,
                r * 2,
            )

            dot_r = r * 0.55

            self._dot.pos = (
                cx - dot_r,
                cy - dot_r,
            )

            self._dot.size = (
                dot_r * 2,
                dot_r * 2,
            )

            self._ring.circle = (
                cx,
                cy,
                dot_r,
            )


    class RoutePathLayer(MapLayer):
        """Dotted line connecting route stops."""

        def __init__(
            self,
            coords,
            color_hex=GREEN,
            **kwargs
        ):
            super().__init__(**kwargs)

            self.coords = coords

            with self.canvas:
                Color(*hexc(color_hex))
                self._line = Line(
                    width=dp(2),
                    dash_length=7,
                    dash_offset=4,
                    joint="round",
                )

        def reposition(self):
            mapview = self.parent

            if not mapview or not self.coords:
                return

            pts = []

            for lat, lon in self.coords:
                try:
                    x, y = mapview.get_window_xy_from(
                        lat,
                        lon,
                        mapview.zoom,
                    )
                    pts += [x, y]
                except Exception:
                    continue

            self._line.points = pts


# =================================================================

# ================================================================
# SHARED TASK STATUS (local for now; Firebase can be connected next)
# ================================================================
TASK_STATUS_FILE = "staff_task_status.json"

def load_task_statuses():
    try:
        p = Path(TASK_STATUS_FILE)
        if p.exists():
            data = json.loads(p.read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else {}
    except Exception as exc:
        print("Task status read error:", exc)
    return {}

def save_task_status(bin_id, status):
    try:
        data = load_task_statuses()
        key = str(bin_id).replace("Bin:", "").replace(" ", "")
        data[key] = status
        Path(TASK_STATUS_FILE).write_text(
            json.dumps(data, indent=2),
            encoding="utf-8"
        )
        return True
    except Exception as exc:
        print("Task status save error:", exc)
        return False

# NEXT STOP CARD
# =================================================================

class NavigateButton(ButtonBehavior, AnchorLayout):
    def __init__(self, on_press_cb=None, button_text="Navigate", **kwargs):
        super().__init__(**kwargs)

        with self.canvas.before:
            Color(*hexc(GREEN))
            self._bg = RoundedRectangle(radius=[dp(10)])

        self.bind(pos=self._redraw, size=self._redraw)

        label = Label(
            text=button_text,
            font_size=sp(13),
            bold=True,
            color=(1, 1, 1, 1),
        )
        self.add_widget(label)

        if on_press_cb:
            self.bind(on_release=lambda inst: on_press_cb())

    def _redraw(self, *args):
        self._bg.pos = self.pos
        self._bg.size = self.size


class NextStopCard(BoxLayout):
    def __init__(
        self,
        bin_id="Bin :B-002",
        address="Street 16, Green Park",
        distance="1.2 km",
        on_navigate=None,
        on_collected=None,
        **kwargs
    ):
        super().__init__(
            orientation="vertical",
            size_hint_y=None,
            height=dp(220),
            padding=(dp(20), dp(10), dp(20), dp(10)),
            spacing=dp(5),
            **kwargs
        )

        with self.canvas.before:
            Color(1, 1, 1, 1)
            self._bg = Rectangle()
        self.bind(pos=self._redraw, size=self._redraw)

        self.status_lbl = Label(
            text="Status: Pending",
            font_size=sp(10),
            bold=True,
            color=hexc(STATUS_NEXT),
            size_hint_y=None,
            height=dp(16),
            halign="left",
            valign="middle",
        )
        self.status_lbl.bind(size=lambda inst, val: setattr(inst, "text_size", val))
        self.add_widget(self.status_lbl)

        next_stop_lbl = Label(
            text="Next Stop",
            font_size=sp(11),
            color=hexc(TEXT_GRAY),
            size_hint_y=None,
            height=dp(16),
            halign="left",
            valign="middle",
        )
        next_stop_lbl.bind(size=lambda inst, val: setattr(inst, "text_size", val))
        self.add_widget(next_stop_lbl)

        bin_row = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(28),
        )
        bin_lbl = Label(
            text=bin_id,
            font_size=sp(17),
            bold=True,
            color=(0, 0, 0, 1),
            halign="left",
            valign="middle",
        )
        bin_lbl.bind(size=lambda inst, val: setattr(inst, "text_size", val))
        bin_row.add_widget(bin_lbl)

        info_anchor = AnchorLayout(size_hint_x=None, width=dp(22))
        info_anchor.add_widget(
            InfoCircleIcon(size_hint=(None, None), size=(dp(18), dp(18)))
        )
        bin_row.add_widget(info_anchor)
        self.add_widget(bin_row)

        addr_row = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(22),
        )
        addr_lbl = Label(
            text=address,
            font_size=sp(11),
            color=hexc(TEXT_GRAY),
            halign="left",
            valign="middle",
        )
        addr_lbl.bind(size=lambda inst, val: setattr(inst, "text_size", val))
        addr_row.add_widget(addr_lbl)

        dist_lbl = Label(
            text=distance,
            font_size=sp(12),
            bold=True,
            color=hexc(GREEN),
            size_hint_x=None,
            width=dp(60),
            halign="right",
            valign="middle",
        )
        dist_lbl.bind(size=lambda inst, val: setattr(inst, "text_size", val))
        addr_row.add_widget(dist_lbl)
        self.add_widget(addr_row)

        self.add_widget(Widget(size_hint_y=None, height=dp(2)))

        self.navigate_btn = NavigateButton(
            on_press_cb=on_navigate,
            button_text="Navigate",
            size_hint_y=None,
            height=dp(38),
        )
        self.add_widget(self.navigate_btn)

        self.collect_btn = NavigateButton(
            on_press_cb=on_collected,
            button_text="Mark as Collected",
            size_hint_y=None,
            height=dp(38),
        )
        self.add_widget(self.collect_btn)

    def set_status(self, status):
        status = str(status)
        self.status_lbl.text = f"Status: {status}"

        if status.lower() == "collected":
            self.status_lbl.color = hexc(STATUS_GREEN)
            self.collect_btn.opacity = 0.45
            self.collect_btn.disabled = True
        elif status.lower() == "skipped":
            self.status_lbl.color = hexc(STATUS_PENDING)
            self.collect_btn.opacity = 1
            self.collect_btn.disabled = False
        else:
            self.status_lbl.color = hexc(STATUS_NEXT)
            self.collect_btn.opacity = 1
            self.collect_btn.disabled = False

    def _redraw(self, *args):
        self._bg.pos = self.pos
        self._bg.size = self.size


# =================================================================
# MAIN STAFF ROUTE SCREEN
# =================================================================

class StaffRouteScreen(Screen):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        root = BoxLayout(
            orientation="vertical"
        )

        self.add_widget(root)

        with root.canvas.before:
            Color(*hexc("#E8F0ED"))
            self._bg_rect = Rectangle()

        root.bind(
            pos=self._redraw_bg,
            size=self._redraw_bg,
        )

        # ---------------------------------------------------------
        # Header
        # ---------------------------------------------------------
        header = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(65),
            padding=(dp(16), 0),
            spacing=dp(14),
        )

        with header.canvas.before:
            Color(*hexc(GREEN))
            self._header_bg = Rectangle()

        header.bind(
            pos=self._redraw_header_bg,
            size=self._redraw_header_bg,
        )

        back_anchor = AnchorLayout(
            size_hint_x=None,
            width=dp(20),
        )

        back_btn = BackArrowIcon(
            color_hex="#FFFFFF",
            size_hint=(None, None),
            size=(dp(18), dp(18)),
        )

        back_btn.bind(
            on_release=lambda inst:
            self._go_back()
        )

        back_anchor.add_widget(back_btn)
        header.add_widget(back_anchor)

        title_lbl = Label(
            text="My Route",
            font_size=sp(18),
            bold=True,
            color=(1, 1, 1, 1),
            halign="left",
            valign="middle",
        )

        title_lbl.bind(
            size=lambda inst, val:
            setattr(inst, "text_size", val)
        )

        header.add_widget(title_lbl)
        root.add_widget(header)

        # ---------------------------------------------------------
        # Map
        # ---------------------------------------------------------
        self.map_view = None

        if MapView is not None:
            self.map_view = MapView(
                zoom=15,
                lat=WAH_LAT,
                lon=WAH_LNG,
                size_hint=(1, 1),
            )
            root.add_widget(self.map_view)

        else:
            map_error = Label(
                text=(
                    "MapView is not installed.\n\n"
                    "Run:\n"
                    "pip install kivy_garden.mapview plyer"
                ),
                color=(0, 0, 0, 1),
                halign="center",
                valign="middle",
            )

            map_error.bind(
                size=lambda inst, val:
                setattr(inst, "text_size", val)
            )

            root.add_widget(map_error)

        Clock.schedule_once(
            self._setup_map,
            0.5,
        )

        # ---------------------------------------------------------
        # Next stop
        # ---------------------------------------------------------
        self.next_stop_card = NextStopCard(
            bin_id="Bin :B-002",
            address="Street 16, Green Park",
            distance="1.2 km",
            on_navigate=self._on_navigate,
            on_collected=self._mark_next_stop_collected,
        )
        root.add_widget(self.next_stop_card)
        self._refresh_next_stop_status()

        # ---------------------------------------------------------
        # Bottom navigation
        # ---------------------------------------------------------
        nav = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(52),
        )

        with nav.canvas.before:
            Color(*hexc(GREEN))
            self._nav_bg = Rectangle()

        nav.bind(
            pos=self._redraw_nav_bg,
            size=self._redraw_nav_bg,
        )

        nav.add_widget(
            NavButton(
                NavHomeIcon(
                    color_hex=NAV_INACTIVE
                ),
                self._go_dashboard,
                icon_size=dp(16),
            )
        )

        nav.add_widget(
            NavButton(
                NavPinIcon(
                    color_hex=NAV_ACTIVE
                ),
                self._go_route,
                icon_size=dp(16),
            )
        )

        nav.add_widget(
            NavButton(
                NavClockIcon(
                    color_hex=NAV_INACTIVE
                ),
                self._go_history,
                icon_size=dp(16),
            )
        )

        nav.add_widget(
            NavButton(
                NavPersonIcon(
                    color_hex=NAV_INACTIVE
                ),
                self._go_profile,
                icon_size=dp(16),
            )
        )

        root.add_widget(nav)

        # ---------------------------------------------------------
        # GPS state
        # ---------------------------------------------------------
        self.current_lat = WAH_LAT
        self.current_lng = WAH_LNG

        self._location_event = None
        self._you_marker = None
        self._gps_started = False
        self._map_ready = False

    # =============================================================
    # MAP SETUP
    # =============================================================

    def _setup_map(self, dt):
        if self.map_view is None:
            return

        if self._map_ready:
            return

        try:
            coords = []

            for label, lat, lon, color in ROUTE_PINS:
                marker = ColorPinMarker(
                    lat=lat,
                    lon=lon,
                    color_hex=color,
                )

                self.map_view.add_marker(marker)
                coords.append((lat, lon))

            if coords:
                path_layer = RoutePathLayer(
                    coords,
                    color_hex=GREEN,
                )

                self.map_view.add_layer(
                    path_layer,
                    mode="window",
                )

            self._you_marker = YouMarker(
                lat=self.current_lat,
                lon=self.current_lng,
                color_hex=YOU_COLOR,
            )

            self.map_view.add_marker(
                self._you_marker
            )

            self._map_ready = True

            print("Staff Route map loaded successfully.")

        except Exception as exc:
            print(
                "Staff Route map setup failed:",
                exc,
            )

    # =============================================================
    # STAFF ID
    # =============================================================

    def _get_staff_id(self):
        try:
            if get_current_user:
                user = get_current_user()

                if isinstance(user, dict):
                    return (
                        user.get("uid")
                        or user.get("localId")
                        or user.get("id")
                        or "staff_1"
                    )

                if user:
                    return (
                        getattr(user, "uid", None)
                        or getattr(user, "localId", None)
                        or getattr(user, "id", None)
                        or "staff_1"
                    )

        except Exception as exc:
            print(
                "Could not read current staff user:",
                exc,
            )

        return "staff_1"

    # =============================================================
    # GPS
    # =============================================================

    def _request_gps_permission(self):
        try:
            if _request_android_location_permission:
                _request_android_location_permission()
        except Exception as exc:
            print(
                "GPS permission request failed:",
                exc,
            )

    def _start_gps(self):
        if self._gps_started:
            return

        if gps is None:
            print(
                "Plyer GPS is not available. "
                "Desktop mode will use the demo location."
            )
            return

        try:
            self._request_gps_permission()

            gps.configure(
                on_location=self.on_gps_location,
                on_status=self.on_gps_status,
            )

            gps.start(
                minTime=5000,
                minDistance=5,
            )

            self._gps_started = True

            print("Real GPS started.")

        except Exception as exc:
            print(
                "GPS start failed:",
                exc,
            )

    def _stop_gps(self):
        if gps is None:
            return

        if not self._gps_started:
            return

        try:
            gps.stop()
        except Exception as exc:
            print(
                "GPS stop failed:",
                exc,
            )

        self._gps_started = False

    def on_gps_status(self, stype, status):
        print(
            "GPS status:",
            stype,
            status,
        )

    def on_gps_location(self, **kwargs):
        try:
            lat = float(
                kwargs.get("lat")
            )
            lon = float(
                kwargs.get("lon")
            )
        except (TypeError, ValueError):
            return

        Clock.schedule_once(
            lambda dt:
            self.update_worker_location(
                lat,
                lon,
            ),
            0,
        )

        self._send_location_to_firebase(
            lat,
            lon,
        )

    # =============================================================
    # FIREBASE LOCATION
    # =============================================================

    def _send_location_to_firebase(
        self,
        latitude,
        longitude,
    ):
        staff_id = self._get_staff_id()

        def worker():
            try:
                result = update_location(
                    latitude,
                    longitude,
                    user_id=staff_id,
                )

                if isinstance(result, tuple):
                    ok, detail = result
                else:
                    ok = bool(result)
                    detail = result

                if ok:
                    print(
                        "Location saved:",
                        staff_id,
                        "->",
                        f"{latitude:.6f}, {longitude:.6f}",
                    )
                else:
                    print(
                        "Firebase location update failed:",
                        detail,
                    )

            except Exception as exc:
                print(
                    "Firebase location update failed:",
                    exc,
                )

        threading.Thread(
            target=worker,
            daemon=True,
        ).start()

    def _send_location_tick(self, dt):
        # Desktop/demo heartbeat.
        if self._gps_started:
            return

        self._send_location_to_firebase(
            self.current_lat,
            self.current_lng,
        )

    # =============================================================
    # MOVE YOU MARKER
    # =============================================================

    def update_worker_location(
        self,
        new_lat,
        new_lng,
    ):
        self.current_lat = float(new_lat)
        self.current_lng = float(new_lng)

        if self._you_marker is None:
            return

        try:
            self._you_marker.lat = (
                self.current_lat
            )
            self._you_marker.lon = (
                self.current_lng
            )

            # Refresh MapView's marker layer.
            layer = getattr(
                self.map_view,
                "_default_marker_layer",
                None,
            )

            if layer is not None:
                layer.set_marker_position(
                    self.map_view,
                    self._you_marker,
                )

        except Exception as exc:
            print(
                "Marker update warning:",
                exc,
            )

    # =============================================================
    # SCREEN LIFECYCLE
    # =============================================================

    def on_enter(self, *args):
        self._refresh_next_stop_status()
        if self.map_view is not None:
            if not self._map_ready:
                Clock.schedule_once(
                    self._setup_map,
                    0,
                )

        self._start_gps()

        if self._location_event is None:
            self._location_event = (
                Clock.schedule_interval(
                    self._send_location_tick,
                    5,
                )
            )

    def on_leave(self, *args):
        self._stop_gps()

        if self._location_event is not None:
            self._location_event.cancel()
            self._location_event = None

    # =============================================================
    # MARK NEXT STOP AS COLLECTED
    # =============================================================

    def _mark_next_stop_collected(self):
        """Mark B-002 as collected and save the status locally."""
        try:
            bin_id = "B-002"
            if save_task_status(bin_id, "Collected"):
                self.next_stop_card.set_status("Collected")
                print(f"{bin_id} marked as Collected.")
            else:
                print(f"Could not save collection status for {bin_id}.")
        except Exception as exc:
            print("Collection status update failed:", exc)

    def _refresh_next_stop_status(self):
        """Load the saved B-002 status and update the card."""
        try:
            statuses = load_task_statuses()
            status = statuses.get("B-002", "Pending")
            self.next_stop_card.set_status(status)
        except Exception as exc:
            print("Could not refresh next-stop status:", exc)

    # =============================================================
    # NAVIGATION TO GOOGLE MAPS
    # =============================================================

    def _on_navigate(self):
        if not ROUTE_PINS:
            return

        next_bin = next(
            (
                p
                for p in ROUTE_PINS
                if p[0] == "B-002"
            ),
            ROUTE_PINS[0],
        )

        _, lat, lon, _ = next_bin

        url = (
            "https://www.google.com/maps/dir/"
            "?api=1"
            f"&origin={self.current_lat},{self.current_lng}"
            f"&destination={lat},{lon}"
            "&travelmode=driving"
        )

        try:
            webbrowser.open(url)
            print(
                "Opening Google Maps navigation..."
            )
        except Exception as exc:
            print(
                "Could not open navigation:",
                exc,
            )

    # =============================================================
    # DRAWING HELPERS
    # =============================================================

    def _redraw_bg(self, instance, *args):
        self._bg_rect.pos = instance.pos
        self._bg_rect.size = instance.size

    def _redraw_header_bg(
        self,
        instance,
        *args
    ):
        self._header_bg.pos = instance.pos
        self._header_bg.size = instance.size

    def _redraw_nav_bg(
        self,
        instance,
        *args
    ):
        self._nav_bg.pos = instance.pos
        self._nav_bg.size = instance.size

    # =============================================================
    # NAVIGATION
    # =============================================================

    def _go_back(self):
        self._navigate(BACK_SCREEN)

    def _go_dashboard(self):
        self._navigate(DASHBOARD_SCREEN)

    def _go_route(self):
        pass

    def _go_history(self):
        self._navigate(HISTORY_SCREEN)

    def _go_profile(self):
        self._navigate(PROFILE_SCREEN)

    def _navigate(self, target):
        if self.manager and target in self.manager.screen_names:
            self.manager.current = target
        else:
            print(
                f"(staff_route) '{target}' is not registered "
                "in main.py."
            )


# =================================================================
# STANDALONE PREVIEW
# =================================================================

if __name__ == "__main__":
    from kivy.app import App
    from kivy.uix.screenmanager import ScreenManager
    from kivy.core.window import Window

    class PlaceholderScreen(Screen):
        def __init__(
            self,
            label_text,
            **kwargs
        ):
            super().__init__(**kwargs)

            self.add_widget(
                Label(
                    text=label_text,
                    color=(0, 0, 0, 1),
                )
            )

    class StaffRoutePreviewApp(App):
        def build(self):
            Window.size = (
                360,
                640,
            )

            Window.clearcolor = (
                1, 1, 1, 1
            )

            sm = ScreenManager()

            sm.add_widget(
                StaffRouteScreen(
                    name="staff_route"
                )
            )

            sm.add_widget(
                PlaceholderScreen(
                    "Staff Dashboard\n(placeholder)",
                    name="staff_dashboard",
                )
            )

            sm.add_widget(
                PlaceholderScreen(
                    "Task History\n(placeholder)",
                    name="staff_task_history",
                )
            )

            sm.add_widget(
                PlaceholderScreen(
                    "Staff Profile\n(placeholder)",
                    name="staff_profile",
                )
            )

            sm.current = "staff_route"

            return sm

    StaffRoutePreviewApp().run()
