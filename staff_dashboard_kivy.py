# UPDATED STAFF DASHBOARD — Firebase connected
# Full source based on your original file. Copy this entire file as staff_dashboard_kivy.py

import math
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.uix.behaviors import ButtonBehavior
from kivy.graphics import Color, Rectangle, RoundedRectangle, Line, Ellipse
from kivy.utils import get_color_from_hex as hexc
from kivy.metrics import dp, sp

# Firebase
try:
    from firebase_auth import get_current_user
    from firebase_config import get_data
except ImportError:
    get_current_user = None
    get_data = None

BACK_SCREEN = "staff_login"
ROUTE_SCREEN = "staff_route"
HISTORY_SCREEN = "staff_task_history"
PROFILE_SCREEN = "staff_profile"

GREEN = "#004D34"
TEXT_GRAY = "#777777"
ROUTE_BG = "#F9F9F9"
STATUS_GREEN = "#4CAF50"
STATUS_PENDING = "#FF5722"
NAV_ACTIVE = "#FFFFFF"
NAV_INACTIVE = "#A3C4B7"

CARD_DATA = [
    ("Assigned Bins", "48", "#E3F2FD", "bin", "#1E88E5"),
    ("Calculated", "28", "#E8F5E9", "bin", "#2E7D32"),
    ("Pending", "14", "#FFF3E0", "bin", "#FB8C00"),
    ("Today's collection", "1.6 Ton", "#E1F5FE", "truck", "#0277BD"),
]

ROUTE_DATA = [
    ("Bin :B-001", "Street 12, Green Park", "Collected", STATUS_GREEN),
    ("Bin :B-002", "Street 16, Green Park", "Pending", STATUS_PENDING),
    ("Bin :B-003", "Street 20, Green Park", "Pending", STATUS_PENDING),
]


class BackArrowIcon(ButtonBehavior, Widget):
    def __init__(self, color_hex="#000000", **kwargs):
        super().__init__(**kwargs)
        with self.canvas:
            Color(*hexc(color_hex))
            self._line = Line(width=dp(1.5), cap="round", joint="round")
        self.bind(pos=self._redraw, size=self._redraw)
        self._redraw()

    def _redraw(self, *args):
        x, y = self.pos
        w, h = self.size
        self._line.points = [
            x+w*.68, y+h*.12, x+w*.28, y+h*.50, x+w*.68, y+h*.88
        ]


class BellIcon(Widget):
    def __init__(self, color_hex="#333333", dot_hex="#FF3B30", **kwargs):
        super().__init__(**kwargs)
        with self.canvas:
            Color(*hexc(color_hex))
            self._bell = Line(width=dp(1.6), joint="round", cap="round")
            self._clapper = Ellipse()
            Color(*hexc(dot_hex))
            self._dot = Ellipse()
        self.bind(pos=self._redraw, size=self._redraw)
        self._redraw()

    def _redraw(self, *args):
        x, y = self.pos
        w, h = self.size
        cx = x+w*.48
        top = y+h*.90
        pts = [x+w*.22, y+h*.32]
        for i in range(13):
            t = i/12
            theta = math.pi*(1-t)
            pts += [cx+w*.30*math.cos(theta),
                    top-h*.10-h*.48*(1-math.sin(theta))]
        pts += [x+w*.78,y+h*.32,x+w*.86,y+h*.28,
                x+w*.14,y+h*.28,x+w*.22,y+h*.32]
        self._bell.points = pts
        r = w*.07
        self._clapper.pos = (cx-r, y+h*.14)
        self._clapper.size = (2*r, 2*r)
        r = w*.11
        self._dot.pos = (x+w*.72,y+h*.74)
        self._dot.size = (2*r,2*r)


class TrashBinIcon(Widget):
    def __init__(self, color_hex="#1E88E5", **kwargs):
        super().__init__(**kwargs)
        with self.canvas:
            Color(*hexc(color_hex))
            self._lid = Line(width=dp(1.6), cap="round")
            self._handle = Line(width=dp(1.6), cap="round")
            self._body = RoundedRectangle(radius=[dp(2)])
            Color(1,1,1,1)
            self._ridge1 = Line(width=dp(1.1), cap="round")
            self._ridge2 = Line(width=dp(1.1), cap="round")
        self.bind(pos=self._redraw, size=self._redraw)
        self._redraw()

    def _redraw(self,*args):
        x,y=self.pos; w,h=self.size; cx=x+w/2
        self._lid.points=[x+w*.12,y+h*.78,x+w*.88,y+h*.78]
        self._handle.points=[x+w*.38,y+h*.86,x+w*.38,y+h*.94,
                             x+w*.62,y+h*.94,x+w*.62,y+h*.86]
        bw,bh=w*.62,h*.62
        bx,by=cx-bw/2,y+h*.10
        self._body.pos=(bx,by); self._body.size=(bw,bh)
        self._ridge1.points=[cx-bw*.15,by+bh*.15,cx-bw*.15,by+bh*.85]
        self._ridge2.points=[cx+bw*.15,by+bh*.15,cx+bw*.15,by+bh*.85]


class TruckIcon(Widget):
    def __init__(self,color_hex="#0277BD",**kwargs):
        super().__init__(**kwargs)
        with self.canvas:
            Color(*hexc(color_hex))
            self._cargo=RoundedRectangle(radius=[dp(1.5)])
            self._cab=RoundedRectangle(radius=[dp(1.5)])
            self._window=Line(width=dp(1.1))
            self._wheel1=Line(width=dp(1.4))
            self._wheel2=Line(width=dp(1.4))
        self.bind(pos=self._redraw,size=self._redraw); self._redraw()

    def _redraw(self,*args):
        x,y=self.pos; w,h=self.size; by=y+h*.30
        cw,ch=w*.56,h*.42
        self._cargo.pos=(x+w*.06,by); self._cargo.size=(cw,ch)
        cabw,cabh=w*.30,h*.32; cx=x+w*.06+cw-dp(1)
        self._cab.pos=(cx,by); self._cab.size=(cabw,cabh)
        p=cabw*.22
        self._window.rectangle=(cx+p,by+cabh*.35,cabw-2*p,cabh*.45)
        r=h*.11; wy=by-r*.6
        self._wheel1.circle=(x+w*.26,wy,r)
        self._wheel2.circle=(cx+cabw*.55,wy,r)


class NavHomeIcon(Widget):
    def __init__(self,color_hex=NAV_ACTIVE,**kwargs):
        super().__init__(**kwargs)
        with self.canvas:
            Color(*hexc(color_hex))
            self._roof=Line(width=dp(1.3),joint="round",cap="round")
            self._body=Line(width=dp(1.3))
        self.bind(pos=self._redraw,size=self._redraw); self._redraw()
    def set_color(self,c): self.canvas.children[0].rgba=(*hexc(c)[:3],1)
    def _redraw(self,*args):
        x,y=self.pos; w,h=self.size; cx=x+w/2
        self._roof.points=[x+w*.08,y+h*.48,cx,y+h*.90,x+w*.92,y+h*.48]
        self._body.rectangle=(x+w*.22,y+h*.10,w*.56,h*.42)


class NavPinIcon(Widget):
    def __init__(self,color_hex=NAV_INACTIVE,**kwargs):
        super().__init__(**kwargs)
        with self.canvas:
            Color(*hexc(color_hex))
            self._outline=Line(width=dp(1.3),joint="round",cap="round")
            self._hole=Line(width=dp(1.1))
        self.bind(pos=self._redraw,size=self._redraw); self._redraw()
    def set_color(self,c): self.canvas.children[0].rgba=(*hexc(c)[:3],1)
    def _redraw(self,*args):
        x,y=self.pos; w,h=self.size; cx=x+w/2; top=y+h*.92
        r=w*.34; cy=top-r; pts=[]
        for i in range(17):
            th=math.pi*i/16
            pts += [cx-r*math.cos(th),cy+r*math.sin(th)]
        pts += [x+w*.5-r,cy,cx,y+h*.06,cx+r,cy]
        self._outline.points=pts
        self._hole.circle=(cx,cy,r*.38)


class NavClockIcon(Widget):
    def __init__(self,color_hex=NAV_INACTIVE,**kwargs):
        super().__init__(**kwargs)
        with self.canvas:
            Color(*hexc(color_hex))
            self._face=Line(width=dp(1.3)); self._hands=Line(width=dp(1.1),cap="round")
        self.bind(pos=self._redraw,size=self._redraw); self._redraw()
    def set_color(self,c): self.canvas.children[0].rgba=(*hexc(c)[:3],1)
    def _redraw(self,*args):
        x,y=self.pos; w,h=self.size; cx,cy=x+w/2,y+h/2; r=min(w,h)*.42
        self._face.circle=(cx,cy,r)
        self._hands.points=[cx,cy,cx,cy+r*.55,cx,cy,cx+r*.45,cy]


class NavPersonIcon(Widget):
    def __init__(self,color_hex=NAV_INACTIVE,**kwargs):
        super().__init__(**kwargs)
        with self.canvas:
            Color(*hexc(color_hex))
            self._head=Ellipse(); self._body=Ellipse()
        self.bind(pos=self._redraw,size=self._redraw); self._redraw()
    def set_color(self,c): self.canvas.children[0].rgba=(*hexc(c)[:3],1)
    def _redraw(self,*args):
        x,y=self.pos; w,h=self.size; cx=x+w/2; d=h*.40
        self._head.size=(d,d); self._head.pos=(cx-d/2,y+h*.48)
        bw,bh=w*.78,h*.42
        self._body.size=(bw,bh); self._body.pos=(cx-bw/2,y+h*.02)


class ClickableLabel(ButtonBehavior,Label):
    pass


class StatCard(BoxLayout):
    def __init__(self,title,value,bg_hex,icon_kind,icon_color,**kwargs):
        super().__init__(orientation="vertical",padding=(dp(14),dp(12)),spacing=dp(6),**kwargs)
        with self.canvas.before:
            Color(*hexc(bg_hex)); self._bg_rect=RoundedRectangle(radius=[dp(14)])
        self.bind(pos=self._redraw,size=self._redraw)
        row=BoxLayout(orientation="horizontal",spacing=dp(6),size_hint_y=None,height=dp(20))
        anchor=AnchorLayout(size_hint_x=None,width=dp(20))
        icon=TrashBinIcon(color_hex=icon_color) if icon_kind=="bin" else TruckIcon(color_hex=icon_color)
        icon.size_hint=(None,None); icon.size=(dp(18),dp(18)); anchor.add_widget(icon); row.add_widget(anchor)
        lbl=Label(text=title,font_size=sp(11),color=hexc("#333333"),halign="left",valign="middle")
        lbl.bind(size=lambda i,v:setattr(i,"text_size",v)); row.add_widget(lbl); self.add_widget(row)
        val=Label(text=value,font_size=sp(16),bold=True,color=hexc("#000000"),halign="left",valign="middle",size_hint_y=None,height=dp(24))
        val.bind(size=lambda i,v:setattr(i,"text_size",v)); self.add_widget(val)
    def _redraw(self,*args): self._bg_rect.pos=self.pos; self._bg_rect.size=self.size


class RouteRow(BoxLayout):
    def __init__(self,title,address,status,status_color,**kwargs):
        super().__init__(orientation="horizontal",size_hint_y=None,height=dp(58),padding=(dp(12),dp(8)),**kwargs)
        with self.canvas.before:
            Color(*hexc(ROUTE_BG)); self._bg_rect=RoundedRectangle(radius=[dp(8)])
        self.bind(pos=self._redraw,size=self._redraw)
        left=BoxLayout(orientation="vertical")
        a=Label(text=title,font_size=sp(12),bold=True,color=(0,0,0,1),halign="left",valign="middle")
        a.bind(size=lambda i,v:setattr(i,"text_size",v))
        b=Label(text=address,font_size=sp(10),color=hexc(TEXT_GRAY),halign="left",valign="middle")
        b.bind(size=lambda i,v:setattr(i,"text_size",v))
        left.add_widget(a); left.add_widget(b); self.add_widget(left)
        s=Label(text=status,font_size=sp(11),bold=True,color=hexc(status_color),size_hint_x=None,width=dp(80),halign="right",valign="middle")
        s.bind(size=lambda i,v:setattr(i,"text_size",v)); self.add_widget(s)
    def _redraw(self,*args): self._bg_rect.pos=self.pos; self._bg_rect.size=self.size


class NavButton(ButtonBehavior,AnchorLayout):
    def __init__(self,icon_widget,on_tap,icon_size=dp(16),**kwargs):
        super().__init__(**kwargs); self.icon_widget=icon_widget
        icon_widget.size_hint=(None,None); icon_widget.size=(icon_size,icon_size)
        self.add_widget(icon_widget); self.bind(on_release=lambda inst:on_tap())


class StaffDashboardScreen(Screen):
    def __init__(self,**kwargs):
        super().__init__(**kwargs)

        root=BoxLayout(orientation="vertical"); self.add_widget(root)
        with root.canvas.before:
            Color(1,1,1,1); self._bg_rect=Rectangle()
        root.bind(pos=self._redraw_bg,size=self._redraw_bg)

        self.staff_name=""
        self.staff_id=""
        self.staff_email=""

        scroll=ScrollView(size_hint=(1,1),do_scroll_x=False)
        content=BoxLayout(orientation="vertical",size_hint_y=None,spacing=dp(4),padding=(0,dp(10),0,dp(20)))
        content.bind(minimum_height=content.setter("height")); scroll.add_widget(content); root.add_widget(scroll)

        header=BoxLayout(orientation="horizontal",size_hint_y=None,height=dp(46),padding=(dp(25),0),spacing=dp(10))
        back_anchor=AnchorLayout(size_hint_x=None,width=dp(16),anchor_x="left",anchor_y="center")
        back=BackArrowIcon(color_hex="#000000",size_hint=(None,None),size=(dp(16),dp(16)))
        back.bind(on_release=lambda inst:self._go_back()); back_anchor.add_widget(back); header.add_widget(back_anchor)

        self.title_lbl=Label(text="Good Morning",font_size=sp(18),bold=True,color=(0,0,0,1),halign="left",valign="middle")
        self.title_lbl.bind(size=lambda i,v:setattr(i,"text_size",v)); header.add_widget(self.title_lbl)

        bell=AnchorLayout(size_hint_x=None,width=dp(24)); bell.add_widget(BellIcon(size_hint=(None,None),size=(dp(22),dp(22))))
        header.add_widget(bell); content.add_widget(header)

        self.staff_info_lbl=Label(text="Staff Dashboard",font_size=sp(11),color=hexc(TEXT_GRAY),size_hint_y=None,height=dp(26),halign="left",valign="middle")
        self.staff_info_lbl.bind(size=lambda i,v:setattr(i,"text_size",v))
        sr=BoxLayout(size_hint_y=None,height=dp(26),padding=(dp(25),0)); sr.add_widget(self.staff_info_lbl); content.add_widget(sr)
        content.add_widget(Widget(size_hint_y=None,height=dp(10)))

        gw=BoxLayout(size_hint_y=None,height=dp(210),padding=(dp(20),0)); grid=GridLayout(cols=2,spacing=dp(10))
        self.stat_cards=[]
        for item in CARD_DATA:
            c=StatCard(*item); self.stat_cards.append(c); grid.add_widget(c)
        gw.add_widget(grid); content.add_widget(gw); content.add_widget(Widget(size_hint_y=None,height=dp(14)))

        rh=BoxLayout(orientation="horizontal",size_hint_y=None,height=dp(30),padding=(dp(25),0))
        rt=Label(text="Today's Route",font_size=sp(14),bold=True,color=(0,0,0,1),halign="left",valign="middle")
        rt.bind(size=lambda i,v:setattr(i,"text_size",v)); rh.add_widget(rt)
        va=ClickableLabel(text="View All",font_size=sp(11),color=hexc("#1E88E5"),size_hint_x=None,width=dp(60),halign="right",valign="middle")
        va.bind(size=lambda i,v:setattr(i,"text_size",v)); va.bind(on_release=lambda i:self._go_route()); rh.add_widget(va); content.add_widget(rh)

        self.route_wrap=BoxLayout(orientation="vertical",size_hint_y=None,spacing=dp(8),padding=(dp(20),dp(4),dp(20),0))
        self.route_wrap.bind(minimum_height=self.route_wrap.setter("height"))
        self._build_route_rows(ROUTE_DATA); content.add_widget(self.route_wrap)

        nav=BoxLayout(orientation="horizontal",size_hint_y=None,height=dp(52))
        with nav.canvas.before:
            Color(*hexc(GREEN)); self._nav_bg=Rectangle()
        nav.bind(pos=self._redraw_nav_bg,size=self._redraw_nav_bg)
        self._home_icon=NavHomeIcon(); self._pin_icon=NavPinIcon(); self._clock_icon=NavClockIcon(); self._person_icon=NavPersonIcon()
        nav.add_widget(NavButton(self._home_icon,self._go_dashboard,icon_size=dp(16)))
        nav.add_widget(NavButton(self._pin_icon,self._go_route,icon_size=dp(16)))
        nav.add_widget(NavButton(self._clock_icon,self._go_history,icon_size=dp(16)))
        nav.add_widget(NavButton(self._person_icon,self._go_profile,icon_size=dp(16)))
        root.add_widget(nav)

    # Firebase profile loading
    def on_enter(self,*args):
        self._load_staff_profile()

    def _load_staff_profile(self):
        if get_current_user is None or get_data is None:
            print("(staff_dashboard) Firebase modules not available.")
            return
        try:
            user=get_current_user()
            if not user:
                print("(staff_dashboard) No logged-in Firebase user.")
                return

            uid=user.get("localId")
            if not uid:
                print("(staff_dashboard) Firebase UID not found.")
                return

            success,data=get_data(f"staff/{uid}")
            if not success:
                print("(staff_dashboard) Could not load staff profile:",data)
                return
            if not data:
                print("(staff_dashboard) No staff profile found for UID:",uid)
                return

            self.staff_name=data.get("full_name","Staff")
            self.staff_email=data.get("email","")
            self.staff_id=data.get("staff_id","")

            self.title_lbl.text=f"Good Morning, {self.staff_name}"

            if self.staff_id and self.staff_email:
                self.staff_info_lbl.text=f"Staff ID: {self.staff_id}  •  {self.staff_email}"
            elif self.staff_id:
                self.staff_info_lbl.text=f"Staff ID: {self.staff_id}"
            elif self.staff_email:
                self.staff_info_lbl.text=self.staff_email
            else:
                self.staff_info_lbl.text="Staff Dashboard"

            print("(staff_dashboard) Staff profile loaded:",self.staff_name,self.staff_id,self.staff_email)
        except Exception as e:
            print("(staff_dashboard) Firebase error:",e)

    def _build_route_rows(self,data):
        self.route_wrap.clear_widgets()
        for title,addr,status,color in data:
            self.route_wrap.add_widget(RouteRow(title,addr,status,color))

    def _redraw_bg(self,*args):
        self._bg_rect.pos=args[0].pos; self._bg_rect.size=args[0].size

    def _redraw_nav_bg(self,instance,*args):
        self._nav_bg.pos=instance.pos; self._nav_bg.size=instance.size

    def _go_back(self): self._navigate(BACK_SCREEN)
    def _go_dashboard(self): pass
    def _go_route(self): self._navigate(ROUTE_SCREEN)
    def _go_history(self): self._navigate(HISTORY_SCREEN)
    def _go_profile(self): self._navigate(PROFILE_SCREEN)

    def _navigate(self,target):
        if self.manager and target in self.manager.screen_names:
            self.manager.current=target
        else:
            print(f"(staff_dashboard) Would navigate to '{target}', but it isn't registered in main.py's ScreenManager yet.")


if __name__=="__main__":
    from kivy.app import App
    from kivy.uix.screenmanager import ScreenManager
    from kivy.core.window import Window

    class PlaceholderScreen(Screen):
        def __init__(self,label_text,**kwargs):
            super().__init__(**kwargs)
            self.add_widget(Label(text=label_text,color=(0,0,0,1)))

    class StaffDashboardPreviewApp(App):
        def build(self):
            Window.size=(360,640)
            Window.clearcolor=(1,1,1,1)
            sm=ScreenManager()
            sm.add_widget(StaffDashboardScreen(name="staff_dashboard"))
            sm.add_widget(PlaceholderScreen("Staff Login\n(placeholder)",name="staff_login"))
            sm.current="staff_dashboard"
            return sm

    StaffDashboardPreviewApp().run()
