"""
Admin Dashboard Screen — Smart Waste Monitor
Firebase-connected version.

FIXES in this version:
1. The Today dropdown uses a real drawn chevron icon, so the arrow is
   visible on Windows/Android and does not depend on a Unicode glyph.
2. The analytics graph starts EMPTY when there is no Firebase collection
   data. No fake/hard-coded graph is shown.
3. If the selected period has no collection data, the graph stays empty
   instead of drawing a misleading line.
4. InfoCard.set_title() is fixed (the previous version referenced a
   title_label that was never stored).
5. The dashboard keeps the same overall design, cards, colours and
   bottom navigation.
"""

from datetime import datetime, timedelta
import math

from kivy.clock import Clock
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.uix.behaviors import ButtonBehavior
from kivy.graphics import Color, RoundedRectangle, Line, Ellipse, Mesh
from kivy.properties import ListProperty, NumericProperty, StringProperty, BooleanProperty
from kivy.metrics import dp, sp
from kivy.utils import get_color_from_hex


# ---------------------------------------------------------------- #
# Firebase helper
# ---------------------------------------------------------------- #
try:
    from firebase_config import get_data
except Exception:
    get_data = None


# ---------------------------------------------------------------- #
# Palette
# ---------------------------------------------------------------- #
BG = get_color_from_hex("#F9F9F9")
DARK_GREEN = get_color_from_hex("#004D34")
HEADER_ICON = get_color_from_hex("#1E3A2F")
CARD_BG = get_color_from_hex("#F2F2F2")
WHITE = get_color_from_hex("#FFFFFF")
TEXT_DARK = get_color_from_hex("#000000")
TEXT_GRAY = get_color_from_hex("#666666")
TEXT_GRAY2 = get_color_from_hex("#555555")

GREEN_BG = get_color_from_hex("#E8F2ED")
GREEN_FG = get_color_from_hex("#004D34")
RED_BG = get_color_from_hex("#FCEBEB")
RED_FG = get_color_from_hex("#D32F2F")
YELLOW_BG = get_color_from_hex("#FFF9E6")
YELLOW_FG = get_color_from_hex("#F57C00")

CHART_FILL = get_color_from_hex("#E2EFE7")
CHART_LINE = get_color_from_hex("#39A96B")
GRID_LINE = get_color_from_hex("#EAEAEA")
AXIS_TEXT = get_color_from_hex("#8A8A8A")
NAV_INACTIVE = get_color_from_hex("#A3C4B7")


# ---------------------------------------------------------------- #
# Basic rounded container
# ---------------------------------------------------------------- #
class RoundedBox(BoxLayout):
    bg_color = ListProperty(list(WHITE))
    radius = NumericProperty(dp(14))

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        with self.canvas.before:
            self._bg_col = Color(*self.bg_color)
            self._bg_rect = RoundedRectangle(
                pos=self.pos,
                size=self.size,
                radius=[self.radius],
            )
        self.bind(pos=self._sync, size=self._sync, bg_color=self._sync_color)

    def _sync(self, *_):
        self._bg_rect.pos = self.pos
        self._bg_rect.size = self.size

    def _sync_color(self, *_):
        self._bg_col.rgba = self.bg_color


# ---------------------------------------------------------------- #
# Vector icons
# ---------------------------------------------------------------- #
class VectorIcon(Widget):
    icon_name = StringProperty("home")
    icon_color = ListProperty(list(TEXT_DARK))
    line_width = NumericProperty(dp(1.6))

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(
            pos=self.redraw,
            size=self.redraw,
            icon_color=self.redraw,
            icon_name=self.redraw,
        )

    def _pt(self, fx, fy):
        x, y = self.pos
        w, h = self.size
        s = min(w, h)
        ox = x + (w - s) / 2.0
        oy = y + (h - s) / 2.0
        return ox + fx * s, oy + fy * s

    def redraw(self, *_):
        self.canvas.clear()
        with self.canvas:
            Color(*self.icon_color)
            name = self.icon_name

            if name == "menu":
                self._draw_menu()
            elif name == "bell":
                self._draw_bell()
            elif name == "trash":
                self._draw_trash()
            elif name == "truck":
                self._draw_truck()
            elif name == "people":
                self._draw_people()
            elif name == "home":
                self._draw_home()
            elif name == "pin":
                self._draw_pin()
            elif name == "people_cog":
                self._draw_people_cog()
            elif name == "person":
                self._draw_person()
            elif name == "chevron_down":
                self._draw_chevron_down()

    def _draw_menu(self):
        for fy in (0.72, 0.5, 0.28):
            p1 = self._pt(0.12, fy)
            p2 = self._pt(0.88, fy)
            Line(points=[*p1, *p2], width=self.line_width, cap="round")

    def _draw_bell(self):
        w = self._pt(1, 0)[0] - self._pt(0, 0)[0]
        bx, by = self._pt(0.22, 0.42)
        bw = self._pt(0.78, 0.42)[0] - bx
        bh = self._pt(0.22, 0.78)[1] - by
        Line(
            ellipse=(bx, by, bw, bh, -90, 90),
            width=self.line_width,
            cap="round",
        )
        left_mid = self._pt(0.22, 0.60)
        right_mid = self._pt(0.78, 0.60)
        base_left = self._pt(0.14, 0.28)
        base_right = self._pt(0.86, 0.28)
        Line(
            points=[*left_mid, *base_left],
            width=self.line_width,
            cap="round",
        )
        Line(
            points=[*right_mid, *base_right],
            width=self.line_width,
            cap="round",
        )
        Line(
            points=[*base_left, *base_right],
            width=self.line_width,
            cap="round",
        )
        Line(
            points=[*self._pt(0.5, 0.78), *self._pt(0.5, 0.87)],
            width=self.line_width,
            cap="round",
        )
        clapper = self._pt(0.5, 0.20)
        r = w * 0.045
        Ellipse(
            pos=(clapper[0] - r, clapper[1] - r),
            size=(2 * r, 2 * r),
        )
        dot_x, dot_y = self._pt(0.80, 0.84)
        Color(*DARK_GREEN)
        dr = w * 0.07
        Ellipse(
            pos=(dot_x - dr, dot_y - dr),
            size=(2 * dr, 2 * dr),
        )

    def _draw_trash(self):
        Line(
            points=[*self._pt(0.30, 0.82), *self._pt(0.70, 0.82)],
            width=self.line_width,
            cap="round",
        )
        Line(
            points=[*self._pt(0.42, 0.86), *self._pt(0.58, 0.86)],
            width=self.line_width,
            cap="round",
        )
        body = [
            self._pt(0.28, 0.78),
            self._pt(0.72, 0.78),
            self._pt(0.66, 0.20),
            self._pt(0.34, 0.20),
        ]
        Line(
            points=[c for pt in body for c in pt],
            width=self.line_width,
            close=True,
            joint="round",
            cap="round",
        )
        Line(
            points=[*self._pt(0.44, 0.68), *self._pt(0.42, 0.32)],
            width=self.line_width * 0.8,
            cap="round",
        )
        Line(
            points=[*self._pt(0.56, 0.68), *self._pt(0.58, 0.32)],
            width=self.line_width * 0.8,
            cap="round",
        )

    def _draw_truck(self):
        x0, y0 = self._pt(0.06, 0.40)
        x1, y1 = self._pt(0.60, 0.68)
        Line(
            rectangle=(x0, y0, x1 - x0, y1 - y0),
            width=self.line_width,
            joint="round",
        )
        cab = [
            self._pt(0.60, 0.40),
            self._pt(0.60, 0.60),
            self._pt(0.78, 0.60),
            self._pt(0.92, 0.44),
            self._pt(0.92, 0.40),
        ]
        Line(
            points=[c for pt in cab for c in pt],
            width=self.line_width,
            close=True,
            joint="round",
            cap="round",
        )
        wr = (self._pt(1, 1)[0] - self._pt(0, 0)[0]) * 0.09
        for fx in (0.24, 0.78):
            cx, cy = self._pt(fx, 0.40)
            Line(circle=(cx, cy, wr), width=self.line_width)

    def _draw_people(self):
        s = self._pt(1, 1)[0] - self._pt(0, 0)[0]
        for fx in (0.36, 0.64):
            cx, cy = self._pt(fx, 0.66)
            Line(circle=(cx, cy, 0.14 * s), width=self.line_width)
        for fx in (0.36, 0.64):
            cx, cy = self._pt(fx, 0.30)
            Line(
                ellipse=(
                    cx - 0.20 * s,
                    cy - 0.10 * s,
                    0.40 * s,
                    0.32 * s,
                    90,
                    270,
                ),
                width=self.line_width,
            )

    def _draw_home(self):
        roof = [
            self._pt(0.10, 0.50),
            self._pt(0.50, 0.86),
            self._pt(0.90, 0.50),
        ]
        Line(
            points=[c for pt in roof for c in pt],
            width=self.line_width,
            joint="round",
            cap="round",
        )
        x0, y0 = self._pt(0.22, 0.16)
        x1, y1 = self._pt(0.78, 0.52)
        Line(
            rectangle=(x0, y0, x1 - x0, y1 - y0),
            width=self.line_width,
            joint="round",
        )
        dx0, dy0 = self._pt(0.42, 0.16)
        dx1, dy1 = self._pt(0.58, 0.36)
        Line(
            rectangle=(dx0, dy0, dx1 - dx0, dy1 - dy0),
            width=self.line_width * 0.85,
        )

    def _draw_pin(self):
        s = self._pt(1, 1)[0] - self._pt(0, 0)[0]
        cx, cy = self._pt(0.5, 0.62)
        Line(circle=(cx, cy, 0.26 * s), width=self.line_width)
        tip = [
            self._pt(0.30, 0.46),
            self._pt(0.50, 0.10),
            self._pt(0.70, 0.46),
        ]
        Line(
            points=[c for pt in tip for c in pt],
            width=self.line_width,
            joint="round",
            cap="round",
        )
        Ellipse(
            pos=(cx - 0.07 * s, cy - 0.07 * s),
            size=(0.14 * s, 0.14 * s),
        )

    def _draw_people_cog(self):
        s = self._pt(1, 1)[0] - self._pt(0, 0)[0]
        cx, cy = self._pt(0.42, 0.62)
        Line(circle=(cx, cy, 0.18 * s), width=self.line_width)
        bx, by = self._pt(0.42, 0.22)
        Line(
            ellipse=(
                bx - 0.26 * s,
                by - 0.10 * s,
                0.52 * s,
                0.38 * s,
                90,
                270,
            ),
            width=self.line_width,
        )
        gx, gy = self._pt(0.76, 0.34)
        Line(circle=(gx, gy, 0.14 * s), width=self.line_width)
        for i in range(6):
            ang = math.radians(i * 60)
            x1 = gx + 0.14 * s * math.cos(ang)
            y1 = gy + 0.14 * s * math.sin(ang)
            x2 = gx + 0.21 * s * math.cos(ang)
            y2 = gy + 0.21 * s * math.sin(ang)
            Line(
                points=[x1, y1, x2, y2],
                width=self.line_width * 0.8,
                cap="round",
            )

    def _draw_person(self):
        s = self._pt(1, 1)[0] - self._pt(0, 0)[0]
        cx, cy = self._pt(0.5, 0.66)
        Line(circle=(cx, cy, 0.18 * s), width=self.line_width)
        bx, by = self._pt(0.5, 0.24)
        Line(
            ellipse=(
                bx - 0.28 * s,
                by - 0.10 * s,
                0.56 * s,
                0.40 * s,
                90,
                270,
            ),
            width=self.line_width,
        )

    def _draw_chevron_down(self):
        # Real vector chevron. This replaces the Unicode "▾" character.
        p1 = self._pt(0.27, 0.63)
        p2 = self._pt(0.50, 0.37)
        p3 = self._pt(0.73, 0.63)
        Line(
            points=[*p1, *p2, *p3],
            width=max(dp(1.8), self.line_width),
            joint="round",
            cap="round",
        )


class IconButton(ButtonBehavior, VectorIcon):
    pass


class PeriodSelector(ButtonBehavior, FloatLayout):
    """Single touch target for the analytics period selector."""

    text = StringProperty("Today")
    on_select = None

    def __init__(self, on_select=None, **kwargs):
        super().__init__(**kwargs)
        self.on_select = on_select

        with self.canvas.before:
            Color(*get_color_from_hex("#E0E0E0"))
            self._bg = RoundedRectangle(
                pos=self.pos,
                size=self.size,
                radius=[dp(9)],
            )

        self.bind(
            pos=self._sync_bg,
            size=self._sync_bg,
        )

        self.label = Label(
            text=self.text,
            font_size=sp(10.5),
            color=get_color_from_hex("#333333"),
            bold=False,
            halign="center",
            valign="middle",
            size_hint=(1, 1),
            text_size=(None, None),
        )
        self.add_widget(self.label)

        self.chevron = VectorIcon(
            icon_name="chevron_down",
            icon_color=list(get_color_from_hex("#333333")),
            line_width=dp(1.7),
            size_hint=(None, None),
            size=(dp(12), dp(12)),
            pos_hint={"right": 0.90, "center_y": 0.5},
        )
        self.add_widget(self.chevron)

        self.bind(text=self._sync_text)

    def _sync_bg(self, *_):
        self._bg.pos = self.pos
        self._bg.size = self.size

    def _sync_text(self, *_):
        self.label.text = self.text

    def on_release(self):
        self.open_menu()

    def open_menu(self):
        content = BoxLayout(
            orientation="vertical",
            spacing=dp(6),
            padding=dp(10),
        )

        popup = Popup(
            title="Select Period",
            content=content,
            size_hint=(None, None),
            size=(dp(220), dp(235)),
            auto_dismiss=True,
            separator_height=dp(1),
        )

        for period in ("Today", "This Week", "This Month"):
            btn = Button(
                text=period,
                font_size=sp(12),
                color=TEXT_DARK,
                background_normal="",
                background_down="",
                background_color=(
                    get_color_from_hex("#DCEFE5")
                    if period == self.text
                    else get_color_from_hex("#F2F2F2")
                ),
                size_hint_y=None,
                height=dp(45),
            )
            btn.bind(
                on_release=lambda instance, p=period:
                self._choose(p, popup)
            )
            content.add_widget(btn)

        popup.open()

    def _choose(self, period, popup):
        self.text = period
        popup.dismiss()
        if self.on_select:
            self.on_select(period)


# ---------------------------------------------------------------- #
# Stat cards
# ---------------------------------------------------------------- #
class StatCard(RoundedBox):
    def __init__(self, icon_name, count, label, icon_bg, icon_fg, **kwargs):
        super().__init__(
            orientation="horizontal",
            bg_color=list(CARD_BG),
            padding=(dp(10), dp(10)),
            spacing=dp(10),
            **kwargs,
        )

        self.count_label = Label(
            text=str(count),
            font_size=sp(17),
            bold=True,
            color=TEXT_DARK,
            halign="left",
            valign="middle",
            size_hint_y=None,
            height=dp(22),
            text_size=(dp(90), dp(22)),
        )

        icon_holder = RoundedBox(
            bg_color=list(icon_bg),
            radius=dp(10),
            size_hint=(None, None),
            size=(dp(38), dp(38)),
        )
        icon_holder.add_widget(
            VectorIcon(
                icon_name=icon_name,
                icon_color=list(icon_fg),
                size_hint=(1, 1),
                line_width=dp(1.6),
            )
        )
        icon_holder.pos_hint = {"center_y": 0.5}

        text_stack = BoxLayout(
            orientation="vertical",
            spacing=dp(2),
        )
        text_stack.add_widget(
            Label(
                text=label,
                font_size=sp(11),
                bold=True,
                color=TEXT_GRAY2,
                halign="left",
                valign="middle",
                size_hint_y=None,
                height=dp(16),
                text_size=(dp(90), dp(16)),
            )
        )
        text_stack.add_widget(self.count_label)

        self.add_widget(icon_holder)
        self.add_widget(text_stack)

    def set_count(self, value):
        self.count_label.text = str(value)


# ---------------------------------------------------------------- #
# Info cards
# ---------------------------------------------------------------- #
class InfoCard(RoundedBox):
    def __init__(self, icon_name, title, value, unit="", **kwargs):
        super().__init__(
            orientation="horizontal",
            bg_color=list(CARD_BG),
            padding=(dp(10), dp(8)),
            spacing=dp(8),
            **kwargs,
        )

        self.title_label = Label(
            text=title,
            font_size=sp(9.5),
            color=TEXT_GRAY2,
            halign="left",
            valign="middle",
            size_hint_y=None,
            height=dp(26),
            text_size=(dp(90), dp(26)),
        )

        self.value_label = Label(
            text=f"{value} {unit}".strip(),
            font_size=sp(14),
            bold=True,
            color=TEXT_DARK,
            halign="left",
            valign="middle",
            size_hint_y=None,
            height=dp(18),
            text_size=(dp(90), dp(18)),
        )

        icon_holder = RoundedBox(
            bg_color=list(GREEN_BG),
            radius=dp(10),
            size_hint=(None, None),
            size=(dp(34), dp(34)),
        )
        icon_holder.add_widget(
            VectorIcon(
                icon_name=icon_name,
                icon_color=list(GREEN_FG),
                line_width=dp(1.5),
            )
        )

        text_stack = BoxLayout(
            orientation="vertical",
            spacing=dp(2),
        )
        text_stack.add_widget(self.title_label)
        text_stack.add_widget(self.value_label)

        self.add_widget(icon_holder)
        self.add_widget(text_stack)

    def set_title(self, title):
        self.title_label.text = title

    def set_value(self, value, unit=""):
        self.value_label.text = f"{value} {unit}".strip()


# ---------------------------------------------------------------- #
# Graph
# ---------------------------------------------------------------- #
def _catmull_rom(points, samples_per_seg=14):
    if len(points) < 3:
        return points

    pts = [points[0]] + list(points) + [points[-1]]
    out = []

    for i in range(1, len(pts) - 2):
        p0, p1, p2, p3 = (
            pts[i - 1],
            pts[i],
            pts[i + 1],
            pts[i + 2],
        )

        for step in range(samples_per_seg):
            t = step / samples_per_seg
            t2 = t * t
            t3 = t2 * t

            x = 0.5 * (
                (2 * p1[0])
                + (-p0[0] + p2[0]) * t
                + (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * t2
                + (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * t3
            )

            y = 0.5 * (
                (2 * p1[1])
                + (-p0[1] + p2[1]) * t
                + (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * t2
                + (-p0[0] + 3 * p1[1] - 3 * p2[1] + p3[1]) * t3
            )

            # Correct the y expression above explicitly.
            y = 0.5 * (
                (2 * p1[1])
                + (-p0[1] + p2[1]) * t
                + (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * t2
                + (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * t3
            )

            out.append((x, y))

    out.append(points[-1])
    return out


class WaveGraph(FloatLayout):
    """
    Graph is intentionally empty when there is no real data.

    The previous version used hard-coded values, which made it look as if
    Firebase already contained collection/bin activity. This version does
    not invent any data.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.data = []
        self.y_ticks = [80, 60, 40, 20, 0]
        self.x_ticks = ["1 AM", "6 AM", "12 PM", "6 PM", "12 AM"]

        self.empty_label = Label(
            text="No collection data for this period",
            font_size=sp(10),
            color=AXIS_TEXT,
            size_hint=(None, None),
            size=(dp(190), dp(20)),
            pos_hint={"center_x": 0.5, "center_y": 0.52},
        )
        self.add_widget(self.empty_label)

        self.y_label_objs = []
        for txt in self.y_ticks:
            lbl = Label(
                text=str(txt),
                font_size=sp(9),
                color=AXIS_TEXT,
                size_hint=(None, None),
                size=(dp(24), dp(14)),
            )
            self.add_widget(lbl)
            self.y_label_objs.append(lbl)

        self.x_label_objs = []
        for txt in self.x_ticks:
            lbl = Label(
                text=txt,
                font_size=sp(9),
                color=AXIS_TEXT,
                size_hint=(None, None),
                size=(dp(46), dp(14)),
            )
            self.add_widget(lbl)
            self.x_label_objs.append(lbl)

        self.bind(pos=self.redraw, size=self.redraw)

    def set_data(self, data, x_ticks=None):
        # Empty/zero data means no graph line.
        if data and any(float(v) > 0 for v in data):
            self.data = list(data)
        else:
            self.data = []

        if x_ticks:
            self.x_ticks = list(x_ticks)

            for label in self.x_label_objs:
                self.remove_widget(label)

            self.x_label_objs = []

            for txt in self.x_ticks:
                lbl = Label(
                    text=txt,
                    font_size=sp(9),
                    color=AXIS_TEXT,
                    size_hint=(None, None),
                    size=(dp(46), dp(14)),
                )
                self.add_widget(lbl)
                self.x_label_objs.append(lbl)

        self.empty_label.opacity = 0 if self.data else 1
        self.redraw()

    def redraw(self, *_):
        self.canvas.before.clear()

        x, y = self.pos
        w, h = self.size

        left = dp(30)
        right = dp(10)
        top = dp(10)
        bottom = dp(22)

        cx0 = x + left
        cx1 = x + w - right
        cy0 = y + bottom
        cy1 = y + h - top

        if cx1 <= cx0 or cy1 <= cy0:
            return

        max_val = max(self.y_ticks)
        self.empty_label.pos = (
            x + (w - self.empty_label.width) / 2.0,
            y + (h - self.empty_label.height) * 0.50,
        )
        self.empty_label.opacity = 0 if self.data else 1

        with self.canvas.before:
            # Grid remains visible even when there is no data.
            for i, val in enumerate(self.y_ticks):
                fy = cy0 + (val / max_val) * (cy1 - cy0)

                Color(*GRID_LINE)
                Line(
                    points=[cx0, fy, cx1, fy],
                    width=1,
                    dash_length=4,
                    dash_offset=4,
                )

                self.y_label_objs[i].pos = (
                    x + 2,
                    fy - dp(7),
                )

            n = len(self.x_ticks)

            if n > 1:
                for i, _ in enumerate(self.x_ticks):
                    fx = cx0 + (i / (n - 1)) * (cx1 - cx0)
                    if i < len(self.x_label_objs):
                        self.x_label_objs[i].pos = (
                            fx - dp(23),
                            cy0 - dp(20),
                        )

            # IMPORTANT: no fabricated line/fill when Firebase has no data.
            if not self.data or sum(float(v) for v in self.data) <= 0:
                return

            n_pts = len(self.data)

            if n_pts == 1:
                raw_points = [
                    (
                        (cx0 + cx1) / 2.0,
                        cy0 + (float(self.data[0]) / max_val) * (cy1 - cy0),
                    )
                ]
            else:
                raw_points = []
                for i, v in enumerate(self.data):
                    fx = cx0 + (i / (n_pts - 1)) * (cx1 - cx0)
                    fy = cy0 + (float(v) / max_val) * (cy1 - cy0)
                    raw_points.append((fx, fy))

            if len(raw_points) >= 3:
                smooth = _catmull_rom(
                    raw_points,
                    samples_per_seg=10,
                )
            else:
                smooth = raw_points

            if len(smooth) < 2:
                return

            verts = []
            for px, py in smooth:
                verts.extend([px, py, 0, 0])
                verts.extend([px, cy0, 0, 0])

            indices = list(range(len(smooth) * 2))

            Color(*CHART_FILL)
            Mesh(
                vertices=verts,
                indices=indices,
                mode="triangle_strip",
            )

            Color(*CHART_LINE)
            flat = [c for pt in smooth for c in pt]
            Line(
                points=flat,
                width=dp(2.2),
                cap="round",
                joint="round",
            )


# ---------------------------------------------------------------- #
# Analytics dropdown
# ---------------------------------------------------------------- #
class AnalyticsCard(RoundedBox):
    """Waste Analytics card with a real Today/Week/Month dropdown."""

    def __init__(self, on_period_change=None, **kwargs):
        super().__init__(
            orientation="vertical",
            bg_color=list(WHITE),
            padding=(0, 0, 0, dp(4)),
            spacing=0,
            **kwargs,
        )

        self.on_period_change = on_period_change
        self.selected_period = "Today"

        top_bar = RoundedBox(
            orientation="horizontal",
            bg_color=list(get_color_from_hex("#F2F2F2")),
            radius=dp(14),
            size_hint_y=None,
            height=dp(38),
            padding=(dp(12), 0),
        )

        top_bar.add_widget(
            Label(
                text="Waste Analytics",
                font_size=sp(13.5),
                bold=True,
                color=TEXT_DARK,
                halign="left",
                valign="middle",
                size_hint_x=1,
                text_size=(dp(180), dp(38)),
            )
        )

        # ---------------------------------------------------------- #
        # Period selector
        # ---------------------------------------------------------- #
        # The selector itself owns the touch behavior. There is no
        # transparent overlay/sibling that can intercept mouse/touch input.
        self.period_button = PeriodSelector(
            on_select=self.select_period,
            size_hint=(None, None),
            size=(dp(92), dp(32)),
        )

        top_bar.add_widget(self.period_button)
        self.add_widget(top_bar)

        self.graph = WaveGraph(
            size_hint_y=None,
            height=dp(150),
        )
        self.add_widget(self.graph)

    def open_period_dropdown(self, *_):
        # Kept for compatibility with older code that may call this method.
        self.period_button.open_menu()

    def select_period(self, period, popup=None):
        self.selected_period = period
        self.period_button.text = period

        if popup is not None:
            popup.dismiss()

        if self.on_period_change:
            self.on_period_change(period)



# ---------------------------------------------------------------- #
# Bottom navigation
# ---------------------------------------------------------------- #
class NavButton(ButtonBehavior, FloatLayout):
    active = BooleanProperty(False)

    def __init__(
        self,
        icon_name,
        on_press_cb=None,
        icon_size=dp(24),
        **kwargs,
    ):
        super().__init__(**kwargs)

        color = WHITE if self.active else NAV_INACTIVE

        self.icon = VectorIcon(
            icon_name=icon_name,
            icon_color=list(color),
            line_width=dp(1.7),
            size_hint=(None, None),
            size=(icon_size, icon_size),
            pos_hint={
                "center_x": 0.5,
                "center_y": 0.5,
            },
        )

        self.add_widget(self.icon)
        self._cb = on_press_cb

    def on_press(self):
        if self._cb:
            self._cb()

    def set_active(self, is_active):
        self.active = is_active
        self.icon.icon_color = list(
            WHITE if is_active else NAV_INACTIVE
        )


class BottomNav(BoxLayout):
    def __init__(self, on_nav=None, **kwargs):
        super().__init__(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(60),
            padding=(dp(6), dp(4)),
            **kwargs,
        )

        with self.canvas.before:
            Color(*DARK_GREEN)
            self._rect = RoundedRectangle(
                pos=self.pos,
                size=self.size,
                radius=[0],
            )

        self.bind(pos=self._sync, size=self._sync)

        self.buttons = []

        icons = [
            "home",
            "pin",
            "people_cog",
            "person",
        ]

        for i, name in enumerate(icons):
            btn = NavButton(
                icon_name=name,
                icon_size=dp(24),
                on_press_cb=lambda idx=i:
                    self._handle(idx, on_nav),
            )

            btn.active = i == 0
            btn.icon.icon_color = list(
                WHITE if i == 0 else NAV_INACTIVE
            )

            self.buttons.append(btn)
            self.add_widget(btn)

    def _sync(self, *_):
        self._rect.pos = self.pos
        self._rect.size = self.size

    def _handle(self, idx, on_nav):
        for i, b in enumerate(self.buttons):
            b.set_active(i == idx)

        if on_nav:
            on_nav(idx)


# ---------------------------------------------------------------- #
# Header
# ---------------------------------------------------------------- #
class HeaderBar(BoxLayout):
    def __init__(
        self,
        greeting="Good Evening",
        subtitle="Here's what's happening today",
        on_menu=None,
        on_bell=None,
        **kwargs,
    ):
        super().__init__(
            orientation="vertical",
            size_hint_y=None,
            height=dp(78),
            spacing=dp(4),
            **kwargs,
        )

        top_row = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(30),
        )

        menu_btn = IconButton(
            icon_name="menu",
            icon_color=list(HEADER_ICON),
            size_hint=(None, None),
            size=(dp(24), dp(24)),
            pos_hint={"center_y": 0.5},
        )

        if on_menu:
            menu_btn.bind(
                on_press=lambda *_: on_menu()
            )

        top_row.add_widget(menu_btn)
        top_row.add_widget(Widget())

        bell_btn = IconButton(
            icon_name="bell",
            icon_color=list(HEADER_ICON),
            size_hint=(None, None),
            size=(dp(24), dp(24)),
            pos_hint={"center_y": 0.5},
        )

        if on_bell:
            bell_btn.bind(
                on_press=lambda *_: on_bell()
            )

        top_row.add_widget(bell_btn)

        self.add_widget(top_row)

        self.add_widget(
            Label(
                text=greeting,
                font_size=sp(20),
                bold=True,
                color=TEXT_DARK,
                halign="left",
                valign="middle",
                size_hint_y=None,
                height=dp(26),
                text_size=(dp(300), dp(26)),
            )
        )

        self.add_widget(
            Label(
                text=subtitle,
                font_size=sp(11),
                color=TEXT_GRAY,
                halign="left",
                valign="middle",
                size_hint_y=None,
                height=dp(16),
                text_size=(dp(300), dp(16)),
            )
        )


# ---------------------------------------------------------------- #
# Firebase helpers
# ---------------------------------------------------------------- #
def _read_first(paths):
    """
    Read the first non-empty Firebase path.

    firebase_config.get_data() returns (ok, result), not result directly.
    The old dashboard treated that tuple as the data itself, so _records()
    received a tuple and returned [] — causing bins, workers and graph data
    to stay at zero even when Firebase contained records.
    """
    if get_data is None:
        print("[ADMIN FIREBASE] get_data is unavailable")
        return None

    for path in paths:
        try:
            response = get_data(path)

            if isinstance(response, tuple) and len(response) == 2:
                ok, data = response
            else:
                ok, data = True, response

            if not ok:
                print(f"[ADMIN FIREBASE] read failed for {path}: {data}")
                continue

            if data not in (None, {}, []):
                print(
                    f"[ADMIN FIREBASE] loaded {path}: "
                    f"{type(data).__name__}"
                )
                return data

            print(f"[ADMIN FIREBASE] {path}: no data")

        except Exception as exc:
            print(f"[ADMIN FIREBASE] read exception for {path}: {exc}")

    return None


def _records(data):
    if data is None:
        return []

    if isinstance(data, list):
        return [
            x for x in data
            if isinstance(x, dict)
        ]

    if isinstance(data, dict):
        result = []

        for key, value in data.items():
            if isinstance(value, dict):
                item = dict(value)
                item.setdefault("_id", key)
                result.append(item)

        return result

    return []


def _lower(value):
    return str(value or "").strip().lower()


def _bin_status(record):
    raw = record.get("status")

    if raw is None:
        raw = record.get("bin_status")

    if raw is None:
        raw = record.get("fill_status")

    if raw is None:
        raw = record.get("waste_status")

    text = _lower(raw)

    if text in (
        "full",
        "filled",
        "100",
        "100%",
        "full bin",
    ):
        return "full"

    if text in (
        "half",
        "half filled",
        "half-filled",
        "medium",
        "50",
        "50%",
        "half_full",
    ):
        return "half"

    if text in (
        "empty",
        "0",
        "0%",
        "empty bin",
    ):
        return "empty"

    for key in (
        "fill_level",
        "waste_level",
        "level",
        "percentage",
        "fill_percentage",
    ):
        if key in record:
            try:
                value = float(
                    str(record[key])
                    .replace("%", "")
                    .strip()
                )

                if value >= 80:
                    return "full"

                if value >= 30:
                    return "half"

                return "empty"

            except Exception:
                pass

    return ""


def _is_collected(record):
    """Return True for common Firebase collection/completion schemas."""
    # Explicit boolean flags.
    for key in (
        "collected",
        "is_collected",
        "collection_completed",
        "is_completed",
        "completed",
    ):
        if key in record:
            value = record.get(key)
            if value is True:
                return True
            if _lower(value) in ("true", "1", "yes", "collected", "completed", "complete"):
                return True

    # Text status fields.
    for key in (
        "collection_status",
        "task_status",
        "status",
        "state",
    ):
        if key not in record:
            continue
        text = _lower(record.get(key))
        if text in (
            "collected",
            "completed",
            "complete",
            "done",
            "picked",
            "picked up",
            "true",
            "finished",
            "closed",
        ):
            return True

    # A collection timestamp is itself strong evidence that a collection
    # happened, even if no separate status field exists.
    for key in (
        "collected_at",
        "collectedAt",
        "collection_datetime",
        "collectionDateTime",
        "collection_date",
        "collectionDate",
        "completed_at",
        "completedAt",
        "picked_up_at",
        "pickedUpAt",
    ):
        if record.get(key) not in (None, "", False):
            return True

    return False


def _is_active_worker(record):
    value = record.get("active")

    if value is True:
        return True

    for key in (
        "status",
        "worker_status",
        "account_status",
    ):
        text = _lower(record.get(key))

        if text in (
            "active",
            "online",
            "available",
        ):
            return True

    return False


def _record_datetime(record):
    candidates = (
        "collected_at",
        "collectedAt",
        "collection_datetime",
        "collectionDateTime",
        "datetime",
        "created_at",
        "createdAt",
        "timestamp",
        "date",
        "task_date",
        "taskDate",
        "collection_date",
        "collectionDate",
        "updated_at",
        "updatedAt",
    )

    for key in candidates:
        value = record.get(key)

        if value is None:
            continue

        if isinstance(value, (int, float)):
            try:
                return datetime.fromtimestamp(
                    float(value)
                )
            except Exception:
                pass

        text = str(value).strip()

        if not text:
            continue

        try:
            return datetime.fromisoformat(
                text.replace("Z", "+00:00")
            ).replace(tzinfo=None)
        except Exception:
            pass

        for fmt in (
            "%d-%m-%Y %H:%M",
            "%d/%m/%Y %H:%M",
            "%m/%d/%Y %H:%M",
            "%Y-%m-%d %H:%M",
            "%d-%m-%Y",
            "%d/%m/%Y",
            "%m/%d/%Y",
            "%Y-%m-%d",
        ):
            try:
                return datetime.strptime(
                    text[:16],
                    fmt,
                )
            except Exception:
                try:
                    return datetime.strptime(
                        text[:10],
                        fmt,
                    )
                except Exception:
                    pass

    return None


def _collection_tons(record):
    for key in (
        "weight_ton",
        "weight_tons",
        "weightTon",
        "weightTons",
        "tons",
        "collection_ton",
        "collectionTon",
        "collected_ton",
        "collectedTon",
    ):
        if key in record:
            try:
                return float(record[key])
            except Exception:
                pass

    for key in (
        "weight_kg",
        "weightKg",
        "kg",
        "weight",
        "collection_weight",
        "collectionWeight",
    ):
        if key in record:
            try:
                return float(record[key]) / 1000.0
            except Exception:
                pass

    return 0.0


def _period_tasks(tasks, period):
    now = datetime.now()
    today = now.date()

    collected = [
        t for t in tasks
        if _is_collected(t)
        and _record_datetime(t) is not None
    ]

    if period == "Today":
        return [
            t for t in collected
            if _record_datetime(t).date() == today
        ]

    if period == "This Week":
        week_start = today - timedelta(
            days=today.weekday()
        )
        week_end = week_start + timedelta(days=6)

        return [
            t for t in collected
            if week_start
            <= _record_datetime(t).date()
            <= week_end
        ]

    month_start = today.replace(day=1)

    if today.month == 12:
        next_month = today.replace(
            year=today.year + 1,
            month=1,
            day=1,
        )
    else:
        next_month = today.replace(
            month=today.month + 1,
            day=1,
        )

    return [
        t for t in collected
        if month_start
        <= _record_datetime(t).date()
        < next_month
    ]


def _period_graph_data(tasks, period):
    """
    Returns REAL collected-task data only.

    If there are no collected records for the selected period,
    returns zeros. WaveGraph then intentionally displays no line.
    """

    now = datetime.now()

    collected = [
        t for t in tasks
        if _is_collected(t)
        and _record_datetime(t) is not None
    ]

    if period == "Today":
        data = [0] * 14

        for task in collected:
            dt = _record_datetime(task)

            if dt.date() != now.date():
                continue

            bucket = min(
                max(dt.hour // 2, 0),
                13,
            )
            data[bucket] += 1

        return (
            data,
            [
                "1 AM",
                "6 AM",
                "12 PM",
                "6 PM",
                "12 AM",
            ],
        )

    if period == "This Week":
        start = now.date() - timedelta(
            days=now.date().weekday()
        )

        data = [0] * 7

        for task in collected:
            dt = _record_datetime(task)
            diff = (dt.date() - start).days

            if 0 <= diff < 7:
                data[diff] += 1

        return (
            data,
            [
                "Mon",
                "Tue",
                "Wed",
                "Thu",
                "Fri",
                "Sat",
                "Sun",
            ],
        )

    start = now.date().replace(day=1)
    data = [0] * 5

    for task in collected:
        dt = _record_datetime(task)

        if (
            dt.year == start.year
            and dt.month == start.month
        ):
            bucket = min(
                (dt.day - 1) // 7,
                4,
            )
            data[bucket] += 1

    return (
        data,
        [
            "W1",
            "W2",
            "W3",
            "W4",
            "W5",
        ],
    )


# ---------------------------------------------------------------- #
# Dashboard
# ---------------------------------------------------------------- #
class AdminDashboardScreen(Screen):

    NAV_ROUTES = {
        0: "admin_dashboard",
        1: "admin_map",
        2: "admin_panel",
        3: "admin_profile",
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        root = FloatLayout()

        with root.canvas.before:
            Color(*BG)
            self._bg_rect = RoundedRectangle(
                pos=root.pos,
                size=root.size,
                radius=[0],
            )

        root.bind(
            pos=lambda *_:
                setattr(self._bg_rect, "pos", root.pos),
            size=lambda *_:
                setattr(self._bg_rect, "size", root.size),
        )

        outer = BoxLayout(
            orientation="vertical",
            size_hint=(1, 1),
        )

        body = BoxLayout(
            orientation="vertical",
            padding=(
                dp(16),
                dp(14),
                dp(16),
                dp(6),
            ),
            spacing=dp(12),
        )

        body.add_widget(HeaderBar())

        grid = GridLayout(
            cols=2,
            spacing=dp(8),
            size_hint_y=None,
            height=dp(160),
        )

        self.total_card = StatCard(
            "trash",
            0,
            "Total Bins",
            GREEN_BG,
            GREEN_FG,
        )

        self.full_card = StatCard(
            "trash",
            0,
            "Full Bins",
            RED_BG,
            RED_FG,
        )

        self.half_card = StatCard(
            "trash",
            0,
            "Half Filled",
            YELLOW_BG,
            YELLOW_FG,
        )

        self.empty_card = StatCard(
            "trash",
            0,
            "Empty Bins",
            GREEN_BG,
            GREEN_FG,
        )

        for card in (
            self.total_card,
            self.full_card,
            self.half_card,
            self.empty_card,
        ):
            grid.add_widget(card)

        body.add_widget(grid)

        self.analytics = AnalyticsCard(
            on_period_change=self._on_period_change,
            size_hint_y=None,
            height=dp(200),
        )

        body.add_widget(self.analytics)

        bottom_row = BoxLayout(
            orientation="horizontal",
            spacing=dp(10),
            size_hint_y=None,
            height=dp(64),
        )

        self.collection_card = InfoCard(
            "truck",
            "Today's Collection",
            "0",
            "Ton",
        )

        self.workers_card = InfoCard(
            "people",
            "Active Workers",
            "0",
        )

        bottom_row.add_widget(self.collection_card)
        bottom_row.add_widget(self.workers_card)

        body.add_widget(bottom_row)
        body.add_widget(Widget())

        outer.add_widget(body)
        outer.add_widget(
            BottomNav(on_nav=self._on_nav)
        )

        root.add_widget(outer)
        self.add_widget(root)

        self._refresh_event = None
        self._refresh_running = False
        self.selected_period = "Today"

    def on_pre_enter(self, *args):
        # NEVER perform Firebase/network I/O on Kivy's main thread.
        self._start_refresh()

        if self._refresh_event is None:
            self._refresh_event = Clock.schedule_interval(
                lambda dt: self._start_refresh(),
                10,
            )

    def on_leave(self, *args):
        if self._refresh_event is not None:
            self._refresh_event.cancel()
            self._refresh_event = None

    def _start_refresh(self, *_):
        # One refresh at a time; prevents slow Firebase calls from piling up.
        if getattr(self, "_refresh_running", False):
            return

        self._refresh_running = True

        import threading
        threading.Thread(
            target=self._firebase_worker,
            daemon=True,
        ).start()

    def _firebase_worker(self):
        try:
            data = self._load_dashboard_data()
            Clock.schedule_once(
                lambda dt: self._apply_dashboard_data(data),
                0,
            )
        except Exception as exc:
            print(f"[ADMIN FIREBASE] Background refresh error: {exc}")
            Clock.schedule_once(
                lambda dt: self._finish_refresh(),
                0,
            )

    def _load_dashboard_data(self):
        # This function runs OFF the Kivy UI thread.
        bins_data = _read_first(
            ["bins", "waste_bins", "bin_data"]
        )

        staff_data = _read_first(
            ["staff", "users", "workers"]
        )

        tasks_data = _read_first(
            [
                "tasks",
                "task_history",
                "collections",
                "collection_history",
                "collection_tasks",
                "waste_collections",
                "pickup_tasks",
                "staff_tasks",
            ]
        )

        bins = _records(bins_data)
        staff = _records(staff_data)
        tasks = _records(tasks_data)

        total = len(bins)
        full = sum(1 for b in bins if _bin_status(b) == "full")
        half = sum(1 for b in bins if _bin_status(b) == "half")
        empty = sum(1 for b in bins if _bin_status(b) == "empty")

        active_workers = sum(
            1 for worker in staff if _is_active_worker(worker)
        )

        period = self.selected_period
        period_tasks = _period_tasks(tasks, period)
        tons = sum(_collection_tons(task) for task in period_tasks)

        collection_title = {
            "Today": "Today's Collection",
            "This Week": "This Week's Collection",
            "This Month": "This Month's Collection",
        }.get(period, "Today's Collection")

        graph_data, graph_ticks = _period_graph_data(tasks, period)

        return {
            "total": total,
            "full": full,
            "half": half,
            "empty": empty,
            "active_workers": active_workers,
            "period": period,
            "period_tasks": len(period_tasks),
            "tons": round(tons, 2),
            "collection_title": collection_title,
            "graph_data": graph_data,
            "graph_ticks": graph_ticks,
        }

    def _apply_dashboard_data(self, data):
        try:
            # UI changes happen ONLY on Kivy's main thread.
            if not data:
                return

            self.total_card.set_count(data["total"])
            self.full_card.set_count(data["full"])
            self.half_card.set_count(data["half"])
            self.empty_card.set_count(data["empty"])

            self.workers_card.set_value(data["active_workers"])

            self.collection_card.set_title(data["collection_title"])
            self.collection_card.set_value(data["tons"], "Ton")

            self.analytics.graph.set_data(
                data["graph_data"],
                data["graph_ticks"],
            )

            print(
                "[ADMIN FIREBASE] "
                f"bins={data['total']}, "
                f"full={data['full']}, "
                f"half={data['half']}, "
                f"empty={data['empty']}, "
                f"active_workers={data['active_workers']}, "
                f"period={data['period']}, "
                f"period_collected={data['period_tasks']}, "
                f"period_tons={data['tons']}"
            )
        except Exception as exc:
            print(f"[ADMIN FIREBASE] UI update error: {exc}")
        finally:
            self._finish_refresh()

    def _finish_refresh(self):
        self._refresh_running = False

    # Compatibility: older code can still call refresh_firebase().
    # It now starts a background refresh instead of blocking the UI.
    def refresh_firebase(self, *_):
        self._start_refresh()

    def _on_period_change(self, period):
        self.selected_period = period
        self._start_refresh()

    def _on_nav(self, index):
        target = self.NAV_ROUTES.get(index)

        if target is None:
            return

        if target == self.name:
            self.refresh_firebase()
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
                f"'{target}' is not registered in main.py."
            )
            return

        self.manager.current = target
