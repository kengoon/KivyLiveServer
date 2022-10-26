import contextlib
from multiprocessing import Event, Process
from subprocess import STDOUT, DEVNULL, call as shell_call
import socket
from datetime import datetime
from os.path import join, expanduser

from PIL import Image

if hasattr(__import__(__name__), "__compiled__"):
    from os import environ

    environ["KIVY_NO_CONSOLELOG"] = "1"
from threading import Thread

from kivy.animation import Animation
from kivy.app import App
from kivy.clock import mainthread
from kivy.config import Config
from kivy.properties import NumericProperty
from kivy.core.text import Label as CoreLabel
from kivy.uix.behaviors import TouchRippleButtonBehavior
from kivy.lang import Builder
from kivy.utils import get_color_from_hex
from kivy.core.window import Window
from kivy.graphics import Color, Line, BindTexture
from kivy.metrics import dp
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.factory import Factory
from kivy.uix.modalview import ModalView
from kivy.storage.jsonstore import JsonStore
from kivy import platform
from plyer import filechooser
from server import KivyLiveServer
from kivy.uix.dropdown import DropDown
from netifaces import gateways, AF_INET, ifaddresses

from toast import toast

Window.size = Window.width + dp(150), Window.height
Window.minimum_width, Window.minimum_height = Window.size
Window.custom_titlebar = True
Window.clearcolor = get_color_from_hex("#1f1f1f")

Config.set("kivy", "exit_on_escape", 0)
Config.set('input', 'mouse', 'mouse,multitouch_on_demand')
Factory.register("HoverBehavior", module="hover_behavior")

CoreLabel.register(*["Icon", "assets/fonts/icon.ttf"])
CoreLabel.register(*["Ubuntu", "assets/fonts/UbuntuMono-R.ttf"])

Builder.load_string("""
#: import icon tools.icon_def.x_icons
#: import win kivy.core.window.Window
#: import get_color_from_hex kivy.utils.get_color_from_hex
#: import ScrollEffect kivy.effects.scroll.ScrollEffect
<IconButton@HoverBehavior+ButtonBehavior+Label>:
    icon: ""
    text: icon[self.icon] if self.icon else ""
    size_hint: None, None
    size: self.texture_size
    font_name: "Icon"
    padding: dp(5), dp(5)
    pos_hint: {"center_y": .5}
    on_leave: self.color = 1, 1, 1, 1
    
<Input@HoverBehavior+TextInput>:
    background_normal: ""
    background_active: ""
    background_disabled_normal: ""
    background_color: 0, 0, 0, .5
    foreground_color: get_color_from_hex("#00C853")
    disabled_foreground_color: self.foreground_color
    size_hint: None, None
    font_name: "Ubuntu"
    size: dp(200), dp(30)
    on_enter: win.set_system_cursor("ibeam")
    on_leave: win.set_system_cursor("arrow")
    
<Log@Label>:
    text_size: self.width, None
    color: get_color_from_hex("#00C853")
    bold: True
    markup: True
    font_name: "Ubuntu"

<ButtonLabel@ButtonBehavior+Label>:
    size_hint: None, None
    size: self.texture_size
    bold: True
    padding: dp(50), dp(10)
    bg_color: 0, 0, 0, .5
    line_color: 0, 0, 0, 0
    radius: [dp(0)]
    canvas.before:
        Color:
            rgba: self.bg_color
        RoundedRectangle:
            size: self.size
            pos: self.pos
            radius: self.radius or [dp(0)]
        Color:
            rgba: self.line_color
        Line:
            points: self.x, self.y, self.width, self.y
    
<BlackBox@RecycleView>:
    effect_cls: ScrollEffect
    viewclass: "Log"
    canvas.before:
        Color:
            rgba: 0, 0, 0, .7
        RoundedRectangle:
            size: self.size
            pos: self.pos
            radius: [dp(20)]
    RecycleBoxLayout:
        orientation: "vertical"
        size_hint_y: None
        height: self.minimum_height
        spacing: dp(5)
        default_size_hint: 1, None
        padding: dp(10)
        # magic value for the default height of the message
        default_size: 0, dp(30)
        
<ProtocolBox@BoxLayout>:
    orientation: "vertical"
    spacing: dp(10)
    size_hint: None, None
    size: self.minimum_size
    pos_hint: {"center_x": .5}
    Label:
        text: "IP ADDRESS"
        size_hint: None, None
        size: self.texture_size   
    ButtonLabel:
        id: ip
        text: "0.0.0.0"
        size: dp(200), self.texture_size[1]
        color: get_color_from_hex("#00C853")
        radius: [dp(5), dp(5), 0, 0]
        padding_x: dp(10)
        disabled_outline_color: self.color
        disabled_color: self.color
        on_release: app.open_dropdown(args[0])
    Label:
        text: "PORT"
        size_hint: None, None
        size: self.texture_size   
    Input:
        id: port
        text: "5567"
        input_type: "number"
        input_filter: "int"
    Label:
        text: "SELECT FOLDER"
        size_hint: None, None
        size: self.texture_size
    ButtonLabel:
        id: folder_name
        text: app.resolve_cache_path or "open filechooser"
        padding_x: dp(10)
        size: dp(200), self.texture_size[1]
        color: get_color_from_hex("#00C853")
        radius: [dp(5), dp(5), 0, 0]
        disabled_outline_color: self.color
        disabled_color: self.color
        text_size: self.width, None
        shorten: True
        bold: False
        shorten_from: "left"
        on_release: app.choose_write_location(self)
        
    
<TitleBar@BoxLayout>:
    size_hint_y: None
    height: self.minimum_height
    padding: dp(2)
    spacing: dp(15)
    IconButton:
        id: icon
        icon: "computer-tower-f"
        color: get_color_from_hex("#C51162")
        font_size: "20sp"
    Label:
        text: "Fleet"
        size_hint_y: None
        height: self.texture_size[1]
        text_size: self.size
        bold: True
        pos_hint: {"center_y": .5}
    IconButton:
        draggable: False
        icon: "minus-l"
        on_release: win.minimize()
        on_enter: self.color = get_color_from_hex("#00C853")
    IconButton:
        icon: "square-l"
        draggable: False
        maximize: True
        on_enter: self.color = get_color_from_hex("#00C853")
        on_release:
            self.icon = "square-l" if self.icon == "cards-l" else "cards-l"
            win.maximize() if self.maximize else win.restore()
            self.maximize = not self.maximize
    IconButton:
        draggable: False
        icon: "x-l"
        on_enter: self.color = "red"
        on_release:
            app.stop_server(stop_app=True)
<Dialog@BoxLayout>:
    orientation: "vertical"
    size_hint: None, None
    size: self.minimum_size
    spacing: dp(40)
    Label:
        text: "Minimize To System Tray?"
    LineButton:
        text: "YES MINIMIZE"
        size_hint: None, None
        size: self.texture_size
        color: app.GREEN
        ripple_color: app.GREEN
        padding: dp(50), dp(20)
        pos_hint: {"center_x": .5}
        on_release: app.minimize_app_to_tray()
    LineButton:
        text: "NO CLOSE APPLICATION"
        size_hint: None, None
        color: app.RED
        ripple_color: app.RED
        size: self.texture_size
        padding: dp(50), dp(20)
        pos_hint: {"center_x": .5}
        on_release: app.stop_server(stop_app=True, dialog_open=True)
""", filename="main.kv", rulesonly=True)
title_bar = Factory.TitleBar()
Window.set_custom_titlebar(title_bar)


class LineButton(TouchRippleButtonBehavior, Label):
    ripple_duration_in = NumericProperty(1)

    ripple_duration_out = NumericProperty(1)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.radius = dp(10)
        self.resolution = 100
        self.canvas_length = 0
        self.bind(size=self.draw_rectangle, pos=self.draw_rectangle)

    def on_disabled(self, instance, value):
        if value:
            self.ripple_fade()

    def draw_rectangle(self, *_):
        for child in self.canvas.children[self.canvas_length - 3: self.canvas_length]:
            if isinstance(child, BindTexture):
                continue
            self.canvas.remove(child)
        with self.canvas:
            Color(*self.color)
            Line(width=1.1, rounded_rectangle=[self.x, self.y, self.width, self.height, self.radius, self.resolution])
        self.canvas_length = len(self.canvas.children)


class FleetApp(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.quit_app = False
        self.raise_window = False
        self.p: Process = None
        self.raise_flag = None
        self.quit_flag = None
        self.title = "Fleet"
        self.server_flag = Event()  # checking access granted to firewall while quitting to remove tray icon
        self.server_started = False
        self.kill_server_thread = False
        self.RED = get_color_from_hex("#C51162")
        self.GREEN = get_color_from_hex("#00C853")
        self.PURE_RED = [1, 0, 0, 1]
        self.cache = JsonStore(join(self.user_data_dir, "cache.json"))
        try:
            self.resolve_cache_path = self.cache.get("folder")["path"]
        except KeyError:
            self.resolve_cache_path = None
        self.thread = None
        self.dialog = ModalView(
            size_hint=(None, None),
            size=(dp(300), dp(256)),
            background="",
            background_color=[0, 0, 0, 0],
            overlay_color=[0, 0, 0, .8]
        )
        self.dialog.add_widget(Factory.Dialog())
        self.anim = Animation(opacity=.2) + Animation(opacity=1)
        self.anim.repeat = True
        self.start_server_button = LineButton(
            text="START SERVER",
            bold=True,
            color=self.GREEN,
            ripple_color=self.GREEN,
            size_hint=(None, None),
            pos_hint={"center_x": .5},
            padding=(dp(50), dp(20)),
            on_release=lambda _: self.start_server()
        )
        self.start_server_button.bind(texture_size=self.start_server_button.setter("size"))

        self.stop_server_button = LineButton(
            text="STOP SERVER",
            bold=True,
            color=self.RED,
            ripple_color=self.RED,
            size_hint=(None, None),
            pos_hint={"center_x": .5},
            padding=(dp(50), dp(20)),
            disabled=True,
            on_release=lambda _: self.stop_server()
        )
        self.stop_server_button.bind(texture_size=self.stop_server_button.setter("size"))

        box = BoxLayout(
            size_hint_y=None,
            orientation="vertical",
            pos_hint={"center": [.5, .5]},
            padding=dp(20),
            spacing=dp(40)
        )

        box.bind(minimum_height=box.setter("height"))
        self.protocol_box = Factory.ProtocolBox()
        box.add_widget(self.protocol_box)
        box.add_widget(self.start_server_button)
        box.add_widget(self.stop_server_button)

        relative = RelativeLayout(size_hint_x=.7)
        relative.add_widget(box)
        self.black_box = Factory.BlackBox()
        big_box = BoxLayout(padding=dp(10), spacing=dp(10))
        big_box.add_widget(relative)
        big_box.add_widget(self.black_box)

        self.root = BoxLayout(orientation="vertical")
        self.root.add_widget(title_bar)
        self.root.add_widget(big_box)
        self.dropdown = DropDown(
            on_select=lambda _, text: setattr(self.protocol_box.ids.ip, "text", text),
            on_dismiss=lambda dropdown: dropdown.clear_widgets(),
        )

    def open_dropdown(self, button):
        try:
            item = Factory.ButtonLabel(
                text="0.0.0.0",
                on_release=lambda btn: self.dropdown.select(btn.text),
                bg_color=[0, 0, 0, 1],
                color=get_color_from_hex("#00C853"),
            )
            item.line_color = [1, 1, 1, 1]
            self.dropdown.add_widget(item)
            gateway = gateways()[AF_INET]
            for _, interface, _ in gateway:
                ip = ifaddresses(interface)[AF_INET][0]["addr"]
                item = Factory.ButtonLabel(
                    text=ip,
                    on_release=lambda btn: self.dropdown.select(btn.text),
                    bg_color=[0, 0, 0, 1],
                    color=get_color_from_hex("#00C853")
                )
                item.line_color = [1, 1, 1, 1] if interface not in gateway[-1] else [0, 0, 0, 0]
                self.dropdown.add_widget(item)
            self.dropdown.open(button)
        except KeyError:
            toast(
                "YOU ARE NOT CONNECTED ON ANY NETWORK YET: USING 0.0.0.0 AS YOUR IP ADDRESS",
                text_color=self.GREEN, bold=True
            )
            self.protocol_box.ids.ip.text = "0.0.0.0"

    def start_server(self):
        if len(self.protocol_box.ids.port.text) < 4:
            return toast(
                "YOUR PORT ADDRESS MUST BE 1000 AND ABOVE",
                bold=True, text_color=self.PURE_RED)
        if self.protocol_box.ids.folder_name.text == "open filechooser":
            return toast(
                "SELECT A FOLDER BEFORE PROCEEDING",
                bold=True, text_color=self.PURE_RED)
        ip_address = self.protocol_box.ids.ip.text
        port = int(self.protocol_box.ids.port.text)
        self.log_black_box(f"[color=#ffffff]requesting to open port {port} over firewall.....[/color]")
        if platform == "linux" and not shell_call(["which", "ufw"], stderr=STDOUT, stdout=DEVNULL) and \
                shell_call(["pkexec", "ufw", "allow", f"{port}/tcp"], stderr=STDOUT, stdout=DEVNULL):
            self.log_black_box("[color=#ff0000]request denied.....[/color]")
            self.log_black_box("[color=#ffff00][size=18]Is `ufw` installed?[/size][/color]")
            return toast(f"FAILED TO OPEN PORT {port} OVER FIREWALL", bold=True, text_color=self.PURE_RED)
        self.log_black_box("request accepted....")
        self.start_server_button.disabled = True
        self.protocol_box.disabled = True
        self.stop_server_button.disabled = False
        title_bar.ids.icon.color = self.GREEN
        self.anim.start(title_bar.ids.icon)
        folder = self.protocol_box.ids.folder_name.text
        self.thread = Thread(target=KivyLiveServer, args=(self, ip_address, port, join(self.user_data_dir, folder)))
        self.thread.start()
        self.server_started = True
        self.server_flag.clear()

    @mainthread
    def stop_server(self, error: str = None, stop_app: bool = False, dialog_open: bool = False):
        if not self.server_started and stop_app:
            self.stop()
            return True
        elif stop_app and not dialog_open:
            self.dialog.open()
            return
        if error:
            toast(error.upper(), bold=True, text_color=self.PURE_RED)
        ip_address = self.protocol_box.ids.ip.text
        port = int(self.protocol_box.ids.port.text)
        self.log_black_box(f"[color=#ffffff]requesting to open port {port} over firewall.....[/color]")
        if platform == "linux" and shell_call(["pkexec", "ufw", "deny", f"{port}/tcp"], stderr=STDOUT, stdout=DEVNULL):
            self.log_black_box("[color=#ff0000]request denied.....[/color]")
            self.log_black_box("[color=#ffff00][size=18]Is `ufw` installed?[/size][/color]")
            toast(f"FAILED TO CLOSE {port} OVER FIREWALL", bold=True, text_color=self.PURE_RED)
            self.server_flag.set()
            return
        self.log_black_box("request accepted.......")
        self.start_server_button.disabled = False
        self.protocol_box.disabled = False
        self.stop_server_button.disabled = True
        title_bar.ids.icon.color = self.RED
        self.anim.stop(title_bar.ids.icon)
        title_bar.ids.icon.opacity = 1
        self.kill_server_thread = True
        with contextlib.suppress(ConnectionRefusedError, AttributeError):
            server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server.connect((ip_address, port))
            server.close()
            self.thread.join()
        self.kill_server_thread = False
        self.log_black_box(f"{datetime.now().strftime('%d/%m/%Y %H:%M:%S')} : server stopped")
        self.server_started = False
        self.server_flag.set()
        if stop_app:
            self.stop()
            return True

    def choose_write_location(self, button):
        filechooser.choose_dir(
            path=self.resolve_cache_path or expanduser("~"),
            title="SELECT A FOLDER FOR THE SERVER TO WRITE TO",
            on_selection=lambda files: self.cache.put("folder", path=files[0] if files else "open filechooser"))
        self.resolve_cache_path = self.cache.get("folder")["path"]
        button.text = self.resolve_cache_path

    @mainthread
    def log_black_box(self, message):
        self.black_box.data.append({"text": message})

    def minimize_app_to_tray(self):
        self.dialog.dismiss()
        Window.hide()

        def create_system_tray(raise_flag, quit_flag):
            from pystray import Icon, Menu, MenuItem
            img = Image.open("assets/images/kivy-icon-64.png")
            menu = Menu(
                MenuItem("Open Fleet", lambda: raise_flag.set()),
                MenuItem("Quit Fleet", lambda: quit_flag.set())
            )
            icon = Icon(icon=img, name="Fleet", title="Fleet", menu=menu)
            icon.run()

        self.quit_app = False
        self.raise_window = False
        self.raise_flag = Event()
        self.quit_flag = Event()
        self.p = Process(target=create_system_tray, args=(self.raise_flag, self.quit_flag))
        self.p.start()

        def check_process_window_raised():
            self.raise_flag.wait()
            if self.quit_app:
                return
            self.raise_window = True
            self.quit_flag.set()
            self.raise_app_window()

        Thread(target=check_process_window_raised).start()

        def check_process_quit_app():
            self.quit_flag.wait()
            if self.raise_window:
                return
            if not self.terminate_app():
                self.quit_flag.clear()
                check_process_quit_app()
            self.quit_app = True
            self.raise_flag.set()

        Thread(target=check_process_quit_app).start()

    def terminate_process(self):
        self.p.terminate()
        self.p.kill()
        self.p.join()

    def terminate_app(self):
        self.stop_server(stop_app=True, dialog_open=True)
        self.server_flag.wait()
        if not self.server_started:
            self.terminate_process()
            return True
        self.server_flag.clear()
        return False

    @mainthread
    def raise_app_window(self):
        self.terminate_process()
        Window.show()

# FleetApp().run()
