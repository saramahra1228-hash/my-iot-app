"""
Admin Map View - Firebase Connected + Professional Bin Pins
Updated: reliable Nominatim location search + map centering.
"""

import threading
import urllib.parse

from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.widget import Widget
from kivy.uix.behaviors import ButtonBehavior
from kivy.graphics import Color, Ellipse, Line, RoundedRectangle, Rectangle, Mesh
from kivy.properties import ListProperty
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.network.urlrequest import UrlRequest
from kivy_garden.mapview import MapView, MapMarkerPopup

from admin_dashboard_kivy import BottomNav, WHITE, DARK_GREEN

try:
    from firebase_config import get_data, get_location
except Exception as exc:
    print("[ADMIN MAP] Firebase import failed:", exc)
    get_data = None
    get_location = None

WAH_LAT = 33.7714
WAH_LNG = 72.7518
FIREBASE_REFRESH_SECONDS = 5


class BackArrowIcon(ButtonBehavior, Widget):
    color = ListProperty(list(WHITE))

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(pos=self.redraw, size=self.redraw, color=self.redraw)

    def redraw(self, *_):
        self.canvas.clear()
        with self.canvas:
            Color(*self.color)
            x, y = self.pos
            s = min(self.size)
            ox = x + (self.width - s) / 2
            oy = y + (self.height - s) / 2
            Line(points=[
                ox + .68*s, oy + .15*s,
                ox + .28*s, oy + .50*s,
                ox + .68*s, oy + .85*s
            ], width=dp(1.5), cap="round", joint="round")


class SearchIcon(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(pos=self.redraw, size=self.redraw)

    def redraw(self, *_):
        self.canvas.clear()
        with self.canvas:
            Color(.45, .45, .45, 1)
            s = min(self.size)
            ox = self.x + (self.width-s)/2
            oy = self.y + (self.height-s)/2
            cx, cy, r = ox+.42*s, oy+.58*s, .26*s
            Line(circle=(cx, cy, r), width=dp(1.3))
            Line(points=[
                cx+r*.72, cy-r*.72,
                ox+.86*s, oy+.14*s
            ], width=dp(1.4), cap="round")


class ColorDotMarker(MapMarkerPopup):
    def __init__(self, outside_color, circle_color, marker_kind="bin", **kwargs):
        super().__init__(**kwargs)
        self.marker_kind = marker_kind
        self.outside_color = outside_color
        self.circle_color = circle_color
        self.size = (dp(34), dp(42))
        try:
            self.anchor_x = .5
            self.anchor_y = .12
        except Exception:
            pass
        self.bind(pos=self.sync, size=self.sync)
        self.redraw_marker()

    def redraw_marker(self, *_):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*self.outside_color)
            self.outer = Ellipse()
            Color(*self.outside_color)
            self.point = Mesh(mode="triangles")
            Color(1, 1, 1, 1)
            self.inner = Ellipse()

            if self.marker_kind == "staff":
                self.person_head = Ellipse()
                self.person_body = RoundedRectangle(radius=[dp(3)])
            elif self.marker_kind == "search":
                self.search_dot = Ellipse()
            else:
                self.bin_body = RoundedRectangle(radius=[dp(2)])
                self.bin_lid = RoundedRectangle(radius=[dp(1)])
                self.bin_line1 = Line()
                self.bin_line2 = Line()
        self.sync()

    def sync(self, *_):
        x, y = self.pos
        w, h = self.size
        head_size = min(w*.82, h*.70)
        head_x = x+(w-head_size)/2
        head_y = y+h*.20

        self.outer.pos = (head_x, head_y)
        self.outer.size = (head_size, head_size)

        cx = x+w/2
        bottom_y = y+h*.02
        left_x = cx-head_size*.31
        right_x = cx+head_size*.31
        self.point.vertices = [
            left_x, head_y+head_size*.23, 0, 0,
            right_x, head_y+head_size*.23, 0, 0,
            cx, bottom_y, 0, 0
        ]
        self.point.indices = [0, 1, 2]

        inner_size = head_size*.52
        self.inner.size = (inner_size, inner_size)
        self.inner.pos = (
            cx-inner_size/2,
            head_y+head_size/2-inner_size/2
        )

        if self.marker_kind == "staff":
            ph = inner_size*.23
            self.person_head.size = (ph, ph)
            self.person_head.pos = (
                cx-ph/2,
                self.inner.pos[1]+inner_size*.54
            )
            bw, bh = inner_size*.38, inner_size*.31
            self.person_body.size = (bw, bh)
            self.person_body.pos = (
                cx-bw/2,
                self.inner.pos[1]+inner_size*.18
            )

        elif self.marker_kind == "search":
            d = inner_size*.30
            self.search_dot.size = (d, d)
            self.search_dot.pos = (cx-d/2, self.inner.pos[1]+inner_size*.35)

        else:
            bw, bh = inner_size*.34, inner_size*.38
            self.bin_body.size = (bw, bh)
            self.bin_body.pos = (
                cx-bw/2,
                self.inner.pos[1]+inner_size*.18
            )
            lid_w = inner_size*.46
            lid_h = max(dp(2), inner_size*.075)
            self.bin_lid.size = (lid_w, lid_h)
            self.bin_lid.pos = (
                cx-lid_w/2,
                self.inner.pos[1]+inner_size*.58
            )
            self.bin_line1.points = [
                cx-bw*.20, self.inner.pos[1]+inner_size*.25,
                cx-bw*.20, self.inner.pos[1]+inner_size*.48
            ]
            self.bin_line2.points = [
                cx+bw*.20, self.inner.pos[1]+inner_size*.25,
                cx+bw*.20, self.inner.pos[1]+inner_size*.48
            ]

    def set_colors(self, outside_color, circle_color):
        self.outside_color = outside_color
        self.circle_color = circle_color
        self.redraw_marker()


class SearchMarker(ColorDotMarker):
    def __init__(self, **kwargs):
        super().__init__(
            outside_color=(211/255, 47/255, 47/255, 1),
            circle_color=(1, 1, 1, 1),
            marker_kind="search",
            **kwargs
        )
        self.size = (dp(34), dp(42))


class SearchButton(ButtonBehavior, Widget):
    def __init__(self, callback, **kwargs):
        super().__init__(size_hint=(None, 1), width=dp(30), **kwargs)
        self.callback = callback
        self.icon = SearchIcon()
        self.add_widget(self.icon)
        self.bind(pos=self._sync, size=self._sync)

    def _sync(self, *_):
        self.icon.pos = self.pos
        self.icon.size = self.size

    def on_release(self):
        self.callback()


class MapScreenAdmin(Screen):
    BIN_PATHS = ("bins", "waste_bins", "bin_data", "smart_bins", "bin")
    STAFF_PATHS = ("staff_locations", "staff", "workers", "users")

    NAV_ROUTES = {
        0: "admin_dashboard",
        1: "admin_map",
        2: "admin_panel",
        3: "admin_profile"
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.bin_markers = {}
        self.staff_markers = {}
        self.search_marker = None

        # Current UrlRequest and a monotonically increasing search token
        # prevent an old result from moving the map after a newer search.
        self._search_request = None
        self._search_token = 0
        self._last_search_query = ""

        self.refresh_event = None
        self._firebase_refresh_running = False
        self._map_screen_active = False
        self._refresh_lock = threading.Lock()

        root = BoxLayout(orientation="vertical")

        header = FloatLayout(size_hint=(1, None), height=dp(60))
        self.paint_bg(header, DARK_GREEN)

        back = BackArrowIcon(
            size_hint=(None, None),
            size=(dp(20), dp(20)),
            pos_hint={"x": .045, "center_y": .5}
        )
        back.bind(on_release=lambda *_: self._go_back())
        header.add_widget(back)

        title = Label(
            text="Map View",
            font_size="19sp",
            bold=True,
            color=WHITE,
            pos_hint={"center_x": .5, "center_y": .5},
            size_hint=(None, None),
            size=(dp(220), dp(30)),
            halign="center",
            valign="middle"
        )
        title.bind(size=lambda w, *_: setattr(w, "text_size", w.size))
        header.add_widget(title)
        root.add_widget(header)

        container = FloatLayout()

        self.map_widget = MapView(
            zoom=15,
            lat=WAH_LAT,
            lon=WAH_LNG
        )
        container.add_widget(self.map_widget)

        backdrop = Widget(
            size_hint=(1, None),
            height=dp(70),
            pos_hint={"top": 1}
        )
        self.paint_bg(backdrop, (1, 1, 1, 1))
        container.add_widget(backdrop)
        container.add_widget(self.build_search())
        container.add_widget(self.build_legend())

        root.add_widget(container)

        nav = BottomNav(on_nav=self._on_nav)
        for i, button in enumerate(nav.buttons):
            button.set_active(i == 1)
        root.add_widget(nav)

        self.add_widget(root)

    def on_pre_enter(self, *_):
        self._map_screen_active = True
        Clock.schedule_once(lambda dt: self._start_firebase_refresh(), .2)

        if self.refresh_event is None:
            self.refresh_event = Clock.schedule_interval(
                lambda dt: self._start_firebase_refresh(),
                FIREBASE_REFRESH_SECONDS
            )

    def on_leave(self, *_):
        self._map_screen_active = False

        if self.refresh_event is not None:
            self.refresh_event.cancel()
            self.refresh_event = None

        # Invalidate any outstanding search response.
        self._search_token += 1
        self._search_request = None

    def _start_firebase_refresh(self):
        if not self._map_screen_active:
            return

        if get_data is None:
            print("[ADMIN MAP] Firebase get_data is unavailable.")
            return

        with self._refresh_lock:
            if self._firebase_refresh_running:
                return
            self._firebase_refresh_running = True

        threading.Thread(
            target=self._firebase_worker,
            daemon=True
        ).start()

    def _firebase_worker(self):
        try:
            bins = self.read_first(self.BIN_PATHS)
            staff = self.read_first(self.STAFF_PATHS)

            if staff is None and get_location is not None:
                try:
                    lat, lng = get_location("staff_1")
                    if lat is not None and lng is not None:
                        staff = {
                            "staff_1": {
                                "latitude": lat,
                                "longitude": lng
                            }
                        }
                except Exception as exc:
                    print("[ADMIN MAP] get_location fallback failed:", exc)

            Clock.schedule_once(
                lambda dt, b=bins, s=staff:
                self._apply_firebase_data(b, s),
                0
            )

        except Exception as exc:
            print("[ADMIN MAP] Firebase worker failed:", exc)
            Clock.schedule_once(
                lambda dt, err=str(exc): self._firebase_error_ui(err), 0
            )
        finally:
            with self._refresh_lock:
                self._firebase_refresh_running = False

    def _apply_firebase_data(self, bins, staff):
        if not self._map_screen_active:
            return
        try:
            self.update_bins(bins)
            self.update_staff(staff)
        except Exception as exc:
            print("[ADMIN MAP] UI update failed:", exc)

    @staticmethod
    def _firebase_error_ui(error):
        print("[ADMIN MAP] Firebase connection error:", error)

    def refresh_firebase(self):
        self._start_firebase_refresh()

    @staticmethod
    def paint_bg(widget, color):
        with widget.canvas.before:
            Color(*color)
            widget.bg = Rectangle(pos=widget.pos, size=widget.size)
        widget.bind(
            pos=lambda w, *_: setattr(w.bg, "pos", w.pos),
            size=lambda w, *_: setattr(w.bg, "size", w.size)
        )

    def build_search(self):
        bar = BoxLayout(
            size_hint=(.94, None),
            height=dp(50),
            pos_hint={"center_x": .5, "top": 1},
            padding=(dp(14), 0),
            spacing=dp(8)
        )

        with bar.canvas.before:
            Color(1, 1, 1, 1)
            bar.bg = RoundedRectangle(
                pos=bar.pos,
                size=bar.size,
                radius=[dp(25)]
            )
            Color(0, 0, 0, .12)
            bar.border = Line(
                rounded_rectangle=(
                    bar.x, bar.y, bar.width, bar.height, dp(25)
                ),
                width=1
            )

        bar.bind(pos=self.sync_search, size=self.sync_search)

        self.search_input = TextInput(
            hint_text="Search a location...",
            multiline=False,
            background_color=(0, 0, 0, 0),
            foreground_color=(.1, .1, .1, 1),
            padding=(0, dp(11)),
            font_size="15sp",
            write_tab=False
        )
        self.search_input.bind(on_text_validate=lambda *_: self.search_location())
        bar.add_widget(self.search_input)
        bar.add_widget(SearchButton(self.search_location))
        return bar

    def build_legend(self):
        legend = BoxLayout(
            orientation="vertical",
            size_hint=(None, None),
            size=(dp(118), dp(88)),
            pos_hint={"right": .97, "y": .08},
            padding=(dp(8), dp(6)),
            spacing=dp(3)
        )

        with legend.canvas.before:
            Color(1, 1, 1, .94)
            legend.bg = RoundedRectangle(
                pos=legend.pos, size=legend.size, radius=[dp(10)]
            )
            Color(0, 0, 0, .10)
            legend.border = Line(
                rounded_rectangle=(
                    legend.x, legend.y, legend.width, legend.height, dp(10)
                ), width=1
            )

        title = Label(
            text="Bin status",
            font_size="11sp",
            bold=True,
            color=(.12, .12, .12, 1),
            size_hint_y=None,
            height=dp(16),
            halign="left"
        )
        title.bind(size=lambda w, *_: setattr(w, "text_size", w.size))
        legend.add_widget(title)

        for text, color in (
            ("Empty / Low", (46/255, 125/255, 50/255, 1)),
            ("Half", (255/255, 193/255, 7/255, 1)),
            ("Full", (211/255, 47/255, 47/255, 1)),
        ):
            row = BoxLayout(
                orientation="horizontal",
                size_hint_y=None,
                height=dp(17),
                spacing=dp(5)
            )
            dot = Widget(size_hint=(None, None), size=(dp(10), dp(10)))
            with dot.canvas:
                Color(*color)
                dot.shape = Ellipse(pos=dot.pos, size=dot.size)
            dot.bind(
                pos=lambda w, *_: setattr(w.shape, "pos", w.pos),
                size=lambda w, *_: setattr(w.shape, "size", w.size)
            )
            row.add_widget(dot)

            label = Label(
                text=text,
                font_size="9sp",
                color=(.25, .25, .25, 1),
                halign="left"
            )
            label.bind(size=lambda w, *_: setattr(w, "text_size", w.size))
            row.add_widget(label)
            legend.add_widget(row)

        legend.bind(
            pos=lambda w, *_: self._sync_legend(w),
            size=lambda w, *_: self._sync_legend(w)
        )
        self._sync_legend(legend)
        return legend

    @staticmethod
    def _sync_legend(legend):
        legend.bg.pos = legend.pos
        legend.bg.size = legend.size
        legend.border.rounded_rectangle = (
            legend.x, legend.y, legend.width, legend.height, dp(10)
        )

    @staticmethod
    def sync_search(bar, *_):
        bar.bg.pos = bar.pos
        bar.bg.size = bar.size
        bar.border.rounded_rectangle = (
            bar.x, bar.y, bar.width, bar.height, dp(25)
        )

    # ------------------------------------------------------------------
    # FIXED SEARCH
    # ------------------------------------------------------------------

    def _remove_search_marker(self):
        marker = self.search_marker
        self.search_marker = None

        if marker is not None:
            try:
                self.map_widget.remove_marker(marker)
            except Exception:
                pass

    def _start_nominatim_request(self, query, token):
        encoded = urllib.parse.quote(query, safe="")
        url = (
            "https://nominatim.openstreetmap.org/search"
            f"?format=json&limit=5&addressdetails=1&q={encoded}"
        )

        self._search_request = UrlRequest(
            url,
            on_success=lambda req, result, t=token, q=query:
                self.search_ok(req, result, t, q),
            on_failure=lambda req, error, t=token:
                self.search_failed(req, error, t),
            on_error=lambda req, error, t=token:
                self.search_failed(req, error, t),
            req_headers={
                "User-Agent": "SmartWasteAdminApp/1.0 (admin map)"
            },
            timeout=15
        )

    def search_location(self):
        query = self.search_input.text.strip()

        if not query:
            print("[ADMIN MAP] Please enter a location.")
            return

        # A new search always gets a new token. This is important because
        # Nominatim responses can arrive out of order.
        self._search_token += 1
        token = self._search_token
        self._last_search_query = query

        # Invalidate the Python reference to an older request. UrlRequest
        # cancellation is not consistently available across Kivy versions,
        # so stale callbacks are rejected by the token check.
        self._search_request = None

        print("[ADMIN MAP] Searching:", query)

        # First try exactly what the user typed.
        self._start_nominatim_request(query, token)

    def search_ok(self, request, result, token=None, original_query=None):
        if token is None:
            token = self._search_token
        if original_query is None:
            original_query = self.search_input.text.strip()

        # Ignore old/out-of-order responses.
        if token != self._search_token:
            print("[ADMIN MAP] Ignoring stale search response.")
            return

        self._search_request = None

        if not result:
            # Retry with Pakistan context. This greatly improves results for
            # local names such as Taxila, Wah Cantt, Rawalpindi, etc.
            if not original_query.lower().endswith("pakistan"):
                retry_query = original_query + ", Pakistan"
                print("[ADMIN MAP] Retrying search as:", retry_query)
                self._start_nominatim_request(retry_query, token)
                return

            print("[ADMIN MAP] Location not found:", original_query)
            return

        chosen = None

        for item in result:
            try:
                lat = float(item["lat"])
                lon = float(item["lon"])

                if -90 <= lat <= 90 and -180 <= lon <= 180:
                    chosen = (lat, lon)
                    break
            except (KeyError, TypeError, ValueError):
                continue

        if chosen is None:
            print("[ADMIN MAP] Nominatim returned no valid coordinates.")
            return

        lat, lon = chosen
        print(f"[ADMIN MAP] Found location: {lat}, {lon}")

        # Remove old search pin before moving/adding the new one.
        self._remove_search_marker()

        # Set both properties AND use center_on. Different MapView versions
        # react more reliably when both are supplied.
        try:
            self.map_widget.lat = lat
            self.map_widget.lon = lon
            self.map_widget.zoom = 16
            self.map_widget.center_on(lat, lon)
        except Exception as exc:
            print("[ADMIN MAP] Map centering failed:", exc)
            try:
                self.map_widget.lat = lat
                self.map_widget.lon = lon
                self.map_widget.zoom = 16
            except Exception as inner_exc:
                print("[ADMIN MAP] Map position update failed:", inner_exc)

        try:
            self.search_marker = SearchMarker(lat=lat, lon=lon)
            self.map_widget.add_marker(self.search_marker)

            # Re-center once more after marker insertion. This prevents
            # marker/layout updates from leaving the map at the old center.
            Clock.schedule_once(
                lambda dt, la=lat, lo=lon: self._finalize_search_center(la, lo),
                0.15
            )
        except Exception as exc:
            self.search_marker = None
            print("[ADMIN MAP] Search pin render failed:", exc)

    def _finalize_search_center(self, lat, lon):
        if not self._map_screen_active:
            return

        try:
            self.map_widget.lat = lat
            self.map_widget.lon = lon
            self.map_widget.zoom = 16
            self.map_widget.center_on(lat, lon)
        except Exception as exc:
            print("[ADMIN MAP] Final map centering failed:", exc)

    def search_failed(self, request, error, token=None):
        if token is None:
            token = self._search_token

        if token != self._search_token:
            return

        self._search_request = None
        print("[ADMIN MAP] Search failed:", error)

    # ------------------------------------------------------------------
    # FIREBASE DATA HELPERS
    # ------------------------------------------------------------------

    @staticmethod
    def unwrap(response):
        if isinstance(response, tuple) and len(response) == 2:
            return response
        return True, response

    def read_first(self, paths):
        if get_data is None:
            return None

        for path in paths:
            try:
                ok, data = self.unwrap(get_data(path))
                if not ok:
                    print(f"[ADMIN MAP] {path}: {data}")
                    continue
                if data not in (None, {}, []):
                    print(f"[ADMIN MAP] Loaded Firebase path: {path}")
                    return data
            except Exception as exc:
                print(f"[ADMIN MAP] {path} error:", exc)
        return None

    @staticmethod
    def coords(record):
        if not isinstance(record, dict):
            return None

        candidates = [record]
        for key in ("location", "coordinates", "position", "gps"):
            if isinstance(record.get(key), dict):
                candidates.append(record[key])

        for item in candidates:
            lat = item.get("latitude", item.get("lat"))
            lon = item.get("longitude", item.get("lng", item.get("lon")))

            try:
                lat, lon = float(lat), float(lon)
                if -90 <= lat <= 90 and -180 <= lon <= 180:
                    return lat, lon
            except (TypeError, ValueError):
                pass

        return None

    @classmethod
    def records(cls, data):
        if isinstance(data, list):
            return [(str(i), x) for i, x in enumerate(data) if isinstance(x, dict)]

        if isinstance(data, dict):
            if cls.coords(data):
                return [(
                    str(data.get("id") or data.get("bin_id") or "record_1"),
                    data
                )]
            return [
                (str(k), v) for k, v in data.items() if isinstance(v, dict)
            ]

        return []

    @staticmethod
    def fill_level(record):
        for key in (
            "fill_level", "fillLevel", "fill_percentage",
            "fillPercentage", "percentage", "level", "fill"
        ):
            try:
                value = record.get(key)
                if value is not None:
                    value = float(value)
                    if 0 <= value <= 1:
                        return value * 100
                    return max(0, min(100, value))
            except (TypeError, ValueError):
                pass
        return None

    @classmethod
    def state(cls, record):
        text = str(
            record.get("status")
            or record.get("bin_status")
            or record.get("binStatus")
            or record.get("state")
            or ""
        ).lower()

        if any(x in text for x in ("full", "critical", "overflow")):
            return "full"
        if any(x in text for x in ("half", "warning", "medium", "partial")):
            return "half"
        if any(x in text for x in ("empty", "low", "available")):
            return "empty"

        level = cls.fill_level(record)
        if level is not None:
            if level >= 80:
                return "full"
            if level >= 40:
                return "half"
            return "empty"
        return "unknown"

    @staticmethod
    def colors(state):
        if state == "full":
            return (
                (211/255, 47/255, 47/255, 1),
                (183/255, 28/255, 28/255, 1)
            )
        if state == "half":
            return (
                (255/255, 193/255, 7/255, 1),
                (245/255, 166/255, 0/255, 1)
            )
        return (
            (46/255, 125/255, 50/255, 1),
            (27/255, 94/255, 32/255, 1)
        )

    def update_bins(self, data):
        active = set()

        for fallback_id, record in self.records(data):
            point = self.coords(record)
            if point is None:
                print(f"[ADMIN MAP] Bin {fallback_id} has no valid coordinates.")
                continue

            bin_id = str(
                record.get("id")
                or record.get("bin_id")
                or record.get("binId")
                or fallback_id
            )
            active.add(bin_id)

            state = self.state(record)
            outer, inner = self.colors(state)
            old = self.bin_markers.get(bin_id)

            if old is not None:
                try:
                    old.lat, old.lon = point
                    self.map_widget.set_marker(old)
                    old.set_colors(outer, inner)
                    continue
                except Exception:
                    try:
                        self.map_widget.remove_marker(old)
                    except Exception:
                        pass

            marker = ColorDotMarker(
                outside_color=outer,
                circle_color=inner,
                marker_kind="bin",
                lat=point[0],
                lon=point[1]
            )
            self.map_widget.add_marker(marker)
            self.bin_markers[bin_id] = marker

        for bin_id in list(self.bin_markers):
            if bin_id not in active:
                try:
                    self.map_widget.remove_marker(self.bin_markers[bin_id])
                except Exception:
                    pass
                self.bin_markers.pop(bin_id, None)

        print("[ADMIN MAP] Bins currently on map:", len(self.bin_markers))

    def staff_locations(self, data):
        found = {}

        def walk(value, path=""):
            if not isinstance(value, dict):
                return

            point = self.coords(value)
            if point:
                sid = str(
                    value.get("staff_id")
                    or value.get("staffId")
                    or value.get("user_id")
                    or value.get("userId")
                    or value.get("id")
                    or path.split("/")[-1]
                    or "staff_1"
                )
                found[sid] = point

            for key, child in value.items():
                if isinstance(child, dict):
                    child_path = f"{path}/{key}" if path else str(key)
                    walk(child, child_path)

        walk(data)
        return found

    def update_staff(self, data):
        locations = self.staff_locations(data)
        active = set(locations)

        for sid, point in locations.items():
            old = self.staff_markers.get(sid)

            if old is not None:
                try:
                    old.lat, old.lon = point
                    self.map_widget.set_marker(old)
                    continue
                except Exception:
                    try:
                        self.map_widget.remove_marker(old)
                    except Exception:
                        pass

            marker = ColorDotMarker(
                outside_color=(57/255, 169/255, 107/255, 1),
                circle_color=DARK_GREEN,
                marker_kind="staff",
                lat=point[0],
                lon=point[1]
            )
            self.map_widget.add_marker(marker)
            self.staff_markers[sid] = marker

        for sid in list(self.staff_markers):
            if sid not in active:
                try:
                    self.map_widget.remove_marker(self.staff_markers[sid])
                except Exception:
                    pass
                self.staff_markers.pop(sid, None)

        print("[ADMIN MAP] Staff currently on map:", len(self.staff_markers))

    def _on_nav(self, index):
        target = self.NAV_ROUTES.get(index)

        if not target or target == self.name:
            return
        if self.manager is None:
            print("[ADMIN MAP] No ScreenManager")
            return
        if target not in self.manager.screen_names:
            print(f"[ADMIN MAP] {target} not registered")
            return

        self.manager.current = target

    def _go_back(self):
        self._on_nav(0)
