from kivy.config import Config

# ---------------------------------------------------------
# PHONE SIZE
# ---------------------------------------------------------

Config.set("graphics", "width", "360")
Config.set("graphics", "height", "640")
Config.set("graphics", "resizable", "0")


from kivy.app import App
from kivy.core.window import Window
from kivy.uix.screenmanager import ScreenManager, NoTransition


# ---------------------------------------------------------
# IMPORT SCREENS
# ---------------------------------------------------------

from splash_screen_kivy import SplashScreen
from role_selection_kivy import RoleSelectionScreen

# ADMIN
from admin_login_kivy import AdminLoginScreen
from forget_password_kivy import ForgetPasswordScreen
from reset_password_kivy import ResetPasswordScreen
from admin_dashboard_kivy import AdminDashboardScreen
from admin_map_kivy import MapScreenAdmin
from admin_panel_kivy import AdminPanelScreen
from admin_profile_kivy import AdminProfileScreen

# ADMIN EDIT PROFILE
from admin_edit_profile_kivy import AdminEditProfileScreen

# ADMIN NOTIFICATION SETTINGS
from admin_notification_settings_kivy import AdminNotificationSettingsScreen

# ADMIN FEATURES
from add_bin_kivy import AddBinScreen
from assign_worker_kivy import AssignWorkerScreen
from admin_reports_kivy import AdminReportsScreen
from admin_generate_pdf_kivy import GeneratePDFScreen

# STAFF
from staff_login_kivy import StaffLoginScreen
from staff_registration_kivy import StaffRegistrationScreen
from staff_forget_password_kivy import StaffForgetPasswordScreen
from staff_reset_password_kivy import StaffResetPasswordScreen
from staff_dashboard_kivy import StaffDashboardScreen
from staff_route_kivy import StaffRouteScreen
from staff_task_history_kivy import StaffTaskHistoryScreen
from staff_profile_kivy import StaffProfileScreen
from edit_profile_kivy import EditProfileScreen

# STAFF NOTIFICATION SETTINGS
from staff_notification_settings_kivy import StaffNotificationSettingsScreen


# ---------------------------------------------------------
# APP
# ---------------------------------------------------------

class MyIoTApp(App):

    def build(self):

        Window.size = (360, 640)

        sm = ScreenManager(
            transition=NoTransition()
        )

        # -------------------------------------------------
        # SPLASH / ROLE
        # -------------------------------------------------

        sm.add_widget(
            SplashScreen(name="splash")
        )

        sm.add_widget(
            RoleSelectionScreen(name="role_selection")
        )

        # -------------------------------------------------
        # ADMIN AUTH
        # -------------------------------------------------

        sm.add_widget(
            AdminLoginScreen(name="admin_login")
        )

        sm.add_widget(
            ForgetPasswordScreen(name="forget_password")
        )

        sm.add_widget(
            ResetPasswordScreen(name="reset_password")
        )

        # -------------------------------------------------
        # ADMIN MAIN
        # -------------------------------------------------

        sm.add_widget(
            AdminDashboardScreen(name="admin_dashboard")
        )

        sm.add_widget(
            MapScreenAdmin(name="admin_map")
        )

        sm.add_widget(
            AdminPanelScreen(name="admin_panel")
        )

        sm.add_widget(
            AdminProfileScreen(name="admin_profile")
        )

        # -------------------------------------------------
        # ADMIN EDIT PROFILE
        # -------------------------------------------------

        sm.add_widget(
            AdminEditProfileScreen(name="admin_edit_profile")
        )

        # -------------------------------------------------
        # ADMIN NOTIFICATION SETTINGS
        # -------------------------------------------------

        sm.add_widget(
            AdminNotificationSettingsScreen(
                name="admin_notification_settings"
            )
        )

        # -------------------------------------------------
        # ADMIN FEATURES
        # -------------------------------------------------

        sm.add_widget(
            AddBinScreen(name="add_bin")
        )

        sm.add_widget(
            AssignWorkerScreen(name="assign_worker")
        )

        sm.add_widget(
            AdminReportsScreen(name="admin_reports")
        )

        sm.add_widget(
            GeneratePDFScreen(name="admin_generate_pdf")
        )

        # -------------------------------------------------
        # STAFF AUTH
        # -------------------------------------------------

        sm.add_widget(
            StaffLoginScreen(name="staff_login")
        )

        sm.add_widget(
            StaffRegistrationScreen(name="staff_registration")
        )

        sm.add_widget(
            StaffForgetPasswordScreen(name="staff_forget_password")
        )

        sm.add_widget(
            StaffResetPasswordScreen(name="staff_reset_password")
        )

        # -------------------------------------------------
        # STAFF MAIN
        # -------------------------------------------------

        sm.add_widget(
            StaffDashboardScreen(name="staff_dashboard")
        )

        sm.add_widget(
            StaffRouteScreen(name="staff_route")
        )

        sm.add_widget(
            StaffTaskHistoryScreen(name="staff_task_history")
        )

        sm.add_widget(
            StaffProfileScreen(name="staff_profile")
        )

        sm.add_widget(
            EditProfileScreen(name="edit_profile")
        )

        # -------------------------------------------------
        # STAFF NOTIFICATION SETTINGS
        # -------------------------------------------------

        sm.add_widget(
            StaffNotificationSettingsScreen(
                name="staff_notification_settings"
            )
        )

        # -------------------------------------------------
        # START
        # -------------------------------------------------

        sm.current = "splash"

        return sm


# ---------------------------------------------------------
# RUN
# ---------------------------------------------------------

if __name__ == "__main__":
    MyIoTApp().run()
