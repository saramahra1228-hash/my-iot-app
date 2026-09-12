"""Admin -> Assign Worker screen with Firebase Realtime Database integration."""
import threading
from datetime import datetime, timezone

from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.uix.button import Button
from kivy.uix.spinner import Spinner
from kivy.clock import Clock
from kivy.metrics import dp, sp
from kivy.graphics import Color, Rectangle

from firebase_config import get_data, update_data

DARK_GREEN = (0.0, 0.302, 0.204, 1)
WHITE = (1, 1, 1, 1)
TEXT_DARK = (0.12, 0.12, 0.12, 1)
GRAY = (0.45, 0.45, 0.45, 1)
RED = (0.80, 0.15, 0.15, 1)
GREEN = (0.18, 0.50, 0.30, 1)


def _records(data):
    if isinstance(data, list):
        return [dict(x, _id=str(i)) for i, x in enumerate(data) if isinstance(x, dict)]
    if isinstance(data, dict):
        out = []
        for key, value in data.items():
            if isinstance(value, dict):
                item = dict(value)
                item["_id"] = str(key)
                out.append(item)
        return out
    return []


class AssignWorkerScreen(Screen):
    """Select a bin + registered staff member and save an assignment."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bin_records = []
        self.staff_records = []

        root = BoxLayout(orientation="vertical")
        with root.canvas.before:
            Color(*WHITE)
            self._bg = Rectangle(pos=root.pos, size=root.size)
        root.bind(pos=self._sync_bg, size=self._sync_bg)

        header = BoxLayout(size_hint_y=None, height=dp(60), padding=(dp(16), 0))
        with header.canvas.before:
            Color(*DARK_GREEN)
            self._header_bg = Rectangle(pos=header.pos, size=header.size)
        header.bind(pos=self._sync_header, size=self._sync_header)

        back = Button(text="‹", font_size=sp(28), color=WHITE, background_normal="",
                      background_color=(0, 0, 0, 0), size_hint_x=None, width=dp(45))
        back.bind(on_release=self._go_back)
        header.add_widget(back)
        title = Label(text="Assign Worker", font_size=sp(19), bold=True, color=WHITE)
        header.add_widget(title)
        header.add_widget(Widget(size_hint_x=None, width=dp(45)))
        root.add_widget(header)

        scroll = ScrollView(do_scroll_x=False)
        content = BoxLayout(orientation="vertical", size_hint_y=None, padding=(dp(22), dp(20)), spacing=dp(12))
        content.bind(minimum_height=content.setter("height"))
        scroll.add_widget(content)

        intro = Label(text="Assign a registered staff member to a waste bin.", font_size=sp(12), color=GRAY,
                      size_hint_y=None, height=dp(38), halign="left", valign="middle")
        intro.bind(size=lambda w, *_: setattr(w, "text_size", w.size))
        content.add_widget(intro)

        content.add_widget(self._label("SELECT BIN"))
        self.bin_spinner = Spinner(text="Loading bins...", values=(), size_hint_y=None, height=dp(46),
                                   font_size=sp(13), background_normal="", background_color=(0.93, 0.96, 0.94, 1),
                                   color=TEXT_DARK)
        content.add_widget(self.bin_spinner)

        content.add_widget(self._label("SELECT WORKER"))
        self.worker_spinner = Spinner(text="Loading workers...", values=(), size_hint_y=None, height=dp(46),
                                      font_size=sp(13), background_normal="", background_color=(0.93, 0.96, 0.94, 1),
                                      color=TEXT_DARK)
        content.add_widget(self.worker_spinner)

        self.status_lbl = Label(text="", font_size=sp(11), color=RED, size_hint_y=None, height=dp(42),
                                halign="center", valign="middle")
        self.status_lbl.bind(size=lambda w, *_: setattr(w, "text_size", w.size))
        content.add_widget(self.status_lbl)

        save = Button(text="ASSIGN WORKER", font_size=sp(14), bold=True, color=WHITE, background_normal="",
                      background_color=DARK_GREEN, size_hint_y=None, height=dp(48))
        save.bind(on_release=self._assign_worker)
        content.add_widget(save)
        content.add_widget(Widget())

        root.add_widget(scroll)
        self.add_widget(root)

    def _sync_bg(self, w, *_):
        self._bg.pos, self._bg.size = w.pos, w.size

    def _sync_header(self, w, *_):
        self._header_bg.pos, self._header_bg.size = w.pos, w.size

    def _label(self, text):
        return Label(text=text, font_size=sp(11), bold=True, color=TEXT_DARK, size_hint_y=None,
                     height=dp(22), halign="left", valign="middle")

    def on_pre_enter(self, *_):
        self._load_data()

    def _load_data(self):
        self.status_lbl.text = "Loading bins and workers..."
        self.status_lbl.color = GRAY
        threading.Thread(target=self._load_worker, daemon=True).start()

    def _load_worker(self):
        try:
            bins_result = get_data("bins")
            staff_result = get_data("staff")
            bins_ok, bins_data = bins_result if isinstance(bins_result, tuple) else (True, bins_result)
            staff_ok, staff_data = staff_result if isinstance(staff_result, tuple) else (True, staff_result)
            if not bins_ok:
                raise RuntimeError(str(bins_data))
            if not staff_ok:
                raise RuntimeError(str(staff_data))
            bins = _records(bins_data)
            staff = _records(staff_data)
            Clock.schedule_once(lambda dt, b=bins, s=staff: self._apply_lists(b, s), 0)
        except Exception as exc:
            Clock.schedule_once(lambda dt, e=str(exc): self._show_error("Unable to load data. Check Firebase connection."), 0)
            print("[ASSIGN WORKER] Load error:", exc)

    def _apply_lists(self, bins, staff):
        self.bin_records = bins
        self.staff_records = staff
        bin_values = []
        for b in bins:
            bid = str(b.get("bin_id") or b.get("_id") or "")
            name = str(b.get("name") or "")
            bin_values.append(f"{bid} - {name}" if name else bid)
        worker_values = []
        for s in staff:
            sid = str(s.get("staff_id") or s.get("_id") or "")
            name = str(s.get("full_name") or s.get("name") or "Staff")
            worker_values.append(f"{sid} - {name}" if sid else name)
        self.bin_spinner.values = tuple(bin_values)
        self.worker_spinner.values = tuple(worker_values)
        self.bin_spinner.text = bin_values[0] if bin_values else "No bins found"
        self.worker_spinner.text = worker_values[0] if worker_values else "No workers found"
        self.status_lbl.text = f"{len(bins)} bins • {len(staff)} workers loaded"
        self.status_lbl.color = GREEN if bins and staff else GRAY

    def _assign_worker(self, *_):
        if not self.bin_records:
            self._show_error("No bins available. Add a bin first.")
            return
        if not self.staff_records:
            self._show_error("No staff members found. Register a worker first.")
            return
        bin_index = self.bin_spinner.values.index(self.bin_spinner.text) if self.bin_spinner.text in self.bin_spinner.values else -1
        staff_index = self.worker_spinner.values.index(self.worker_spinner.text) if self.worker_spinner.text in self.worker_spinner.values else -1
        if bin_index < 0 or staff_index < 0:
            self._show_error("Please select both a bin and a worker.")
            return
        b = self.bin_records[bin_index]
        s = self.staff_records[staff_index]
        bin_id = str(b.get("bin_id") or b.get("_id") or "")
        staff_uid = str(s.get("_id") or "")
        staff_id = str(s.get("staff_id") or staff_uid)
        staff_name = str(s.get("full_name") or s.get("name") or "Staff")
        if not bin_id or not staff_uid:
            self._show_error("Bin or worker ID is missing.")
            return
        self.status_lbl.text = "Assigning worker..."
        self.status_lbl.color = GRAY
        threading.Thread(target=self._save_assignment, args=(bin_id, staff_uid, staff_id, staff_name), daemon=True).start()

    def _save_assignment(self, bin_id, staff_uid, staff_id, staff_name):
        try:
            now = datetime.now(timezone.utc).isoformat()
            assignment_id = f"{bin_id}_{staff_uid}".replace("/", "_")
            assignment = {
                "assignment_id": assignment_id,
                "bin_id": bin_id,
                "staff_uid": staff_uid,
                "staff_id": staff_id,
                "staff_name": staff_name,
                "status": "assigned",
                "assigned_at": now,
                "updated_at": now,
            }
            ok, result = update_data(f"assignments/{assignment_id}", assignment)
            if not ok:
                raise RuntimeError(str(result))

            # Keep the bin record immediately aware of its current worker.
            ok2, result2 = update_data(f"bins/{bin_id}", {
                "assigned_worker_id": staff_id,
                "assigned_worker_uid": staff_uid,
                "assigned_worker_name": staff_name,
                "assignment_status": "assigned",
                "assigned_at": now,
                "updated_at": now,
            })
            if not ok2:
                print("[ASSIGN WORKER] Bin update warning:", result2)

            Clock.schedule_once(lambda dt: self._success(bin_id, staff_name), 0)
        except Exception as exc:
            print("[ASSIGN WORKER] Save error:", exc)
            Clock.schedule_once(lambda dt: self._show_error("Assignment failed. Check Firebase connection."), 0)

    def _success(self, bin_id, staff_name):
        self.status_lbl.text = f"{staff_name} assigned to {bin_id} successfully!"
        self.status_lbl.color = GREEN
        Clock.schedule_once(lambda dt: self._go_back(), 1.0)

    def _show_error(self, message):
        self.status_lbl.text = message
        self.status_lbl.color = RED

    def _go_back(self, *_):
        if self.manager and "admin_panel" in self.manager.screen_names:
            self.manager.current = "admin_panel"
        elif self.manager and "admin_dashboard" in self.manager.screen_names:
            self.manager.current = "admin_dashboard"


if __name__ == "__main__":
    pass
