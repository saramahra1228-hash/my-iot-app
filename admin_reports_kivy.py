""" 
Admin Reports Screen — Firebase Connected
------------------------------------------
Shows live Smart Waste Management report data from Firebase.

Firebase sources:
- bins
- staff
- assignments

Register in main.py:
    from admin_reports_kivy import AdminReportsScreen
    sm.add_widget(AdminReportsScreen(name="admin_reports"))
"""

import threading
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.widget import Widget
from kivy.graphics import Color, Rectangle, RoundedRectangle
from kivy.clock import Clock
from kivy.metrics import dp, sp
from kivy.utils import get_color_from_hex as hexc

from admin_dashboard_kivy import (
    BottomNav, BG, DARK_GREEN, WHITE, TEXT_DARK, GREEN_BG, GREEN_FG
)
from admin_panel_kivy import PanelHeader

try:
    from firebase_config import get_data
except Exception as exc:
    print("[REPORTS] Firebase import failed:", exc)
    get_data = None


BIN_PATHS = ("bins", "waste_bins", "bin_data", "smart_bins", "bin")
STAFF_PATHS = ("staff", "users", "workers")
ASSIGNMENT_PATHS = ("assignments", "bin_assignments", "staff_assignments")


def unwrap(result):
    if isinstance(result, tuple) and len(result) >= 2:
        return bool(result[0]), result[1]
    return True, result


def read_first(paths):
    if get_data is None:
        return None

    for path in paths:
        try:
            ok, data = unwrap(get_data(path))
            if ok and data not in (None, {}, []):
                return data
        except Exception as exc:
            print(f"[REPORTS] Read failed {path}: {exc}")

    return None


def records(data):
    if isinstance(data, list):
        return [x for x in data if isinstance(x, dict)]

    if isinstance(data, dict):
        out = []
        for key, value in data.items():
            if isinstance(value, dict):
                item = dict(value)
                item.setdefault("_id", key)
                out.append(item)
        return out

    return []


class StatCard(BoxLayout):
    def __init__(self, title, value="0", **kwargs):
        super().__init__(
            orientation="vertical",
            padding=(dp(12), dp(9)),
            spacing=dp(3),
            **kwargs
        )

        with self.canvas.before:
            Color(1, 1, 1, 1)
            self.bg = RoundedRectangle(
                pos=self.pos,
                size=self.size,
                radius=[dp(12)]
            )

        self.bind(pos=self._sync, size=self._sync)

        self.value_lbl = Label(
            text=value,
            font_size=sp(21),
            bold=True,
            color=DARK_GREEN,
            size_hint_y=None,
            height=dp(29),
            halign="left"
        )

        self.title_lbl = Label(
            text=title,
            font_size=sp(10.5),
            color=(.35, .35, .35, 1),
            halign="left",
            valign="middle"
        )

        self.title_lbl.bind(
            size=lambda w, *_: setattr(w, "text_size", w.size)
        )

        self.add_widget(self.value_lbl)
        self.add_widget(self.title_lbl)

    def _sync(self, *_):
        self.bg.pos = self.pos
        self.bg.size = self.size


class ReportRow(BoxLayout):
    """
    One Firebase bin report row.

    FIX:
    The report data contains 4 values:
        bin_id, name, fill_level, status

    Therefore this constructor accepts 4 values.
    """

    def __init__(self, bin_id, name, fill_level, status, **kwargs):
        super().__init__(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(44),
            padding=(dp(10), dp(5)),
            spacing=dp(4),
            **kwargs
        )

        with self.canvas.before:
            Color(0.95, 0.96, 0.95, 1)
            self.bg = RoundedRectangle(
                pos=self.pos,
                size=self.size,
                radius=[dp(8)]
            )

        self.bind(pos=self._sync, size=self._sync)

        columns = (
            (bin_id, .25, True),
            (name, .32, False),
            (fill_level, .18, False),
            (status, .25, True),
        )

        for text, width, bold in columns:
            lbl = Label(
                text=str(text),
                font_size=sp(10),
                bold=bold,
                color=TEXT_DARK,
                size_hint_x=width,
                halign="left",
                valign="middle",
                shorten=True,
                shorten_from="right",
            )
            lbl.bind(
                size=lambda w, *_: setattr(w, "text_size", w.size)
            )
            self.add_widget(lbl)

    def _sync(self, *_):
        self.bg.pos = self.pos
        self.bg.size = self.size


class ReportHeader(BoxLayout):
    """Column header for the bin status table."""

    def __init__(self, **kwargs):
        super().__init__(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(32),
            padding=(dp(10), dp(3)),
            spacing=dp(4),
            **kwargs
        )

        columns = (
            ("BIN ID", .25),
            ("NAME", .32),
            ("FILL", .18),
            ("STATUS", .25),
        )

        for text, width in columns:
            lbl = Label(
                text=text,
                font_size=sp(9.5),
                bold=True,
                color=DARK_GREEN,
                size_hint_x=width,
                halign="left",
                valign="middle",
            )
            lbl.bind(
                size=lambda w, *_: setattr(w, "text_size", w.size)
            )
            self.add_widget(lbl)


class AdminReportsScreen(Screen):
    NAV_ROUTES = {
        0: "admin_dashboard",
        1: "admin_map",
        2: "admin_panel",
        3: "admin_profile",
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._loading = False
        self._refresh_event = None

        root = BoxLayout(orientation="vertical")

        with root.canvas.before:
            Color(*BG)
            self.root_bg = Rectangle(pos=root.pos, size=root.size)

        root.bind(
            pos=lambda w, *_: setattr(self.root_bg, "pos", w.pos),
            size=lambda w, *_: setattr(self.root_bg, "size", w.size)
        )

        root.add_widget(
            PanelHeader("View Reports", on_back=self._go_back)
        )

        self.status = Label(
            text="Loading Firebase report...",
            font_size=sp(10),
            color=(.35, .35, .35, 1),
            size_hint_y=None,
            height=dp(25),
            halign="center",
            valign="middle",
        )
        self.status.bind(
            size=lambda w, *_: setattr(w, "text_size", w.size)
        )
        root.add_widget(self.status)

        scroll = ScrollView(do_scroll_x=False)

        content = GridLayout(
            cols=1,
            padding=(dp(16), dp(8), dp(16), dp(16)),
            spacing=dp(10),
            size_hint_y=None,
        )
        content.bind(minimum_height=content.setter("height"))

        scroll.add_widget(content)
        self.content = content

        stats = GridLayout(
            cols=2,
            spacing=dp(9),
            size_hint_y=None,
            height=dp(146)
        )

        self.cards = {
            "bins": StatCard("Total Bins"),
            "staff": StatCard("Total Staff"),
            "assigned": StatCard("Assigned Bins"),
            "pending": StatCard("Pending Bins"),
        }

        for card in self.cards.values():
            stats.add_widget(card)

        content.add_widget(stats)

        self.summary = Label(
            text="",
            font_size=sp(11.5),
            color=TEXT_DARK,
            size_hint_y=None,
            height=dp(52),
            halign="left",
            valign="middle",
        )
        self.summary.bind(
            size=lambda w, *_: setattr(w, "text_size", w.size)
        )
        content.add_widget(self.summary)

        title = Label(
            text="Bin Status",
            font_size=sp(14),
            bold=True,
            color=DARK_GREEN,
            size_hint_y=None,
            height=dp(28),
            halign="left",
        )
        title.bind(
            size=lambda w, *_: setattr(w, "text_size", w.size)
        )
        content.add_widget(title)

        # Table header
        content.add_widget(ReportHeader())

        self.bin_rows = GridLayout(
            cols=1,
            spacing=dp(6),
            size_hint_y=None
        )
        self.bin_rows.bind(
            minimum_height=self.bin_rows.setter("height")
        )
        content.add_widget(self.bin_rows)

        self.refresh_btn = Button(
            text="REFRESH REPORT",
            size_hint_y=None,
            height=dp(46),
            font_size=sp(13),
            bold=True,
            color=WHITE,
            background_normal="",
            background_color=DARK_GREEN,
        )
        self.refresh_btn.bind(
            on_release=lambda *_: self.load_report()
        )
        content.add_widget(self.refresh_btn)

        root.add_widget(scroll)

        nav = BottomNav(on_nav=self._on_nav)

        for i, btn in enumerate(nav.buttons):
            btn.set_active(i == 2)

        root.add_widget(nav)

        self.add_widget(root)

    def on_enter(self, *args):
        self.load_report()

        if self._refresh_event is None:
            self._refresh_event = Clock.schedule_interval(
                lambda dt: self.load_report(),
                10
            )

    def on_leave(self, *args):
        if self._refresh_event is not None:
            self._refresh_event.cancel()
            self._refresh_event = None

    def load_report(self, *_):
        if self._loading or get_data is None:
            if get_data is None:
                self.status.text = "Firebase service unavailable"
            return

        self._loading = True
        self.status.text = "Loading live Firebase data..."

        threading.Thread(
            target=self._worker,
            daemon=True
        ).start()

    def _worker(self):
        try:
            bins = records(read_first(BIN_PATHS))
            staff = records(read_first(STAFF_PATHS))
            assignments = records(read_first(ASSIGNMENT_PATHS))

            assigned_ids = set()
            collected = 0
            pending = 0

            for a in assignments:
                bid = str(
                    a.get("bin_id")
                    or a.get("binId")
                    or ""
                ).strip()

                if bid:
                    assigned_ids.add(bid)

                st = str(
                    a.get("status")
                    or "assigned"
                ).lower()

                if st in ("collected", "completed", "done"):
                    collected += 1
                else:
                    pending += 1

            # Also count bins carrying assignment information directly.
            for b in bins:
                bid = str(
                    b.get("bin_id")
                    or b.get("_id")
                    or ""
                ).strip()

                if (
                    b.get("assigned_worker_id")
                    or b.get("assigned_worker_uid")
                ):
                    if bid:
                        assigned_ids.add(bid)

            full = 0
            half = 0
            empty = 0
            bin_data = []

            for b in bins:
                bid = str(
                    b.get("bin_id")
                    or b.get("_id")
                    or "-"
                )

                name = str(
                    b.get("name")
                    or b.get("bin_name")
                    or bid
                )

                raw_fill = b.get(
                    "fill_level",
                    b.get("fillLevel", 0)
                )

                try:
                    fill = float(raw_fill)
                except Exception:
                    fill = 0

                if fill >= 80:
                    full += 1
                    status = "Full"
                elif fill >= 40:
                    half += 1
                    status = "Medium"
                else:
                    empty += 1
                    status = "Low"

                explicit = str(
                    b.get("status") or ""
                ).strip()

                if explicit:
                    status = explicit.title()

                bin_data.append(
                    (
                        bid,
                        name,
                        f"{fill:g}%",
                        status,
                    )
                )

            bin_data.sort(key=lambda x: x[0])

            payload = {
                "bins": len(bins),
                "staff": len(staff),
                "assigned": len(assigned_ids),
                "pending": pending,
                "collected": collected,
                "full": full,
                "half": half,
                "empty": empty,
                "rows": bin_data,
            }

            Clock.schedule_once(
                lambda dt, p=payload: self._apply(p),
                0
            )

        except Exception as exc:
            print("[REPORTS] Worker error:", exc)

            Clock.schedule_once(
                lambda dt, e=str(exc): self._error(e),
                0
            )

        finally:
            self._loading = False

    def _apply(self, p):
        self.status.text = (
            f"Firebase Connected  •  "
            f"{p['bins']} Bins  •  {p['staff']} Staff"
        )
        self.status.color = (.18, .50, .30, 1)

        self.cards["bins"].value_lbl.text = str(p["bins"])
        self.cards["staff"].value_lbl.text = str(p["staff"])
        self.cards["assigned"].value_lbl.text = str(p["assigned"])
        self.cards["pending"].value_lbl.text = str(p["pending"])

        self.summary.text = (
            f"Collected: {p['collected']}    •    "
            f"Full: {p['full']}    •    "
            f"Medium: {p['half']}    •    "
            f"Low: {p['empty']}"
        )

        self.bin_rows.clear_widgets()

        if not p["rows"]:
            self.bin_rows.add_widget(
                Label(
                    text="No bins found in Firebase.",
                    font_size=sp(11),
                    color=(.45, .45, .45, 1),
                    size_hint_y=None,
                    height=dp(40),
                )
            )
        else:
            for row in p["rows"]:
                # row = (bin_id, name, fill_level, status)
                self.bin_rows.add_widget(
                    ReportRow(*row)
                )

    def _error(self, error):
        self.status.text = "Firebase report error"
        self.status.color = (.8, .15, .15, 1)
        self.summary.text = (
            f"Could not load report data. {error}"
        )

    def _on_nav(self, index):
        target = self.NAV_ROUTES.get(index)

        if self.manager and target in self.manager.screen_names:
            self.manager.current = target

    def _go_back(self):
        self._on_nav(2)


if __name__ == "__main__":
    pass
