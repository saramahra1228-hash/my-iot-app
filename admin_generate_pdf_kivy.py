"""
Admin Generate PDF Screen — Firebase Connected
----------------------------------------------
Generates a real PDF report from live Firebase data.

Firebase sources:
- bins
- staff
- assignments

Register in main.py:
    from admin_generate_pdf_kivy import GeneratePDFScreen
    sm.add_widget(GeneratePDFScreen(name="generate_pdf"))
"""

import os
import threading
from datetime import datetime

from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.graphics import Color, Rectangle, RoundedRectangle
from kivy.clock import Clock
from kivy.metrics import dp, sp

from admin_dashboard_kivy import (
    BottomNav,
    BG,
    DARK_GREEN,
    WHITE,
    TEXT_DARK,
)
from admin_panel_kivy import PanelHeader


# =========================================================
# FIREBASE
# =========================================================

try:
    from firebase_config import get_data
except Exception as exc:
    print("[PDF] Firebase import failed:", exc)
    get_data = None


# =========================================================
# REPORTLAB
# =========================================================

try:
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import (
        getSampleStyleSheet,
        ParagraphStyle,
    )
    from reportlab.lib.units import mm
    from reportlab.platypus import (
        SimpleDocTemplate,
        Paragraph,
        Spacer,
        Table,
        TableStyle,
    )

    REPORTLAB_AVAILABLE = True

except Exception as exc:
    print("[PDF] ReportLab import failed:", exc)
    REPORTLAB_AVAILABLE = False


# =========================================================
# FIREBASE PATHS
# =========================================================

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
)

ASSIGNMENT_PATHS = (
    "assignments",
    "bin_assignments",
    "staff_assignments",
)


# =========================================================
# HELPERS
# =========================================================

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
            print(f"[PDF] Read failed {path}: {exc}")

    return None


def records(data):
    if isinstance(data, list):
        return [
            item
            for item in data
            if isinstance(item, dict)
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


def safe_text(value, default="-"):
    text = str(
        value
        if value not in (None, "")
        else default
    )

    return (
        text
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


# =========================================================
# INFO CARD
# =========================================================

class InfoCard(BoxLayout):

    def __init__(self, title, value="0", **kwargs):

        super().__init__(
            orientation="vertical",
            padding=(dp(12), dp(9)),
            spacing=dp(3),
            size_hint_y=None,
            height=dp(68),
            **kwargs
        )

        with self.canvas.before:
            Color(1, 1, 1, 1)

            self.bg = RoundedRectangle(
                pos=self.pos,
                size=self.size,
                radius=[dp(12)],
            )

        self.bind(
            pos=self._sync,
            size=self._sync,
        )

        self.value_lbl = Label(
            text=value,
            font_size=sp(21),
            bold=True,
            color=DARK_GREEN,
            size_hint_y=None,
            height=dp(29),
            halign="left",
            valign="middle",
        )

        self.title_lbl = Label(
            text=title,
            font_size=sp(10.5),
            color=(0.35, 0.35, 0.35, 1),
            halign="left",
            valign="middle",
        )

        self.title_lbl.bind(
            size=lambda w, *_:
            setattr(w, "text_size", w.size)
        )

        self.add_widget(self.value_lbl)
        self.add_widget(self.title_lbl)

    def _sync(self, *_):
        self.bg.pos = self.pos
        self.bg.size = self.size


# =========================================================
# SCREEN
# =========================================================

class GeneratePDFScreen(Screen):

    NAV_ROUTES = {
        0: "admin_dashboard",
        1: "admin_map",
        2: "admin_panel",
        3: "admin_profile",
    }

    def __init__(self, **kwargs):

        super().__init__(**kwargs)

        self._generating = False
        self._summary_loading = False

        # =================================================
        # ROOT
        # =================================================

        root = BoxLayout(
            orientation="vertical",
            spacing=0,
        )

        with root.canvas.before:
            Color(*BG)

            self.root_bg = Rectangle(
                pos=root.pos,
                size=root.size,
            )

        root.bind(
            pos=lambda w, *_:
            setattr(self.root_bg, "pos", w.pos),

            size=lambda w, *_:
            setattr(self.root_bg, "size", w.size),
        )

        # =================================================
        # HEADER
        # =================================================

        header = PanelHeader(
            "Generate PDF",
            on_back=self._go_back,
        )

        # IMPORTANT:
        # Force header to fixed height.
        header.size_hint_y = None
        header.height = dp(62)

        root.add_widget(header)

        # =================================================
        # STATUS
        # =================================================

        self.status = Label(
            text="Ready to generate PDF report",
            font_size=sp(10),
            color=(0.35, 0.35, 0.35, 1),
            size_hint_y=None,
            height=dp(30),
            halign="center",
            valign="middle",
        )

        self.status.bind(
            size=lambda w, *_:
            setattr(w, "text_size", w.size)
        )

        root.add_widget(self.status)

        # =================================================
        # SCROLL VIEW
        # =================================================

        scroll = ScrollView(
            do_scroll_x=False,
            do_scroll_y=True,
            bar_width=dp(4),
        )

        content = GridLayout(
            cols=1,
            padding=(
                dp(16),
                dp(10),
                dp(16),
                dp(18),
            ),
            spacing=dp(10),
            size_hint_y=None,
        )

        content.bind(
            minimum_height=content.setter("height")
        )

        scroll.add_widget(content)

        # =================================================
        # TITLE
        # =================================================

        title = Label(
            text="Smart Waste Management Report",
            font_size=sp(16),
            bold=True,
            color=DARK_GREEN,
            size_hint_y=None,
            height=dp(34),
            halign="left",
            valign="middle",
        )

        title.bind(
            size=lambda w, *_:
            setattr(w, "text_size", w.size)
        )

        content.add_widget(title)

        # =================================================
        # SUBTITLE
        # =================================================

        subtitle = Label(
            text=(
                "Generate a PDF using the latest data "
                "stored in Firebase.\n\n"
                "The report contains summary statistics, "
                "bin status and worker assignments."
            ),
            font_size=sp(10.5),
            color=TEXT_DARK,
            size_hint_y=None,
            height=dp(70),
            halign="left",
            valign="middle",
        )

        subtitle.bind(
            size=lambda w, *_:
            setattr(w, "text_size", w.size)
        )

        content.add_widget(subtitle)

        # =================================================
        # STATISTICS
        # =================================================

        stats = GridLayout(
            cols=2,
            spacing=dp(9),
            size_hint_y=None,
            height=dp(146),
        )

        self.cards = {
            "bins": InfoCard("Total Bins"),
            "staff": InfoCard("Total Staff"),
            "assigned": InfoCard("Assigned Bins"),
            "pending": InfoCard("Pending"),
        }

        for card in self.cards.values():
            stats.add_widget(card)

        content.add_widget(stats)

        # =================================================
        # GENERATE BUTTON
        # =================================================

        self.generate_btn = Button(
            text="GENERATE PDF REPORT",
            size_hint_y=None,
            height=dp(50),
            font_size=sp(13),
            bold=True,
            color=WHITE,
            background_normal="",
            background_color=DARK_GREEN,
        )

        self.generate_btn.bind(
            on_release=lambda *_:
            self.generate_pdf()
        )

        content.add_widget(self.generate_btn)

        # =================================================
        # FILE STATUS
        # =================================================

        self.file_label = Label(
            text="PDF file: Not generated yet",
            font_size=sp(10.5),
            color=(0.35, 0.35, 0.35, 1),
            size_hint_y=None,
            height=dp(62),
            halign="left",
            valign="middle",
        )

        self.file_label.bind(
            size=lambda w, *_:
            setattr(w, "text_size", w.size)
        )

        content.add_widget(self.file_label)

        # =================================================
        # EXTRA INFORMATION CARD
        # =================================================

        info_box = BoxLayout(
            orientation="vertical",
            padding=(dp(12), dp(8)),
            size_hint_y=None,
            height=dp(72),
        )

        with info_box.canvas.before:
            Color(1, 1, 1, 1)

            info_bg = RoundedRectangle(
                pos=info_box.pos,
                size=info_box.size,
                radius=[dp(10)],
            )

        info_box.bind(
            pos=lambda w, *_:
            setattr(info_bg, "pos", w.pos),

            size=lambda w, *_:
            setattr(info_bg, "size", w.size),
        )

        info_title = Label(
            text="PDF Report Includes",
            font_size=sp(11),
            bold=True,
            color=DARK_GREEN,
            size_hint_y=None,
            height=dp(22),
            halign="left",
        )

        info_title.bind(
            size=lambda w, *_:
            setattr(w, "text_size", w.size)
        )

        info_text = Label(
            text=(
                "✓ Firebase summary   "
                "✓ Bin status   "
                "✓ Worker assignments"
            ),
            font_size=sp(9.5),
            color=TEXT_DARK,
            halign="left",
            valign="middle",
        )

        info_text.bind(
            size=lambda w, *_:
            setattr(w, "text_size", w.size)
        )

        info_box.add_widget(info_title)
        info_box.add_widget(info_text)

        content.add_widget(info_box)

        # =================================================
        # ADD SCROLL TO ROOT
        # =================================================

        root.add_widget(scroll)

        # =================================================
        # BOTTOM NAV
        # =================================================

        nav = BottomNav(
            on_nav=self._on_nav
        )

        # IMPORTANT:
        # Force bottom navigation to fixed height.
        nav.size_hint_y = None
        nav.height = dp(62)

        for i, btn in enumerate(nav.buttons):
            btn.set_active(i == 2)

        root.add_widget(nav)

        # =================================================
        # ADD ROOT TO SCREEN
        # =================================================

        self.add_widget(root)

    # =====================================================
    # ENTER
    # =====================================================

    def on_enter(self, *args):

        # Give Kivy one frame to finish layout first.
        Clock.schedule_once(
            lambda dt:
            self.load_summary(),
            0.15,
        )

    # =====================================================
    # LOAD SUMMARY
    # =====================================================

    def load_summary(self):

        if self._summary_loading:
            return

        if get_data is None:
            self.status.text = (
                "Firebase service unavailable"
            )

            self.status.color = (
                0.8,
                0.15,
                0.15,
                1,
            )

            return

        self._summary_loading = True

        self.status.text = (
            "Loading live Firebase data..."
        )

        self.status.color = (
            0.35,
            0.35,
            0.35,
            1,
        )

        threading.Thread(
            target=self._summary_worker,
            daemon=True,
        ).start()

    # =====================================================
    # SUMMARY WORKER
    # =====================================================

    def _summary_worker(self):

        try:

            bins = records(
                read_first(BIN_PATHS)
            )

            staff = records(
                read_first(STAFF_PATHS)
            )

            assignments = records(
                read_first(ASSIGNMENT_PATHS)
            )

            assigned_ids = set()
            pending = 0

            for assignment in assignments:

                bid = str(
                    assignment.get("bin_id")
                    or assignment.get("binId")
                    or ""
                ).strip()

                if bid:
                    assigned_ids.add(bid)

                status = str(
                    assignment.get("status")
                    or "assigned"
                ).lower()

                if status not in (
                    "collected",
                    "completed",
                    "done",
                ):
                    pending += 1

            # Direct bin assignment
            for b in bins:

                bid = str(
                    b.get("bin_id")
                    or b.get("_id")
                    or ""
                ).strip()

                if (
                    b.get("assigned_worker_id")
                    or b.get("assigned_worker_uid")
                ) and bid:

                    assigned_ids.add(bid)

            payload = {
                "bins": len(bins),
                "staff": len(staff),
                "assigned": len(assigned_ids),
                "pending": pending,
            }

            Clock.schedule_once(
                lambda dt, p=payload:
                self._apply_summary(p),
                0,
            )

        except Exception as exc:

            print(
                "[PDF] Summary error:",
                exc,
            )

            Clock.schedule_once(
                lambda dt, e=str(exc):
                self._show_error(e),
                0,
            )

        finally:

            Clock.schedule_once(
                lambda dt:
                setattr(
                    self,
                    "_summary_loading",
                    False,
                ),
                0,
            )

    # =====================================================
    # APPLY SUMMARY
    # =====================================================

    def _apply_summary(self, payload):

        self.cards["bins"].value_lbl.text = str(
            payload["bins"]
        )

        self.cards["staff"].value_lbl.text = str(
            payload["staff"]
        )

        self.cards["assigned"].value_lbl.text = str(
            payload["assigned"]
        )

        self.cards["pending"].value_lbl.text = str(
            payload["pending"]
        )

        self.status.text = (
            "Firebase Connected • "
            "Ready to generate PDF"
        )

        self.status.color = (
            0.18,
            0.50,
            0.30,
            1,
        )

    # =====================================================
    # GENERATE PDF
    # =====================================================

    def generate_pdf(self):

        if self._generating:
            return

        if get_data is None:

            self._show_error(
                "Firebase service unavailable."
            )

            return

        if not REPORTLAB_AVAILABLE:

            self._show_error(
                "ReportLab is not installed.\n"
                "Run: pip install reportlab"
            )

            return

        self._generating = True

        self.generate_btn.disabled = True
        self.generate_btn.text = (
            "GENERATING PDF..."
        )

        self.status.text = (
            "Fetching live Firebase data..."
        )

        self.status.color = (
            0.35,
            0.35,
            0.35,
            1,
        )

        threading.Thread(
            target=self._generate_worker,
            daemon=True,
        ).start()

    # =====================================================
    # PDF WORKER
    # =====================================================

    def _generate_worker(self):

        try:

            bins = records(
                read_first(BIN_PATHS)
            )

            staff = records(
                read_first(STAFF_PATHS)
            )

            assignments = records(
                read_first(ASSIGNMENT_PATHS)
            )

            assigned_ids = set()
            collected = 0
            pending = 0

            # -------------------------------------------------
            # ASSIGNMENTS
            # -------------------------------------------------

            for assignment in assignments:

                bid = str(
                    assignment.get("bin_id")
                    or assignment.get("binId")
                    or ""
                ).strip()

                if bid:
                    assigned_ids.add(bid)

                status = str(
                    assignment.get("status")
                    or "assigned"
                ).lower()

                if status in (
                    "collected",
                    "completed",
                    "done",
                ):
                    collected += 1

                else:
                    pending += 1

            # -------------------------------------------------
            # DIRECT BIN ASSIGNMENTS
            # -------------------------------------------------

            for b in bins:

                bid = str(
                    b.get("bin_id")
                    or b.get("_id")
                    or ""
                ).strip()

                if (
                    b.get("assigned_worker_id")
                    or b.get("assigned_worker_uid")
                ) and bid:

                    assigned_ids.add(bid)

            # -------------------------------------------------
            # BIN STATUS
            # -------------------------------------------------

            full = 0
            medium = 0
            low = 0

            bin_rows = []

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
                    b.get("fillLevel", 0),
                )

                try:
                    fill = float(raw_fill)

                except Exception:
                    fill = 0

                if fill >= 80:

                    full += 1
                    status = "Full"

                elif fill >= 40:

                    medium += 1
                    status = "Medium"

                else:

                    low += 1
                    status = "Low"

                explicit = str(
                    b.get("status")
                    or ""
                ).strip()

                if explicit:
                    status = explicit.title()

                worker = str(
                    b.get("assigned_worker_name")
                    or b.get("assigned_worker_id")
                    or "-"
                )

                bin_rows.append(
                    [
                        safe_text(bid),
                        safe_text(name),
                        f"{fill:g}%",
                        safe_text(status),
                        safe_text(worker),
                    ]
                )

            bin_rows.sort(
                key=lambda row: row[0]
            )

            # -------------------------------------------------
            # ASSIGNMENT ROWS
            # -------------------------------------------------

            assignment_rows = []

            for a in assignments:

                assignment_rows.append(
                    [
                        safe_text(
                            a.get("bin_id")
                            or a.get("binId")
                            or "-"
                        ),

                        safe_text(
                            a.get("staff_name")
                            or a.get("staff_id")
                            or a.get("staff_uid")
                            or "-"
                        ),

                        safe_text(
                            a.get("status")
                            or "assigned"
                        ).title(),

                        safe_text(
                            a.get("assigned_at")
                            or a.get("updated_at")
                            or "-"
                        ),
                    ]
                )

            assignment_rows.sort(
                key=lambda row: row[0]
            )

            # -------------------------------------------------
            # OUTPUT DIRECTORY
            # -------------------------------------------------

            output_dir = os.path.join(
                os.getcwd(),
                "generated_reports",
            )

            os.makedirs(
                output_dir,
                exist_ok=True,
            )

            timestamp = datetime.now().strftime(
                "%Y%m%d_%H%M%S"
            )

            output_path = os.path.join(
                output_dir,
                f"smart_waste_report_{timestamp}.pdf",
            )

            # -------------------------------------------------
            # BUILD PDF
            # -------------------------------------------------

            self._build_pdf(
                output_path=output_path,
                bins=bins,
                staff=staff,
                assignments=assignments,
                assigned_count=len(assigned_ids),
                pending=pending,
                collected=collected,
                full=full,
                medium=medium,
                low=low,
                bin_rows=bin_rows,
                assignment_rows=assignment_rows,
            )

            payload = {
                "path": output_path,
                "bins": len(bins),
                "staff": len(staff),
                "assignments": len(assignments),
            }

            Clock.schedule_once(
                lambda dt, p=payload:
                self._pdf_success(p),
                0,
            )

        except Exception as exc:

            print(
                "[PDF] Generation error:",
                exc,
            )

            Clock.schedule_once(
                lambda dt, e=str(exc):
                self._show_error(e),
                0,
            )

    # =====================================================
    # BUILD PDF
    # =====================================================

    def _build_pdf(
        self,
        output_path,
        bins,
        staff,
        assignments,
        assigned_count,
        pending,
        collected,
        full,
        medium,
        low,
        bin_rows,
        assignment_rows,
    ):

        styles = getSampleStyleSheet()

        title_style = ParagraphStyle(
            "ReportTitle",
            parent=styles["Title"],
            fontSize=20,
            leading=24,
            alignment=TA_CENTER,
            textColor=colors.HexColor(
                "#176B45"
            ),
            spaceAfter=8,
        )

        subtitle_style = ParagraphStyle(
            "ReportSubtitle",
            parent=styles["Normal"],
            fontSize=9,
            leading=12,
            alignment=TA_CENTER,
            textColor=colors.HexColor(
                "#666666"
            ),
            spaceAfter=14,
        )

        section_style = ParagraphStyle(
            "Section",
            parent=styles["Heading2"],
            fontSize=13,
            leading=16,
            textColor=colors.HexColor(
                "#176B45"
            ),
            spaceBefore=10,
            spaceAfter=7,
        )

        normal_style = ParagraphStyle(
            "NormalSmall",
            parent=styles["Normal"],
            fontSize=9,
            leading=12,
        )

        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            rightMargin=14 * mm,
            leftMargin=14 * mm,
            topMargin=14 * mm,
            bottomMargin=14 * mm,
            title="Smart Waste Management Report",
            author="My IoT App",
        )

        story = []

        generated_at = datetime.now().strftime(
            "%d-%m-%Y %I:%M:%S %p"
        )

        story.append(
            Paragraph(
                "Smart Waste Management Report",
                title_style,
            )
        )

        story.append(
            Paragraph(
                f"Generated from Firebase • "
                f"{generated_at}",
                subtitle_style,
            )
        )

        # =================================================
        # SUMMARY TABLE
        # =================================================

        summary_data = [
            [
                "Metric",
                "Value",
                "Metric",
                "Value",
            ],
            [
                "Total Bins",
                str(len(bins)),
                "Total Staff",
                str(len(staff)),
            ],
            [
                "Assigned Bins",
                str(assigned_count),
                "Pending",
                str(pending),
            ],
            [
                "Collected",
                str(collected),
                "Full",
                str(full),
            ],
            [
                "Medium",
                str(medium),
                "Low",
                str(low),
            ],
        ]

        summary_table = Table(
            summary_data,
            colWidths=[
                38 * mm,
                25 * mm,
                38 * mm,
                25 * mm,
            ],
            repeatRows=1,
        )

        summary_table.setStyle(
            TableStyle(
                [
                    (
                        "BACKGROUND",
                        (0, 0),
                        (-1, 0),
                        colors.HexColor("#176B45"),
                    ),
                    (
                        "TEXTCOLOR",
                        (0, 0),
                        (-1, 0),
                        colors.white,
                    ),
                    (
                        "FONTNAME",
                        (0, 0),
                        (-1, 0),
                        "Helvetica-Bold",
                    ),
                    (
                        "FONTNAME",
                        (0, 1),
                        (-1, -1),
                        "Helvetica",
                    ),
                    (
                        "FONTSIZE",
                        (0, 0),
                        (-1, -1),
                        8.5,
                    ),
                    (
                        "GRID",
                        (0, 0),
                        (-1, -1),
                        0.5,
                        colors.HexColor("#D6DED9"),
                    ),
                    (
                        "BACKGROUND",
                        (0, 1),
                        (-1, -1),
                        colors.HexColor("#F5F8F6"),
                    ),
                    (
                        "VALIGN",
                        (0, 0),
                        (-1, -1),
                        "MIDDLE",
                    ),
                    (
                        "TOPPADDING",
                        (0, 0),
                        (-1, -1),
                        6,
                    ),
                    (
                        "BOTTOMPADDING",
                        (0, 0),
                        (-1, -1),
                        6,
                    ),
                ]
            )
        )

        story.append(summary_table)

        # =================================================
        # BIN STATUS
        # =================================================

        story.append(
            Paragraph(
                "Bin Status",
                section_style,
            )
        )

        if bin_rows:

            bin_table_data = [
                [
                    "Bin ID",
                    "Name",
                    "Fill",
                    "Status",
                    "Assigned Worker",
                ]
            ] + bin_rows

        else:

            bin_table_data = [
                [
                    "Bin ID",
                    "Name",
                    "Fill",
                    "Status",
                    "Assigned Worker",
                ],
                [
                    "-",
                    "No bins found",
                    "-",
                    "-",
                    "-",
                ],
            ]

        bin_table = Table(
            bin_table_data,
            colWidths=[
                27 * mm,
                39 * mm,
                18 * mm,
                24 * mm,
                57 * mm,
            ],
            repeatRows=1,
        )

        bin_table.setStyle(
            TableStyle(
                [
                    (
                        "BACKGROUND",
                        (0, 0),
                        (-1, 0),
                        colors.HexColor("#176B45"),
                    ),
                    (
                        "TEXTCOLOR",
                        (0, 0),
                        (-1, 0),
                        colors.white,
                    ),
                    (
                        "FONTNAME",
                        (0, 0),
                        (-1, 0),
                        "Helvetica-Bold",
                    ),
                    (
                        "FONTSIZE",
                        (0, 0),
                        (-1, -1),
                        7.5,
                    ),
                    (
                        "GRID",
                        (0, 0),
                        (-1, -1),
                        0.35,
                        colors.HexColor("#CDD7D1"),
                    ),
                    (
                        "VALIGN",
                        (0, 0),
                        (-1, -1),
                        "MIDDLE",
                    ),
                    (
                        "ROWBACKGROUNDS",
                        (0, 1),
                        (-1, -1),
                        [
                            colors.white,
                            colors.HexColor("#F5F8F6"),
                        ],
                    ),
                    (
                        "TOPPADDING",
                        (0, 0),
                        (-1, -1),
                        5,
                    ),
                    (
                        "BOTTOMPADDING",
                        (0, 0),
                        (-1, -1),
                        5,
                    ),
                ]
            )
        )

        story.append(bin_table)

        # =================================================
        # WORKER ASSIGNMENTS
        # =================================================

        story.append(
            Paragraph(
                "Worker Assignments",
                section_style,
            )
        )

        if assignment_rows:

            assignment_table_data = [
                [
                    "Bin ID",
                    "Worker",
                    "Status",
                    "Assigned / Updated",
                ]
            ] + assignment_rows

        else:

            assignment_table_data = [
                [
                    "Bin ID",
                    "Worker",
                    "Status",
                    "Assigned / Updated",
                ],
                [
                    "-",
                    "No assignments found",
                    "-",
                    "-",
                ],
            ]

        assignment_table = Table(
            assignment_table_data,
            colWidths=[
                30 * mm,
                50 * mm,
                30 * mm,
                55 * mm,
            ],
            repeatRows=1,
        )

        assignment_table.setStyle(
            TableStyle(
                [
                    (
                        "BACKGROUND",
                        (0, 0),
                        (-1, 0),
                        colors.HexColor("#176B45"),
                    ),
                    (
                        "TEXTCOLOR",
                        (0, 0),
                        (-1, 0),
                        colors.white,
                    ),
                    (
                        "FONTNAME",
                        (0, 0),
                        (-1, 0),
                        "Helvetica-Bold",
                    ),
                    (
                        "FONTSIZE",
                        (0, 0),
                        (-1, -1),
                        7.5,
                    ),
                    (
                        "GRID",
                        (0, 0),
                        (-1, -1),
                        0.35,
                        colors.HexColor("#CDD7D1"),
                    ),
                    (
                        "VALIGN",
                        (0, 0),
                        (-1, -1),
                        "MIDDLE",
                    ),
                    (
                        "ROWBACKGROUNDS",
                        (0, 1),
                        (-1, -1),
                        [
                            colors.white,
                            colors.HexColor("#F5F8F6"),
                        ],
                    ),
                    (
                        "TOPPADDING",
                        (0, 0),
                        (-1, -1),
                        5,
                    ),
                    (
                        "BOTTOMPADDING",
                        (0, 0),
                        (-1, -1),
                        5,
                    ),
                ]
            )
        )

        story.append(assignment_table)

        story.append(
            Spacer(1, 12)
        )

        story.append(
            Paragraph(
                "This report was generated by My IoT App "
                "using live Firebase data.",
                normal_style,
            )
        )

        doc.build(story)

    # =====================================================
    # PDF SUCCESS
    # =====================================================

    def _pdf_success(self, payload):

        self._generating = False

        self.generate_btn.disabled = False

        self.generate_btn.text = (
            "GENERATE PDF REPORT"
        )

        self.status.text = (
            "PDF generated successfully • "
            f"{payload['bins']} bins • "
            f"{payload['assignments']} assignments"
        )

        self.status.color = (
            0.18,
            0.50,
            0.30,
            1,
        )

        self.file_label.text = (
            "PDF saved successfully:\n"
            f"{payload['path']}"
        )

    # =====================================================
    # ERROR
    # =====================================================

    def _show_error(self, error):

        self._generating = False

        self.generate_btn.disabled = False

        self.generate_btn.text = (
            "GENERATE PDF REPORT"
        )

        self.status.text = (
            "PDF generation failed"
        )

        self.status.color = (
            0.8,
            0.15,
            0.15,
            1,
        )

        self.file_label.text = str(error)

    # =====================================================
    # NAVIGATION
    # =====================================================

    def _on_nav(self, index):

        target = self.NAV_ROUTES.get(index)

        if (
            self.manager
            and target in self.manager.screen_names
        ):
            self.manager.current = target

    # =====================================================
    # BACK
    # =====================================================

    def _go_back(self):

        self._on_nav(2)


# =========================================================
# DIRECT RUN
# =========================================================

if __name__ == "__main__":
    pass

