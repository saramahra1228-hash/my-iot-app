"""
staff_task_history_kivy.py
Task History connected to the same local task-status file used by
staff_route_kivy.py. B-002 becomes Collected after staff presses
"Mark as Collected" on the Route screen.
"""

from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput
from kivy.graphics import Color, RoundedRectangle, Rectangle
from kivy.metrics import dp
import json
from pathlib import Path

HEADER_GREEN=(0/255,77/255,52/255,1)
BG_GRAY=(0.949,0.941,0.941,1)
CARD_WHITE=(1,1,1,1)
TODAY_BAR=(0.918,0.906,0.906,1)
TEXT_DARK=(0.13,0.13,0.13,1)
TEXT_GRAY=(0.45,0.45,0.45,1)
GREEN_STATUS=(0.30,0.69,0.31,1)
YELLOW_STATUS=(0.90,0.62,0.03,1)
RED_STATUS=(0.96,0.26,0.21,1)
TASK_STATUS_FILE="staff_task_status.json"

def load_statuses():
    try:
        p=Path(TASK_STATUS_FILE)
        if p.exists():
            d=json.loads(p.read_text(encoding="utf-8"))
            return d if isinstance(d,dict) else {}
    except Exception as e:
        print("History status read error:",e)
    return {}

class RoundedCard(BoxLayout):
    def __init__(self,bg_color=CARD_WHITE,radius=14,**kwargs):
        super().__init__(**kwargs)
        with self.canvas.before:
            Color(*bg_color)
            self._rect=RoundedRectangle(pos=self.pos,size=self.size,radius=[radius])
        self.bind(pos=self._update,size=self._update)
    def _update(self,*a):
        self._rect.pos=self.pos
        self._rect.size=self.size

class ClickableCard(ButtonBehavior,RoundedCard):
    pass

class StatCard(RoundedCard):
    def __init__(self,label_text,value_text,**kwargs):
        super().__init__(orientation="vertical",padding=(4,8),**kwargs)
        self.add_widget(Label(text=label_text,font_size="11sp",color=TEXT_GRAY,size_hint_y=.5))
        self.add_widget(Label(text=value_text,font_size="18sp",bold=True,color=TEXT_DARK,size_hint_y=.5))

class TaskCard(RoundedCard):
    def __init__(self,time_text,bin_id,address,status_text,status_color,**kwargs):
        super().__init__(orientation="horizontal",padding=(10,8),spacing=8,**kwargs)
        chip=RoundedCard(bg_color=TODAY_BAR,radius=8,size_hint_x=.24,padding=(4,4))
        chip.add_widget(Label(text=time_text,font_size="10sp",color=TEXT_DARK))
        self.add_widget(chip)
        details=BoxLayout(orientation="vertical",size_hint_x=.52)
        title=Label(text=bin_id,font_size="13sp",bold=True,color=TEXT_DARK,halign="left",valign="middle")
        addr=Label(text=address,font_size="11sp",color=TEXT_GRAY,halign="left",valign="middle")
        for x in (title,addr): x.bind(size=x.setter("text_size"))
        details.add_widget(title); details.add_widget(addr); self.add_widget(details)
        self.add_widget(Label(text=status_text,font_size="11sp",bold=True,color=status_color,size_hint_x=.24))

class StaffTaskHistoryScreen(Screen):
    def __init__(self,**kwargs):
        super().__init__(**kwargs)
        root=FloatLayout()
        with root.canvas.before:
            Color(*BG_GRAY); self._bg=Rectangle(pos=root.pos,size=root.size)
        root.bind(pos=self._bg_update,size=self._bg_update)
        main=BoxLayout(orientation="vertical")

        header=BoxLayout(orientation="horizontal",size_hint_y=None,height=dp(52),padding=(dp(8),dp(6)))
        with header.canvas.before:
            Color(*HEADER_GREEN); self._header=Rectangle(pos=header.pos,size=header.size)
        header.bind(pos=self._header_update,size=self._header_update)
        b=Button(text="<",font_size="18sp",size_hint=(None,None),size=(dp(36),dp(36)),
                 background_color=(0,0,0,0),background_normal="",color=(1,1,1,1))
        b.bind(on_press=lambda *_: self.safe_navigate("staff_dashboard"))
        header.add_widget(b)
        title=Label(text="Task History",font_size="17sp",bold=True,color=(1,1,1,1),halign="center",valign="middle")
        title.bind(size=title.setter("text_size")); header.add_widget(title)
        header.add_widget(Widget(size_hint=(None,None),size=(dp(36),dp(36))))
        main.add_widget(header)

        controls=BoxLayout(orientation="horizontal",size_hint_y=None,height=dp(46),padding=(dp(12),dp(6)),spacing=dp(8))
        date=ClickableCard(radius=8,padding=(10,4))
        self.date_label=Label(text="May 20 - May 26, 2026  v",font_size="11sp",color=TEXT_DARK)
        date.add_widget(self.date_label); date.bind(on_release=self.open_date_popup); controls.add_widget(date)
        search=ClickableCard(radius=8,size_hint_x=.32)
        search.add_widget(Label(text="Search",font_size="11sp",color=TEXT_GRAY)); search.bind(on_release=self.open_search_popup)
        controls.add_widget(search); main.add_widget(controls)

        self.stats=BoxLayout(orientation="horizontal",size_hint_y=None,height=dp(62),padding=(dp(12),0),spacing=dp(8))
        main.add_widget(self.stats)

        today=BoxLayout(size_hint_y=None,height=dp(34),padding=(dp(14),0))
        with today.canvas.before:
            Color(*TODAY_BAR); self._today=Rectangle(pos=today.pos,size=today.size)
        today.bind(pos=self._today_update,size=self._today_update)
        self.today_label=Label(text="Today - May 24, 2026",font_size="13sp",bold=True,color=TEXT_DARK,halign="left",valign="middle")
        self.today_label.bind(size=self.today_label.setter("text_size")); today.add_widget(self.today_label); main.add_widget(today)

        scroll=ScrollView()
        self.task_list=BoxLayout(orientation="vertical",size_hint_y=None,spacing=dp(10),padding=(dp(12),dp(10),dp(12),dp(18)))
        self.task_list.bind(minimum_height=self.task_list.setter("height")); scroll.add_widget(self.task_list); main.add_widget(scroll)
        root.add_widget(main); self.add_widget(root)

        self.all_tasks=[
            ("9:25 AM","Bin: B-001","Street 12, Green Park","Collected",GREEN_STATUS),
            ("9:55 AM","Bin: B-002","Street 16, Green Park","Pending",YELLOW_STATUS),
            ("10:05 AM","Bin: B-003","Street 20, Green Park","Pending",YELLOW_STATUS),
            ("9:55 AM","Bin: B-004","Street 07, Green Park","Skipped",RED_STATUS),
        ]
        self.refresh_history()

    def _bg_update(self,i,*a): self._bg.pos=i.pos; self._bg.size=i.size
    def _header_update(self,i,*a): self._header.pos=i.pos; self._header.size=i.size
    def _today_update(self,i,*a): self._today.pos=i.pos; self._today.size=i.size

    def safe_navigate(self,name):
        if self.manager and name in self.manager.screen_names: self.manager.current=name

    def refresh_history(self):
        statuses=load_statuses()
        rows=[]; completed=0; pending=0
        for t in self.all_tasks:
            key=t[1].replace("Bin:","").replace(" ","")
            status=statuses.get(key,t[3])
            color=GREEN_STATUS if status=="Collected" else RED_STATUS if status=="Skipped" else YELLOW_STATUS
            if status=="Collected": completed+=1
            elif status=="Pending": pending+=1
            rows.append((t[0],t[1],t[2],status,color))
        self.rebuild_task_list(rows)
        self.stats.clear_widgets()
        self.stats.add_widget(StatCard("Total Tasks",str(len(rows))))
        self.stats.add_widget(StatCard("Completed",str(completed)))
        self.stats.add_widget(StatCard("Pending",str(pending)))

    def rebuild_task_list(self,tasks):
        self.task_list.clear_widgets()
        if not tasks:
            self.task_list.add_widget(Label(text="No matching tasks found.",font_size="12sp",color=TEXT_GRAY,size_hint_y=None,height=dp(40))); return
        for t in tasks: self.task_list.add_widget(TaskCard(*t,size_hint_y=None,height=dp(70)))

    def on_enter(self,*a): self.refresh_history()

    def open_search_popup(self,*a):
        content=BoxLayout(orientation="vertical",spacing=dp(10),padding=dp(12))
        inp=TextInput(hint_text="Search by Bin ID or street...",multiline=False,size_hint_y=None,height=dp(40)); content.add_widget(inp)
        row=BoxLayout(size_hint_y=None,height=dp(42),spacing=dp(10))
        clear=Button(text="Clear"); go=Button(text="Search"); row.add_widget(clear); row.add_widget(go); content.add_widget(row)
        pop=Popup(title="Search Tasks",content=content,size_hint=(.85,.38))
        def do_search(*_):
            q=inp.text.strip().lower(); statuses=load_statuses(); rows=[]
            for t in self.all_tasks:
                key=t[1].replace("Bin:","").replace(" ",""); status=statuses.get(key,t[3])
                color=GREEN_STATUS if status=="Collected" else RED_STATUS if status=="Skipped" else YELLOW_STATUS
                if not q or q in t[1].lower() or q in t[2].lower(): rows.append((t[0],t[1],t[2],status,color))
            self.rebuild_task_list(rows); pop.dismiss()
        def do_clear(*_): self.refresh_history(); pop.dismiss()
        go.bind(on_release=do_search); clear.bind(on_release=do_clear); inp.bind(on_text_validate=do_search); pop.open()

    def open_date_popup(self,*a):
        ranges=[("May 20 - May 26, 2026","May 24, 2026"),("May 13 - May 19, 2026","May 17, 2026"),("May 6 - May 12, 2026","May 10, 2026"),("Apr 29 - May 5, 2026","May 3, 2026")]
        content=BoxLayout(orientation="vertical",spacing=dp(6),padding=dp(12))
        pop=Popup(title="Select Date Range",content=content,size_hint=(.85,.55))
        def handler(label,today,*_):
            self.date_label.text=f"{label}  v"; self.today_label.text=f"Today - {today}"; self.refresh_history(); pop.dismiss()
        for label,today in ranges:
            btn=Button(text=label,size_hint_y=None,height=dp(42)); btn.bind(on_release=lambda x,l=label,t=today: handler(l,t)); content.add_widget(btn)
        pop.open()
