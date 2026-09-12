"""
Role Selection Screen — Kivy version
--------------------------------------------------------------------
Recreates the original tkinter "Role Selection" screen:
  - Top artwork image (welcome.png)
  - "Welcome Back!" title + "Select your role to Continue" subtitle
  - Two rounded role cards (Administrator / Staff Member), each with:
        - a small circular icon (checkmark badge for Admin,
          person silhouette for Staff)
        - a title + description
        - a rounded green "Continue as ..." button
  - Bottom "Need help? Contact support" row, pinned to the bottom

Drop this file into your Kivy project (e.g. screens/role_selection.py)
and register it on your ScreenManager:

    from role_selection import RoleSelectionScreen
    sm.add_widget(RoleSelectionScreen(name="role_selection"))

Make sure ARTWORK_FILENAME below points at your saved image
(default: "welcome.png", placed next to this file).
"""

import os
import math
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.image import Image as KvImage
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.uix.behaviors import ButtonBehavior
from kivy.graphics import Color, Rectangle, RoundedRectangle, Ellipse, Line, Mesh
from kivy.utils import get_color_from_hex as hexc
from kivy.metrics import dp, sp
from kivy.properties import BooleanProperty


# ---- configurable bits -------------------------------------------------
ARTWORK_FILENAME   = "welcome.png"     # top illustration
ADMIN_NEXT_SCREEN  = "admin_login"     # screen name to go to on "Continue as Admin"
STAFF_NEXT_SCREEN  = "staff_login"     # screen name to go to on "Continue as Staff"
CARD_BG            = "#EFEFEF"
GREEN              = "#004D34"
TEXT_GRAY          = "#555555"
# -------------------------------------------------------------------------


class ArrowIcon(Widget):
    """A small vector right-arrow (shaft + chevron head) — used instead of
    a unicode arrow character since not every font renders '→' reliably."""

    def __init__(self, color_hex=None, **kwargs):
        super().__init__(**kwargs)
        self._rgba = (1, 1, 1, 1) if color_hex is None else hexc(color_hex)
        with self.canvas:
            Color(*self._rgba)
            self._shaft = Line(width=dp(1.6), cap="round")
            self._head = Line(width=dp(1.6), cap="round", joint="round")
        self.bind(pos=self._redraw, size=self._redraw)
        self._redraw()

    def _redraw(self, *args):
        x, y = self.pos
        w, h = self.size
        cy = y + h / 2
        x1 = x + w * 0.08
        x2 = x + w * 0.62
        self._shaft.points = [x1, cy, x2, cy]
        head_size = h * 0.55
        self._head.points = [
            x2 - head_size * 0.45, cy + head_size * 0.5,
            x2 + w * 0.20, cy,
            x2 - head_size * 0.45, cy - head_size * 0.5,
        ]


class RoundedButton(ButtonBehavior, BoxLayout):
    """A green, rounded, tappable button with centered text + arrow icon
    (used for 'Continue as ...')."""

    def __init__(self, text="", radius=dp(12), bg_hex=GREEN, **kwargs):
        super().__init__(orientation="horizontal", **kwargs)
        with self.canvas.before:
            self._bg_color = Color(*hexc(bg_hex))
            self._bg_rect = RoundedRectangle(radius=[radius])
        self.bind(pos=self._redraw, size=self._redraw)

        anchor = AnchorLayout()
        inner = BoxLayout(orientation="horizontal", spacing=dp(8),
                           size_hint=(None, None), height=dp(20))
        inner.bind(minimum_width=inner.setter("width"))

        self.label = Label(text=text, color=(1, 1, 1, 1), bold=True, font_size=sp(13),
                            size_hint=(None, None), height=dp(20))
        self.label.bind(texture_size=lambda inst, val: setattr(inst, "width", val[0]))
        inner.add_widget(self.label)

        inner.add_widget(ArrowIcon(size_hint=(None, None), size=(dp(16), dp(16))))

        anchor.add_widget(inner)
        self.add_widget(anchor)

    def _redraw(self, *args):
        self._bg_rect.pos = self.pos
        self._bg_rect.size = self.size

    def on_press(self):
        self._bg_color.rgba = (*hexc(GREEN)[:3], 0.85)

    def on_release(self):
        self._bg_color.rgba = (*hexc(GREEN)[:3], 1)


class RoleIcon(Widget):
    """
    Small circular icon matching the app's design:
      - Admin:  mint-green circle + dark-green shield with a white
                checkmark inside (a "secure / verified access" badge).
      - Staff:  light-gray circle + a simple solid person silhouette
                (head + shoulders), same style as a generic avatar icon.
    """

    is_admin = BooleanProperty(True)

    def __init__(self, is_admin=True, **kwargs):
        super().__init__(**kwargs)
        self.is_admin = is_admin

        with self.canvas:
            # Background circle
            self._circle_color = Color(*hexc("#E2ECE9" if is_admin else "#EAEAEA"))
            self._circle = Ellipse()

            if self.is_admin:
                # Filled shield (drawn as a fan-triangulated polygon)
                self._shield_color = Color(*hexc(GREEN))
                self._shield_mesh = Mesh(mode="triangle_fan")
                # White person silhouette inside the shield
                self._icon_color = Color(1, 1, 1, 1)
                self._head = Ellipse()
                self._body = Ellipse()
            else:
                # Outlined avatar: ring + head + shoulders (matches the
                # "account circle" outline icon used in the design)
                self._icon_color = Color(*hexc("#3A3A3A"))
                self._outer_ring = Line(width=dp(1.5))
                self._head_ring = Line(width=dp(1.4))
                self._shoulder_ring = Line(width=dp(1.4))

        self.bind(pos=self._redraw, size=self._redraw)
        self._redraw()  # draw immediately so the Mesh never has an invalid empty state

    @staticmethod
    def _fan_mesh_vertices(points):
        """Build (vertices, indices) for a filled convex polygon via a
        triangle fan pivoted at the polygon's centroid."""
        cx = sum(p[0] for p in points) / len(points)
        cy = sum(p[1] for p in points) / len(points)
        verts = [cx, cy, 0, 0]
        for px, py in points:
            verts += [px, py, 0, 0]
        verts += [points[0][0], points[0][1], 0, 0]
        indices = list(range(len(points) + 2))
        return verts, indices

    def _redraw(self, *args):
        x, y = self.pos
        w, h = self.size
        self._circle.pos = self.pos
        self._circle.size = self.size
        cx, cy = x + w / 2, y + h / 2

        if self.is_admin:
            # ---- Shield outline (flat top, tapering to a point) ----
            shield_pts = [
                (x + w * 0.24, y + h * 0.84),
                (x + w * 0.76, y + h * 0.84),
                (x + w * 0.76, y + h * 0.50),
                (x + w * 0.50, y + h * 0.12),
                (x + w * 0.24, y + h * 0.50),
            ]
            verts, indices = self._fan_mesh_vertices(shield_pts)
            self._shield_mesh.vertices = verts
            self._shield_mesh.indices = indices

            # ---- White person silhouette centered in the shield ----
            shield_cy = y + h * 0.50
            head_d = h * 0.19
            self._head.size = (head_d, head_d)
            self._head.pos = (cx - head_d / 2, shield_cy + h * 0.04)
            body_w = w * 0.38
            body_h = h * 0.22
            self._body.size = (body_w, body_h)
            self._body.pos = (cx - body_w / 2, shield_cy - h * 0.17)

        else:
            # ---- Outlined avatar: circle + head + shoulders (all rings) ----
            ring_r = min(w, h) * 0.40
            self._outer_ring.circle = (cx, cy, ring_r)

            head_r = h * 0.115
            head_cy = y + h * 0.62
            self._head_ring.circle = (cx, head_cy, head_r)

            shoulder_r = w * 0.20
            shoulder_base_y = y + h * 0.33
            segments = 16
            pts = []
            for i in range(segments + 1):
                theta = math.pi - (math.pi * i / segments)
                pts += [cx + shoulder_r * math.cos(theta),
                        shoulder_base_y + shoulder_r * math.sin(theta)]
            self._shoulder_ring.points = pts


class HeadsetIcon(Widget):
    """A small vector headset icon (support/help symbol): a curved band
    over two ear cups."""

    def __init__(self, color_hex=TEXT_GRAY, **kwargs):
        super().__init__(**kwargs)
        with self.canvas:
            Color(*hexc(color_hex))
            self._band = Line(width=dp(1.5), cap="round")
            self._left_cup = RoundedRectangle(radius=[dp(1.5)])
            self._right_cup = RoundedRectangle(radius=[dp(1.5)])
        self.bind(pos=self._redraw, size=self._redraw)
        self._redraw()

    def _redraw(self, *args):
        x, y = self.pos
        w, h = self.size
        cx = x + w / 2
        r = w * 0.36
        base_y = y + h * 0.32

        segments = 14
        pts = []
        for i in range(segments + 1):
            theta = math.pi - (math.pi * i / segments)
            pts += [cx + r * math.cos(theta), base_y + r * math.sin(theta)]
        self._band.points = pts

        cup_w = w * 0.20
        cup_h = h * 0.32
        self._left_cup.pos = (cx - r - cup_w * 0.25, y + h * 0.04)
        self._left_cup.size = (cup_w, cup_h)
        self._right_cup.pos = (cx + r - cup_w * 0.75, y + h * 0.04)
        self._right_cup.size = (cup_w, cup_h)


class RoleCard(BoxLayout):
    """A rounded card: icon + title + description on top, a CTA button below."""

    def __init__(self, title, desc, btn_text, is_admin, on_press, **kwargs):
        super().__init__(orientation="vertical", padding=dp(14), spacing=dp(10), **kwargs)
        self.size_hint_y = None
        self.height = dp(150)

        with self.canvas.before:
            Color(*hexc(CARD_BG))
            self._bg_rect = RoundedRectangle(radius=[dp(20)])
        self.bind(pos=self._redraw, size=self._redraw)

        top_row = BoxLayout(orientation="horizontal", spacing=dp(12))
        icon_anchor = AnchorLayout(size_hint=(None, 1), width=dp(38), anchor_y="top")
        icon_anchor.add_widget(RoleIcon(is_admin=is_admin, size_hint=(None, None),
                                         size=(dp(38), dp(38))))
        top_row.add_widget(icon_anchor)

        text_col = BoxLayout(orientation="vertical", spacing=dp(4))
        title_lbl = Label(text=title, font_size=sp(16), bold=True, color=(0, 0, 0, 1),
                           halign="left", valign="top", size_hint_y=None, height=dp(22))
        title_lbl.bind(size=lambda i, v: setattr(i, "text_size", v))
        desc_lbl = Label(text=desc, font_size=sp(11), color=hexc(TEXT_GRAY),
                          halign="left", valign="top")
        desc_lbl.bind(size=lambda i, v: setattr(i, "text_size", v))
        text_col.add_widget(title_lbl)
        text_col.add_widget(desc_lbl)
        top_row.add_widget(text_col)

        self.add_widget(top_row)

        btn = RoundedButton(text=btn_text, size_hint=(1, None), height=dp(38))
        btn.bind(on_release=lambda inst: on_press())
        self.add_widget(btn)

    def _redraw(self, *args):
        self._bg_rect.pos = self.pos
        self._bg_rect.size = self.size


class ClickableLabel(ButtonBehavior, Label):
    """A Label that behaves like a tappable link."""
    pass


class RoleSelectionScreen(Screen):
    """Full role-selection screen: artwork, title, two role cards, support row."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        root = FloatLayout()
        self._root_layout = root
        self.add_widget(root)

        # White background (drawn in root's own local coordinate space,
        # so it always matches root's pos/size regardless of how the
        # Screen itself is positioned during transitions).
        with root.canvas.before:
            Color(1, 1, 1, 1)
            self._bg_rect = Rectangle()
        root.bind(pos=self._redraw_bg, size=self._redraw_bg)

        # ---- main content (everything except the pinned support row) ----
        content = BoxLayout(orientation="vertical", padding=(dp(25), dp(15), dp(25), 0),
                             spacing=dp(4),
                             size_hint=(1, 1), pos_hint={"x": 0, "top": 1})

        # Top artwork
        art_anchor = AnchorLayout(size_hint=(1, None), height=dp(80), anchor_x="center")
        if os.path.exists(ARTWORK_FILENAME):
            artwork = KvImage(source=ARTWORK_FILENAME, allow_stretch=True, keep_ratio=True,
                               size_hint=(None, None), size=(dp(140), dp(70)))
        else:
            artwork = Label(text="[ Artwork ]", color=(0.2, 0.2, 0.2, 1))
        art_anchor.add_widget(artwork)
        content.add_widget(art_anchor)

        # Title + subtitle
        title = Label(text="Welcome Back!", font_size=sp(24), bold=True, color=(0, 0, 0, 1),
                       size_hint_y=None, height=dp(38))
        content.add_widget(title)

        subtitle = Label(text="Select your role to Continue", font_size=sp(12),
                          color=hexc(TEXT_GRAY), size_hint_y=None, height=dp(26))
        content.add_widget(subtitle)

        # Spacer
        content.add_widget(Widget(size_hint_y=None, height=dp(8)))

        # Role cards
        cards_area = BoxLayout(orientation="vertical", spacing=dp(12),
                                size_hint_y=None)
        cards_area.bind(minimum_height=cards_area.setter("height"))

        admin_card = RoleCard(
            title="Administrator",
            desc="Secure system access\nand management",
            btn_text="Continue as Admin",
            is_admin=True,
            on_press=self._go_admin,
        )
        staff_card = RoleCard(
            title="Staff Member",
            desc="Daily operations\nand support access",
            btn_text="Continue as Staff",
            is_admin=False,
            on_press=self._go_staff,
        )
        cards_area.add_widget(admin_card)
        cards_area.add_widget(staff_card)
        content.add_widget(cards_area)

        # Remaining flexible space above the support row
        content.add_widget(Widget())

        root.add_widget(content)

        # ---- pinned support row at the bottom ----
        support_row = BoxLayout(orientation="horizontal", spacing=dp(4),
                                 size_hint=(1, None), height=dp(50),
                                 pos_hint={"x": 0, "y": 0})
        support_anchor = AnchorLayout(anchor_x="center")

        # Auto-sized (hug-the-text) row so "Need help?" and "Contact support"
        # sit close together as one centered group, instead of stretching
        # to fixed widths that leave a big gap between them.
        inner = BoxLayout(orientation="horizontal", spacing=dp(4),
                           size_hint=(None, None), height=dp(24))
        inner.bind(minimum_width=inner.setter("width"))

        headset_wrap = AnchorLayout(size_hint=(None, None), size=(dp(22), dp(24)))
        headset_wrap.add_widget(HeadsetIcon(size_hint=(None, None), size=(dp(17), dp(17))))
        inner.add_widget(headset_wrap)

        need_help_lbl = Label(text="Need help?", font_size=sp(11),
                               color=hexc(TEXT_GRAY),
                               size_hint=(None, None), height=dp(24))
        need_help_lbl.bind(texture_size=lambda inst, val: setattr(inst, "width", val[0]))

        self.support_link = ClickableLabel(text="Contact support", font_size=sp(11),
                                            bold=True, color=hexc(GREEN),
                                            size_hint=(None, None), height=dp(24))
        self.support_link.bind(texture_size=lambda inst, val: setattr(inst, "width", val[0]))
        self.support_link.bind(on_release=lambda inst: self.contact_support_action())

        inner.add_widget(need_help_lbl)
        inner.add_widget(self.support_link)
        support_anchor.add_widget(inner)
        support_row.add_widget(support_anchor)
        root.add_widget(support_row)

    def _redraw_bg(self, *args):
        self._bg_rect.pos = self._root_layout.pos
        self._bg_rect.size = self._root_layout.size

    # ---- actions ----
    def contact_support_action(self):
        print("Support clicked")

    def _go_admin(self):
        if self.manager:
            self.manager.current = ADMIN_NEXT_SCREEN
        else:
            print(f"(standalone) would navigate to: {ADMIN_NEXT_SCREEN}")

    def _go_staff(self):
        if self.manager:
            self.manager.current = STAFF_NEXT_SCREEN
        else:
            print(f"(standalone) would navigate to: {STAFF_NEXT_SCREEN}")


# ---------------------------------------------------------------------
# Standalone preview — run just this file to see the Role Selection
# screen on its own, at a phone-sized window.
# ---------------------------------------------------------------------
if __name__ == "__main__":
    from kivy.app import App
    from kivy.uix.screenmanager import ScreenManager
    from kivy.core.window import Window

    class PlaceholderScreen(Screen):
        def __init__(self, label_text, **kwargs):
            super().__init__(**kwargs)
            self.add_widget(Label(text=label_text, color=(0, 0, 0, 1)))

    class RolePreviewApp(App):
        def build(self):
            Window.size = (360, 640)
            Window.clearcolor = (1, 1, 1, 1)
            sm = ScreenManager()
            sm.add_widget(RoleSelectionScreen(name="role_selection"))
            sm.add_widget(PlaceholderScreen("Admin Login\n(placeholder)", name="admin_login"))
            sm.add_widget(PlaceholderScreen("Staff Login\n(placeholder)", name="staff_login"))
            sm.current = "role_selection"
            return sm

    RolePreviewApp().run()