"""
Splash Screen — Kivy version
--------------------------------------------------------------------
Recreates the original tkinter splash screen:
  - Dark-green vertical gradient background
  - App logo image, centered near the top
  - "Smart Waste Monitor" title
  - Thin separator line
  - "Clean City, Smart Future" subtitle
  - Animated rounded progress bar with a "Loading......" -> "Done!" label
  - Auto-navigates to the next screen once loading finishes

Drop this file into your Kivy project (e.g. screens/splash_screen.py) and
register it on your ScreenManager:

    from splash_screen import SplashScreen
    sm.add_widget(SplashScreen(name="splash"))

Set LOGO_FILENAME below to match your actual logo image file.
"""

import os
from kivy.uix.screenmanager import Screen
from kivy.uix.image import Image as KvImage
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.graphics import Color, Rectangle, RoundedRectangle
from kivy.graphics.texture import Texture
from kivy.clock import Clock
from kivy.utils import get_color_from_hex as hexc
from kivy.metrics import dp
from kivy.properties import NumericProperty


# ---- configurable bits -------------------------------------------------
LOGO_FILENAME   = "image.png"          # change to your actual logo file name
NEXT_SCREEN     = "role_selection"     # name of the screen to go to next
GRADIENT_TOP    = (0, 77, 52)          # #004D34 (start color, top of screen)
GRADIENT_BOTTOM = (3, 28, 19)          # end color, bottom of screen
# -------------------------------------------------------------------------


class GradientBackground(Widget):
    """Fills itself with a smooth vertical gradient (top -> bottom)."""

    def __init__(self, top_color, bottom_color, **kwargs):
        super().__init__(**kwargs)
        self.top_color = top_color
        self.bottom_color = bottom_color
        self._texture = self._build_texture()
        with self.canvas:
            Color(1, 1, 1, 1)
            self._rect = Rectangle(texture=self._texture, pos=self.pos, size=self.size)
        self.bind(pos=self._on_resize, size=self._on_resize)

    def _build_texture(self):
        height = 256
        buf = bytearray(height * 4)
        for row in range(height):
            factor = row / float(height - 1)
            r = int(self.top_color[0] + factor * (self.bottom_color[0] - self.top_color[0]))
            g = int(self.top_color[1] + factor * (self.bottom_color[1] - self.top_color[1]))
            b = int(self.top_color[2] + factor * (self.bottom_color[2] - self.top_color[2]))
            # Kivy textures are addressed bottom-up, so flip the row
            idx = (height - 1 - row) * 4
            buf[idx:idx + 4] = bytes((r, g, b, 255))
        tex = Texture.create(size=(1, height))
        tex.blit_buffer(bytes(buf), colorfmt="rgba", bufferfmt="ubyte")
        return tex

    def _on_resize(self, *args):
        self._rect.pos = self.pos
        self._rect.size = self.size


class RoundedProgressBar(Widget):
    """A simple rounded track + rounded fill bar, driven by `value` (0.0 - 1.0)."""

    value = NumericProperty(0.0)

    def __init__(self, track_hex="#A8B4AE", fill_hex="#0F683A", **kwargs):
        super().__init__(**kwargs)
        with self.canvas:
            Color(*hexc(track_hex))
            self._track = RoundedRectangle(radius=[dp(6)])
            Color(*hexc(fill_hex))
            self._fill = RoundedRectangle(radius=[dp(6)])
        self.bind(pos=self._redraw, size=self._redraw, value=self._redraw)

    def _redraw(self, *args):
        self._track.pos = self.pos
        self._track.size = self.size
        fill_w = max(self.size[0] * min(max(self.value, 0.0), 1.0), dp(12))
        self._fill.pos = self.pos
        self._fill.size = (fill_w, self.size[1])


class SplashScreen(Screen):
    """Full splash screen: background + logo + text + animated progress bar."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # 1) Gradient background, fills the whole screen
        self.bg = GradientBackground(GRADIENT_TOP, GRADIENT_BOTTOM,
                                      size_hint=(1, 1), pos_hint={"x": 0, "y": 0})
        self.add_widget(self.bg)

        # 2) Logo
        if os.path.exists(LOGO_FILENAME):
            self.logo = KvImage(source=LOGO_FILENAME, allow_stretch=True, keep_ratio=True,
                                 size_hint=(0.4, 0.4),
                                 pos_hint={"center_x": 0.5, "center_y": 0.70})
        else:
            self.logo = Label(text="[ Logo ]", color=(1, 1, 1, 1), font_size=dp(14),
                               size_hint=(0.4, 0.15),
                               pos_hint={"center_x": 0.5, "center_y": 0.70})
        self.add_widget(self.logo)

        # 3) Title
        self.title_label = Label(
            text="Smart Waste\nMonitor",
            font_size=dp(26), bold=True, color=(1, 1, 1, 1),
            halign="center", valign="middle",
            size_hint=(0.9, 0.12),
            pos_hint={"center_x": 0.5, "center_y": 0.478},
        )
        self.title_label.bind(size=self._sync_text_size)
        self.add_widget(self.title_label)

        # 4) Thin separator line
        self.separator = Widget(size_hint=(0.55, None), height=dp(1),
                                 pos_hint={"center_x": 0.5, "center_y": 0.393})
        with self.separator.canvas:
            Color(*hexc("#7DA393"))
            self._sep_rect = Rectangle(pos=self.separator.pos, size=self.separator.size)
        self.separator.bind(pos=self._redraw_separator, size=self._redraw_separator)
        self.add_widget(self.separator)

        # 5) Subtitle
        self.subtitle_label = Label(
            text="Clean City, Smart Future",
            font_size=dp(13), bold=True, color=(1, 1, 1, 1),
            halign="center", valign="middle",
            size_hint=(0.9, 0.05),
            pos_hint={"center_x": 0.5, "center_y": 0.35},
        )
        self.subtitle_label.bind(size=self._sync_text_size)
        self.add_widget(self.subtitle_label)

        # 6) Loading text
        self.loading_label = Label(
            text="Loading......",
            font_size=dp(11), italic=True, color=(1, 1, 1, 1),
            halign="center", valign="middle",
            size_hint=(0.9, 0.04),
            pos_hint={"center_x": 0.5, "center_y": 0.0857},
        )
        self.loading_label.bind(size=self._sync_text_size)
        self.add_widget(self.loading_label)

        # 7) Progress bar
        self.progress_bar = RoundedProgressBar(
            size_hint=(0.675, None), height=dp(12),
            pos_hint={"center_x": 0.5, "center_y": 0.141},
        )
        self.add_widget(self.progress_bar)

        # Animation state
        self._step = 4 / 270.0     # mirrors the original "+4 out of 270px" pace
        self._anim_event = None

    # ---- helpers ----
    def _sync_text_size(self, instance, value):
        instance.text_size = instance.size

    def _redraw_separator(self, *args):
        self._sep_rect.pos = self.separator.pos
        self._sep_rect.size = self.separator.size

    # ---- lifecycle ----
    def on_enter(self, *args):
        """Kick off the loading animation each time this screen is shown."""
        self.progress_bar.value = 0.0
        self.loading_label.text = "Loading......"
        if self._anim_event:
            self._anim_event.cancel()
        self._anim_event = Clock.schedule_interval(self._animate_loading_bar, 35 / 1000)

    def _animate_loading_bar(self, dt):
        if self.progress_bar.value < 1.0:
            self.progress_bar.value = min(self.progress_bar.value + self._step, 1.0)
        else:
            self._anim_event.cancel()
            self.loading_label.text = "Done!"
            Clock.schedule_once(self._go_next, 0.5)

    def _go_next(self, dt):
        if self.manager:
            self.manager.current = NEXT_SCREEN
        else:
            print(f"(standalone) would navigate to: {NEXT_SCREEN}")


# ---------------------------------------------------------------------
# Standalone preview — lets you run just this file to see the splash
# screen on its own, without the rest of the app.
# ---------------------------------------------------------------------
if __name__ == "__main__":
    from kivy.app import App
    from kivy.uix.screenmanager import ScreenManager
    from kivy.core.window import Window

    class PlaceholderScreen(Screen):
        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            self.add_widget(Label(text="Role Selection Screen\n(placeholder)",
                                   color=(0, 0, 0, 1)))

    class SplashPreviewApp(App):
        def build(self):
            # Force a phone-like portrait window size for desktop preview.
            Window.size = (360, 640)
            Window.clearcolor = (1, 1, 1, 1)
            sm = ScreenManager()
            sm.add_widget(SplashScreen(name="splash"))
            sm.add_widget(PlaceholderScreen(name="role_selection"))
            sm.current = "splash"
            return sm

    SplashPreviewApp().run()