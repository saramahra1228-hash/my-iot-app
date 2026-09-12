"""
Admin Panel Screen — Smart Waste Monitor
--------------------------------------------------------------------
Firebase-connected Kivy Admin Panel.

Keeps the existing Premium Admin Panel design and adds:
- Firebase connection check when the screen opens
- Live Firebase counts for bins and staff
- Background refresh so the Kivy UI never freezes
- Safe support for get_data() returning either (success, data) or raw data
- Existing navigation and menu design preserved
- Add Bin / Assign Worker / Reports / Generate PDF routes are used
  automatically when those screens are registered in main.py
"""

import threading

from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.uix.behaviors import ButtonBehavior
from kivy.graphics import Color, RoundedRectangle, Rectangle, Line
from kivy.properties import ListProperty
from kivy.metrics import dp, sp
from kivy.clock import Clock

# Reused from the dashboard so every screen shares the same
# icon system, palette and bottom-nav behaviour.
from admin_dashboard_kivy import (
    VectorIcon, BottomNav, BG, DARK_GREEN, WHITE, TEXT_DARK,
    GREEN_BG, GREEN_FG,
)

# ---------------------------------------------------------------- #
# Firebase
# ---------------------------------------------------------------- #
try:
    from firebase_config import get_data
except Exception as exc:
    print("[ADMIN PANEL] Firebase import failed:", exc)
    get_data = None


# Firebase paths used by the existing Admin Dashboard / Map screens.
BIN_PATHS = (
    "bins",
    "waste_bins",
    "bin_data",
    "smart_bins",
    "bin",
)

STAFF_PATHS = (
    "staff",
    "users",
    "workers",
    "staff_locations",
)


# ================================================================ #
# Firebase helper functions                                        #
# ================================================================ #
def _unwrap_firebase_result(result):
    """
    Supports both common project helper formats:

        get_data(path) -> (success, data)
        get_data(path) -> data
    """
    if isinstance(result, tuple) and len(result) >= 2:
        success, data = result[0], result[1]
        return bool(success), data

    return True, result


def _read_first(paths):
    """Return the first non-empty Firebase path."""
    if get_data is None:
        return None

    for path in paths:
        try:
            success, data = _unwrap_firebase_result(get_data(path))

            if success and data not in (None, {}, []):
                return data

        except Exception as exc:
            print(f"[ADMIN PANEL] Firebase read failed for {path}: {exc}")

    return None


def _records(data):
    """Convert Firebase dict/list data into a list of records."""
    if data is None:
        return []

    if isinstance(data, list):
        return [x for x in data if isinstance(x, dict)]

    if isinstance(data, dict):
        result = []

        for key, value in data.items():
            if isinstance(value, dict):
                item = dict(value)
                item.setdefault("_id", key)
                result.append(item)

        return result

    return []


# ================================================================ #
# Small vector icons used only on this screen                      #
# ================================================================ #
class BackArrowIcon(ButtonBehavior, Widget):
    """Clean chevron-left arrow, drawn with vector lines."""

    color = ListProperty(list(WHITE))

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(pos=self.redraw, size=self.redraw, color=self.redraw)

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
                    ox + 0.68 * s, oy + 0.15 * s,
                    ox + 0.28 * s, oy + 0.50 * s,
                    ox + 0.68 * s, oy + 0.85 * s,
                ],
                width=dp(1.5),
                cap="round",
                joint="round",
            )


class ChevronRightIcon(Widget):
    """Small right-pointing chevron used at the end of each menu row."""

    color = ListProperty([0.5, 0.55, 0.55, 1])

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(pos=self.redraw, size=self.redraw, color=self.redraw)

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
                    ox + 0.32 * s, oy + 0.15 * s,
                    ox + 0.72 * s, oy + 0.50 * s,
                    ox + 0.32 * s, oy + 0.85 * s,
                ],
                width=dp(1.6),
                cap="round",
                joint="round",
            )


class ChartIcon(Widget):
    """Small bar/line chart glyph for 'View Reports'."""

    color = ListProperty(list(GREEN_FG))

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(pos=self.redraw, size=self.redraw, color=self.redraw)

    def redraw(self, *_):
        self.canvas.clear()

        with self.canvas:
            Color(*self.color)

            x, y = self.pos
            w, h = self.size
            s = min(w, h)

            ox = x + (w - s) / 2
            oy = y + (h - s) / 2

            # Axis
            Line(
                points=[
                    ox + 0.16 * s, oy + 0.18 * s,
                    ox + 0.16 * s, oy + 0.82 * s,
                ],
                width=dp(1.4),
                cap="round",
            )

            Line(
                points=[
                    ox + 0.16 * s, oy + 0.18 * s,
                    ox + 0.86 * s, oy + 0.18 * s,
                ],
                width=dp(1.4),
                cap="round",
            )

            # Rising bars
            bar_x = [0.32, 0.52, 0.72]
            bar_h = [0.30, 0.48, 0.62]

            for bx, bh in zip(bar_x, bar_h):
                x0 = ox + bx * s
                y0 = oy + 0.18 * s
                x1 = ox + (bx + 0.12) * s
                y1 = oy + (0.18 + bh) * s

                Line(
                    rectangle=(x0, y0, x1 - x0, y1 - y0),
                    width=dp(1.3),
                    joint="round",
                )


class DocumentIcon(Widget):
    """Small page-with-checkmark glyph for 'Generate PDF'."""

    color = ListProperty(list(GREEN_FG))

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(pos=self.redraw, size=self.redraw, color=self.redraw)

    def redraw(self, *_):
        self.canvas.clear()

        with self.canvas:
            Color(*self.color)

            x, y = self.pos
            w, h = self.size
            s = min(w, h)

            ox = x + (w - s) / 2
            oy = y + (h - s) / 2

            # Page outline
            page = [
                (ox + 0.24 * s, oy + 0.14 * s),
                (ox + 0.60 * s, oy + 0.14 * s),
                (ox + 0.78 * s, oy + 0.32 * s),
                (ox + 0.78 * s, oy + 0.86 * s),
                (ox + 0.24 * s, oy + 0.86 * s),
            ]

            flat = [c for pt in page for c in pt]

            Line(
                points=flat,
                width=dp(1.3),
                close=True,
                joint="round",
                cap="round",
            )

            Line(
                points=[
                    ox + 0.60 * s, oy + 0.14 * s,
                    ox + 0.60 * s, oy + 0.32 * s,
                    ox + 0.78 * s, oy + 0.32 * s,
                ],
                width=dp(1.3),
                joint="round",
                cap="round",
            )

            # Text lines
            for fy in (0.48, 0.60):
                Line(
                    points=[
                        ox + 0.34 * s, oy + fy * s,
                        ox + 0.68 * s, oy + fy * s,
                    ],
                    width=dp(1.1),
                    cap="round",
                )

            # Checkmark
            Line(
                points=[
                    ox + 0.33 * s, oy + 0.74 * s,
                    ox + 0.42 * s, oy + 0.68 * s,
                    ox + 0.58 * s, oy + 0.80 * s,
                ],
                width=dp(1.4),
                cap="round",
                joint="round",
            )


# ================================================================ #
# Menu card row                                                     #
# ================================================================ #
class MenuCard(ButtonBehavior, BoxLayout):
    """
    A tappable rounded row:
    icon chip + label + chevron.
    """

    def __init__(self, icon_factory, label_text, on_press_cb=None, **kwargs):
        super().__init__(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(64),
            padding=(dp(14), dp(10)),
            spacing=dp(12),
            **kwargs,
        )

        self._normal_color = (
            241 / 255,
            243 / 255,
            242 / 255,
            1,
        )

        self._pressed_color = (
            235 / 255,
            239 / 255,
            239 / 255,
            1,
        )

        with self.canvas.before:
            self._bg_col = Color(*self._normal_color)

            self._bg = RoundedRectangle(
                pos=self.pos,
                size=self.size,
                radius=[dp(14)],
            )

        self.bind(
            pos=self._sync,
            size=self._sync,
            state=self._on_state,
        )

        icon_holder = BoxLayout(
            size_hint=(None, None),
            size=(dp(36), dp(36)),
        )

        with icon_holder.canvas.before:
            Color(*GREEN_BG)

            icon_holder._bg = RoundedRectangle(
                pos=icon_holder.pos,
                size=icon_holder.size,
                radius=[dp(10)],
            )

        icon_holder.bind(
            pos=lambda w, *_: setattr(w._bg, "pos", w.pos),
            size=lambda w, *_: setattr(w._bg, "size", w.size),
        )

        icon_holder.add_widget(icon_factory())
        self.add_widget(icon_holder)

        label = Label(
            text=label_text,
            font_size=sp(14.5),
            bold=True,
            color=TEXT_DARK,
            halign="left",
            valign="middle",
            size_hint_x=1,
        )

        label.bind(
            size=lambda w, *_: setattr(w, "text_size", w.size)
        )

        self.add_widget(label)

        self.add_widget(
            ChevronRightIcon(
                size_hint=(None, 1),
                width=dp(16),
            )
        )

        self._cb = on_press_cb

    def _sync(self, *_):
        self._bg.pos = self.pos
        self._bg.size = self.size

    def _on_state(self, *_):
        self._bg_col.rgba = (
            self._pressed_color
            if self.state == "down"
            else self._normal_color
        )

    def on_release(self):
        if self._cb:
            self._cb()


# ================================================================ #
# Header bar                                                        #
# ================================================================ #
class PanelHeader(FloatLayout):
    def __init__(self, title_text, on_back=None, **kwargs):
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

        self.bind(pos=self._sync, size=self._sync)

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
                "center_y": 0.5,
            },
            halign="center",
            valign="middle",
        )

        title.bind(
            size=lambda w, *_: setattr(
                w,
                "text_size",
                w.size,
            )
        )

        self.add_widget(title)

    def _sync(self, *_):
        self._bg.pos = self.pos
        self._bg.size = self.size


# ================================================================ #
# The screen itself                                                  #
# ================================================================ #
class AdminPanelScreen(Screen):

    NAV_ROUTES = {
        0: "admin_dashboard",
        1: "admin_map",
        2: "admin_panel",
        3: "admin_profile",
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self._firebase_refresh_running = False
        self._refresh_lock = threading.Lock()
        self._refresh_event = None

        root = BoxLayout(orientation="vertical")

        with root.canvas.before:
            Color(*BG)

            self._root_bg = Rectangle(
                pos=root.pos,
                size=root.size,
            )

        root.bind(
            pos=lambda w, *_: setattr(
                self._root_bg,
                "pos",
                w.pos,
            ),
            size=lambda w, *_: setattr(
                self._root_bg,
                "size",
                w.size,
            ),
        )

        # -------------------------------------------------------- #
        # Header
        # -------------------------------------------------------- #
        root.add_widget(
            PanelHeader(
                "Admin Panel",
                on_back=self._go_back,
            )
        )

        # -------------------------------------------------------- #
        # Firebase status line
        # -------------------------------------------------------- #
        self.firebase_status = Label(
            text="Checking Firebase...",
            font_size=sp(10.5),
            color=(0.35, 0.35, 0.35, 1),
            size_hint_y=None,
            height=dp(24),
            halign="center",
            valign="middle",
        )

        self.firebase_status.bind(
            size=lambda w, *_: setattr(
                w,
                "text_size",
                w.size,
            )
        )

        root.add_widget(self.firebase_status)

        # -------------------------------------------------------- #
        # Menu
        # -------------------------------------------------------- #
        menu_container = BoxLayout(
            orientation="vertical",
            padding=dp(20),
            spacing=dp(12),
        )

        menu_container.add_widget(
            MenuCard(
                lambda: VectorIcon(
                    icon_name="trash",
                    icon_color=list(GREEN_FG),
                    line_width=dp(1.5),
                ),
                "Add New Bin",
                on_press_cb=self._go_add_bin,
            )
        )

        menu_container.add_widget(
            MenuCard(
                lambda: VectorIcon(
                    icon_name="person",
                    icon_color=list(GREEN_FG),
                    line_width=dp(1.5),
                ),
                "Assign Worker",
                on_press_cb=self._go_assign_worker,
            )
        )

        menu_container.add_widget(
            MenuCard(
                lambda: ChartIcon(),
                "View Reports",
                on_press_cb=self._go_reports,
            )
        )

        menu_container.add_widget(
            MenuCard(
                lambda: DocumentIcon(),
                "Generate PDF",
                on_press_cb=self._go_generate_pdf,
            )
        )

        menu_container.add_widget(Widget())

        root.add_widget(menu_container)

        # -------------------------------------------------------- #
        # Bottom nav
        # -------------------------------------------------------- #
        nav = BottomNav(on_nav=self._on_nav)

        for i, btn in enumerate(nav.buttons):
            btn.set_active(i == 2)

        root.add_widget(nav)

        self.add_widget(root)

    # ============================================================ #
    # SCREEN LIFECYCLE
    # ============================================================ #
    def on_enter(self, *args):
        """
        Called whenever Admin Panel becomes visible.

        Starts an immediate Firebase read and then refreshes
        periodically while this screen is active.
        """
        self._start_firebase_refresh()

        if self._refresh_event is None:
            self._refresh_event = Clock.schedule_interval(
                self._start_firebase_refresh,
                5,
            )

    def on_leave(self, *args):
        """
        Stop the periodic timer when the user leaves the panel.
        """
        if self._refresh_event is not None:
            self._refresh_event.cancel()
            self._refresh_event = None

    # ============================================================ #
    # FIREBASE
    # ============================================================ #
    def _start_firebase_refresh(self, *_):
        if self._firebase_refresh_running:
            return

        if get_data is None:
            self.firebase_status.text = (
                "Firebase service unavailable"
            )
            return

        with self._refresh_lock:
            if self._firebase_refresh_running:
                return

            self._firebase_refresh_running = True

        threading.Thread(
            target=self._firebase_worker,
            daemon=True,
        ).start()

    def _firebase_worker(self):
        try:
            bins_data = _read_first(BIN_PATHS)
            staff_data = _read_first(STAFF_PATHS)

            bins = _records(bins_data)
            staff = _records(staff_data)

            # A successful read can still legitimately return zero
            # records. We show that clearly instead of treating it
            # as an error.
            Clock.schedule_once(
                lambda dt, b=bins, s=staff:
                self._apply_firebase_status(b, s),
                0,
            )

        except Exception as exc:
            print(
                "[ADMIN PANEL] Firebase worker failed:",
                exc,
            )

            Clock.schedule_once(
                lambda dt, err=str(exc):
                self._show_firebase_error(err),
                0,
            )

        finally:
            with self._refresh_lock:
                self._firebase_refresh_running = False

    def _apply_firebase_status(self, bins, staff):
        """
        Update only the small status line.

        The actual Admin Panel cards remain exactly the same.
        """
        if not self.parent:
            return

        self.firebase_status.text = (
            f"Firebase Connected  •  "
            f"{len(bins)} Bins  •  "
            f"{len(staff)} Staff"
        )

        self.firebase_status.color = (
            0.18,
            0.50,
            0.30,
            1,
        )

        print(
            "[ADMIN PANEL] Firebase connected:",
            f"{len(bins)} bins, {len(staff)} staff",
        )

    def _show_firebase_error(self, error):
        self.firebase_status.text = (
            "Firebase connection error"
        )

        self.firebase_status.color = (
            0.80,
            0.15,
            0.15,
            1,
        )

        print(
            "[ADMIN PANEL] Firebase connection error:",
            error,
        )

    # Public method if another screen wants to force refresh.
    def refresh_firebase(self):
        self._start_firebase_refresh()

    # ============================================================ #
    # NAVIGATION
    # ============================================================ #
    def _on_nav(self, index):
        target = self.NAV_ROUTES.get(index)

        if target is None or target == self.name:
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
                f"'{target}' is not registered in main.py's "
                "ScreenManager yet."
            )
            return

        self.manager.current = target

    def _go_back(self):
        self._on_nav(0)

    # ============================================================ #
    # MENU ROW ACTIONS
    # ============================================================ #
    def _open_if_registered(self, *screen_names):
        """
        Open the first registered screen from the supplied names.
        Returns True when navigation succeeded.
        """
        if self.manager is None:
            return False

        for screen_name in screen_names:
            if screen_name in self.manager.screen_names:
                self.manager.current = screen_name
                return True

        return False

    def _go_add_bin(self):
        # Supports common names without breaking the current main.py.
        if not self._open_if_registered(
            "add_bin",
            "add_new_bin",
            "admin_add_bin",
        ):
            print(
                "Add Bin screen is not registered yet. "
                "Register one of: add_bin / add_new_bin / admin_add_bin"
            )

    def _go_assign_worker(self):
        if not self._open_if_registered(
            "assign_worker",
            "admin_assign_worker",
        ):
            print(
                "Assign Worker screen is not registered yet. "
                "Register one of: assign_worker / admin_assign_worker"
            )

    def _go_reports(self):
        if not self._open_if_registered(
            "admin_reports",
            "reports",
            "view_reports",
        ):
            print(
                "Reports screen is not registered yet. "
                "Register one of: admin_reports / reports / view_reports"
            )

    def _go_generate_pdf(self):
        if not self._open_if_registered(
            "generate_pdf",
            "admin_generate_pdf",
            "pdf_report",
        ):
            print(
                "PDF screen is not registered yet. "
                "Register one of: generate_pdf / admin_generate_pdf / pdf_report"
            )


if __name__ == "__main__":
    pass
