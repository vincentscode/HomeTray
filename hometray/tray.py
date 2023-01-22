import wx
import wx.adv
import sched
from _thread import start_new_thread
import time
import sys

if getattr(sys, 'frozen', False):
    from hometray.iconmanager import IconManager
    from hometray.config import Config
    from hometray.settings import Settings
else:
    from iconmanager import IconManager
    from config import Config
    from settings import Settings

class EntityTrayIcon(wx.adv.TaskBarIcon):
    def __init__(self, frame, entity_id, client, icons: IconManager, config: Config, settings: Settings):
        super(EntityTrayIcon, self).__init__()
        self.frame = frame
        self.entity_id = entity_id
        self.client = client
        self.icons = icons
        self.config = config
        self.settings = settings

        self.scheduler = sched.scheduler(time.time, time.sleep)
        def update_task(scheduler): 
            self.update_state()
            self.scheduled_event = self.scheduler.enter(self.config.update_interval, 1, update_task, (scheduler,))
        self.scheduled_event = self.scheduler.enter(self.config.update_interval, 1, update_task, (self.scheduler,))
        start_new_thread(self.scheduler.run, ())

        self.Bind(wx.adv.EVT_TASKBAR_LEFT_DOWN, self.on_left_down)
        self.Bind(wx.adv.EVT_TASKBAR_RIGHT_UP, self.on_right_up)

        self.menu = wx.Menu()
        append_menu_item(self.menu, 'Toggle', self.on_left_down, bold=True)
        self.menu.AppendSeparator()
        append_menu_item(self.menu, 'Configure HomeTray', lambda _: settings.configure())
        append_menu_item(self.menu, 'Close HomeTray', self.on_exit)

        self.update_state()

    def update_state(self):
        entity = self.client.get_entity(entity_id=self.entity_id)
        entity_state = entity.state.state
        entity_icon = entity.state.attributes["icon"] if "icon" in entity.state.attributes else "default"
        entity_name = entity.state.attributes["friendly_name"] if "friendly_name" in entity.state.attributes else self.entity_id
        
        if entity_state == "on":
            if self.config.color_use_rgb_value and "rgb_color" in entity.state.attributes:
                rgb_color = entity.state.attributes["rgb_color"]
            else:
                rgb_color = self.config.color_on
        elif entity_state == "off":
            rgb_color = self.config.color_off
        else:
            rgb_color = self.config.color_unknown

        self.set_icon(entity_icon, entity_state, rgb_color, entity_name)

    def set_icon(self, icon_name, icon_state, icon_color, tooltip):
        icon = self.icons.get_icon(icon_name, icon_state, icon_color)
        self.SetIcon(icon, tooltip)

    def on_left_down(self, _):
        self.update_state()
        domain = self.client.get_domain('homeassistant')
        domain.toggle(entity_id=self.entity_id)
        time.sleep(0.1)
        self.update_state()
    
    def on_right_up(self, _):
        self.PopupMenu(self.menu)

    def cleanup(self):
        if self.scheduled_event:
            try:
                self.scheduler.cancel(self.scheduled_event)
            except:
                pass

        self.RemoveIcon()
        self.frame.Close()
        wx.CallAfter(self.Destroy)

    def on_exit(self, _):
        wx.Exit()

def append_menu_item(menu: wx.Menu, label: str, func, bold: bool = False):
    item = wx.MenuItem(menu, -1, label)
    menu.Bind(wx.EVT_MENU, func, id=item.GetId())
    if bold:
        font: wx.Font = item.GetFont()
        font.SetWeight(wx.FONTWEIGHT_HEAVY)
        item.SetFont(font)
    menu.Append(item)
    return item
