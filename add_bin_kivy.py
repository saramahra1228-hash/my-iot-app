"""
Add New Bin Screen — Smart Waste Monitor
--------------------------------------------------------------------
Firebase-connected Kivy screen.

Saves a new bin to:
    Firebase Realtime Database -> bins/<bin_id>

Fields:
- Bin ID
- Bin Name
- Latitude
- Longitude

New bins start with:
- fill_level = 0
- status = "empty"

The existing Admin Panel design/navigation is preserved.
"""

import threading
from datetime import datetime

from kivy.clock import Clock
from kivy.metrics import dp, sp
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.widget import Widget
from kivy.graphics import Color, Rectangle, RoundedRectangle

try:
    from firebase_config import get_data, update_data
except Exception as exc:
    print("[ADD BIN] Firebase import failed:", exc)
    get_data = None
    update_data = None


DARK_GREEN = (0 / 255, 77 / 255, 52 / 255, 1)
WHITE = (1, 1, 1, 1)
BG = (249 / 255, 249 / 255, 249 / 255, 1)
TEXT_DARK = (51 / 255, 51 / 255, 51 / 255, 1)
GRAY = (110 / 255, 110 / 255, 110 / 255, 1)
RED = (211 / 255, 47 / 255, 47 / 255, 1)
GREEN = (46 / 255, 125 / 255, 50 / 255, 1)


class AddBinScreen(Screen):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        root = BoxLayout(orientation="vertical")

        with root.canvas.before:
            Color(*BG)
            self._bg = Rectangle(pos=root.pos, size=root.size)

        root.bind(
            pos=lambda w, *_: setattr(self._bg, "pos", w.pos),
            size=lambda w, *_: setattr(self._bg, "size", w.size),
        )

        # -------------------------------------------------------- #
        # HEADER
        # -------------------------------------------------------- #
        header = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(65),
            padding=(dp(14), 0),
        )

        with header.canvas.before:
            Color(*DARK_GREEN)
            header_bg = Rectangle(
                pos=header.pos,
                size=header.size,
            )

        header.bind(
            pos=lambda w, *_: setattr(header_bg, "pos", w.pos),
            size=lambda w, *_: setattr(header_bg, "size", w.size),
        )

        back_btn = Button(
            text="‹",
            font_size=sp(34),
            color=WHITE,
            background_normal="",
            background_color=(0, 0, 0, 0),
            size_hint_x=None,
            width=dp(45),
        )
        back_btn.bind(on_release=self._go_back)

        title = Label(
            text="Add New Bin",
            font_size=sp(19),
            bold=True,
            color=WHITE,
            halign="center",
            valign="middle",
        )
        title.bind(
            size=lambda w, *_: setattr(w, "text_size", w.size)
        )

        header.add_widget(back_btn)
        header.add_widget(title)
        header.add_widget(
            Widget(size_hint_x=None, width=dp(45))
        )

        root.add_widget(header)

        # -------------------------------------------------------- #
        # FORM
        # -------------------------------------------------------- #
        content = BoxLayout(
            orientation="vertical",
            padding=(dp(24), dp(22)),
            spacing=dp(7),
        )

        content.add_widget(
            Label(
                text="Create a new waste bin",
                font_size=sp(16),
                bold=True,
                color=TEXT_DARK,
                size_hint_y=None,
                height=dp(28),
                halign="left",
            )
        )

        content.add_widget(
            Label(
                text="Enter the bin details. The new bin will be saved to Firebase.",
                font_size=sp(10.5),
                color=GRAY,
                size_hint_y=None,
                height=dp(34),
                halign="left",
                valign="middle",
            )
        )

        content.add_widget(
            Widget(size_hint_y=None, height=dp(5))
        )

        self.bin_id = self._make_input("Bin ID", "e.g. BIN_001")
        content.add_widget(self._make_label("Bin ID"))
        content.add_widget(self.bin_id)

        self.bin_name = self._make_input("Bin Name", "e.g. Bin 001")
        content.add_widget(self._make_label("Bin Name"))
        content.add_widget(self.bin_name)

        self.latitude = self._make_input("Latitude", "e.g. 33.7714")
        content.add_widget(self._make_label("Latitude"))
        content.add_widget(self.latitude)

        self.longitude = self._make_input("Longitude", "e.g. 72.7518")
        content.add_widget(self._make_label("Longitude"))
        content.add_widget(self.longitude)

        content.add_widget(
            Widget(size_hint_y=None, height=dp(4))
        )

        self.status_lbl = Label(
            text="",
            font_size=sp(11),
            color=RED,
            size_hint_y=None,
            height=dp(32),
            halign="center",
            valign="middle",
        )
        self.status_lbl.bind(
            size=lambda w, *_: setattr(w, "text_size", w.size)
        )
        content.add_widget(self.status_lbl)

        save_btn = Button(
            text="SAVE BIN",
            font_size=sp(15),
            bold=True,
            color=WHITE,
            background_normal="",
            background_color=list(DARK_GREEN),
            size_hint_y=None,
            height=dp(48),
        )
        save_btn.bind(on_release=self._save_bin)
        content.add_widget(save_btn)

        content.add_widget(Widget())

        root.add_widget(content)
        self.add_widget(root)

    # ------------------------------------------------------------ #
    # UI helpers
    # ------------------------------------------------------------ #
    def _make_label(self, text):
        lbl = Label(
            text=text,
            font_size=sp(12.5),
            bold=True,
            color=TEXT_DARK,
            size_hint_y=None,
            height=dp(23),
            halign="left",
            valign="middle",
        )
        lbl.bind(
            size=lambda w, *_: setattr(w, "text_size", w.size)
        )
        return lbl

    def _make_input(self, hint, helper_text):
        return TextInput(
            hint_text=f"{hint}  ({helper_text})",
            font_size=sp(13),
            multiline=False,
            padding=(dp(12), dp(10)),
            size_hint_y=None,
            height=dp(44),
            background_normal="",
            background_active="",
            background_color=WHITE,
            foreground_color=TEXT_DARK,
            hint_text_color=(0.55, 0.55, 0.55, 1),
            cursor_color=DARK_GREEN,
        )

    # ------------------------------------------------------------ #
    # Firebase save
    # ------------------------------------------------------------ #
    def _save_bin(self, *_):
        bin_id = self.bin_id.text.strip()
        bin_name = self.bin_name.text.strip()
        latitude_text = self.latitude.text.strip()
        longitude_text = self.longitude.text.strip()

        if not bin_id:
            self._set_error("Bin ID is required.")
            return

        if not bin_name:
            self._set_error("Bin Name is required.")
            return

        try:
            latitude = float(latitude_text)
        except ValueError:
            self._set_error("Latitude must be a valid number.")
            return

        try:
            longitude = float(longitude_text)
        except ValueError:
            self._set_error("Longitude must be a valid number.")
            return

        if not -90 <= latitude <= 90:
            self._set_error("Latitude must be between -90 and 90.")
            return

        if not -180 <= longitude <= 180:
            self._set_error("Longitude must be between -180 and 180.")
            return

        if get_data is None or update_data is None:
            self._set_error("Firebase service unavailable.")
            return

        self.status_lbl.text = "Checking bin..."
        self.status_lbl.color = list(GRAY)

        # Network work runs in background so the Kivy window does not freeze.
        threading.Thread(
            target=self._firebase_save_worker,
            args=(bin_id, bin_name, latitude, longitude),
            daemon=True,
        ).start()

    def _firebase_save_worker(
        self,
        bin_id,
        bin_name,
        latitude,
        longitude,
    ):
        try:
            # Check both likely bin roots before creating a record.
            existing = None

            for path in (
                f"bins/{bin_id}",
                f"waste_bins/{bin_id}",
                f"bin_data/{bin_id}",
            ):
                try:
                    result = get_data(path)

                    if isinstance(result, tuple) and len(result) >= 2:
                        success, data = result[0], result[1]
                    else:
                        success, data = True, result

                    if success and data not in (None, {}, []):
                        existing = data
                        break

                except Exception as exc:
                    print(
                        f"[ADD BIN] Existing-bin check failed for {path}:",
                        exc,
                    )

            if existing not in (None, {}, []):
                Clock.schedule_once(
                    lambda dt: self._set_error(
                        "This Bin ID already exists."
                    ),
                    0,
                )
                return

            now = datetime.now().isoformat(timespec="seconds")

            bin_data = {
                "bin_id": bin_id,
                "name": bin_name,
                "latitude": latitude,
                "longitude": longitude,
                "fill_level": 0,
                "status": "empty",
                "created_at": now,
                "updated_at": now,
            }

            result = update_data(
                f"bins/{bin_id}",
                bin_data,
            )

            if isinstance(result, tuple) and len(result) >= 2:
                success, response = result[0], result[1]
            else:
                success, response = True, result

            if success:
                Clock.schedule_once(
                    lambda dt: self._save_success(bin_id),
                    0,
                )
            else:
                Clock.schedule_once(
                    lambda dt, r=response: self._set_error(
                        f"Unable to save bin: {r}"
                    ),
                    0,
                )

        except Exception as exc:
            print("[ADD BIN] Firebase save error:", exc)

            Clock.schedule_once(
                lambda dt, e=str(exc): self._set_error(
                    "Unable to save bin. Check Firebase connection."
                ),
                0,
            )

    def _save_success(self, bin_id):
        self.status_lbl.text = (
            f"{bin_id} added successfully!"
        )
        self.status_lbl.color = list(GREEN)

        # Return to Admin Panel after a short confirmation.
        Clock.schedule_once(
            lambda dt: self._go_back(),
            1.0,
        )

    def _set_error(self, message):
        self.status_lbl.text = message
        self.status_lbl.color = list(RED)

    # ------------------------------------------------------------ #
    # Navigation
    # ------------------------------------------------------------ #
    def _go_back(self, *_):
        if self.manager and "admin_panel" in self.manager.screen_names:
            self.manager.current = "admin_panel"
        elif self.manager and "admin_dashboard" in self.manager.screen_names:
            self.manager.current = "admin_dashboard"
        else:
            print("Admin Panel screen is not registered.")


if __name__ == "__main__":
    pass
