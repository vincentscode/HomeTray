import wx
import wx.adv
import sched
from _thread import start_new_thread
import time
import sys
import homeassistant_api as ha

if getattr(sys, 'frozen', False):
    from hometray.iconmanager import IconManager
    from hometray.config import Config
    from hometray.settings import Settings
else:
    from iconmanager import IconManager
    from config import Config
    from settings import Settings

class EntityTrayIcon(wx.adv.TaskBarIcon):
    def __init__(self, frame, entity_id, client: ha.Client, icons: IconManager, config: Config, settings: Settings):
        super(EntityTrayIcon, self).__init__()
        self.frame = frame
        self.entity_id = entity_id
        self.domain_id = entity_id.split(".")[0]
        self.client = client
        self.icons = icons
        self.config = config
        self.settings = settings

        self.has_color_control = False

        self.scheduler = sched.scheduler(time.time, time.sleep)
        def update_task(scheduler): 
            self.update_state()
            self.scheduled_event = self.scheduler.enter(self.config.update_interval, 1, update_task, (scheduler,))
        self.scheduled_event = self.scheduler.enter(self.config.update_interval, 1, update_task, (self.scheduler,))
        start_new_thread(self.scheduler.run, ())

        self.Bind(wx.adv.EVT_TASKBAR_LEFT_DOWN, self.on_left_down)
        self.Bind(wx.adv.EVT_TASKBAR_RIGHT_UP, self.on_right_up)

        self.domain: ha.Domain = self.client.get_domain('homeassistant')
        self.specific_domain: ha.Domain = self.client.get_domain(self.domain_id)
        
        # print("Domain Services")
        # for service_id in self.specific_domain.services:
        #     service: ha.Service = self.specific_domain.services[service_id]
        #     service_name = service.name
        #     service_description = service.description
        #     service_fields = service.fields
        #     print(service_name, list(service_fields.keys()))

        self.update_state()

    def update_state(self):
        entity = self.client.get_entity(entity_id=self.entity_id)
        entity_state = entity.state.state
        entity_icon = entity.state.attributes["icon"] if "icon" in entity.state.attributes else "default"
        entity_name = entity.state.attributes["friendly_name"] if "friendly_name" in entity.state.attributes else self.entity_id
        
        if entity_state == "on":
            if self.config.color_use_rgb_value and "rgb_color" in entity.state.attributes:
                self.rgb_color = entity.state.attributes["rgb_color"]
                self.has_color_control = True
                
            else:
                self.rgb_color = self.config.color_on
        elif entity_state == "off":
            self.rgb_color = self.config.color_off
        else:
            self.rgb_color = self.config.color_unknown

        self.set_icon(entity_icon, entity_state, self.rgb_color, entity_name)

    def pick_color(self):
        data = wx.ColourData()
        data.SetChooseFull(True)
        color = wx.Colour()
        color.Set(*self.config.color_on)
        data.SetColour(color)
        dialog = wx.ColourDialog(self.frame, data)

        def set_color(color):
            rgb = [color.Red(), color.Green(), color.Blue()]
            self.specific_domain.turn_on(entity_id=self.entity_id, rgb_color=rgb)
            self.rgb_color = rgb

        dialog.Bind(wx.EVT_COLOUR_CHANGED, lambda e: set_color(e.Colour))
        dialog.CenterOnScreen()
        dialog.ShowModal()
        dialog.Destroy()

    def set_icon(self, icon_name, icon_state, icon_color, tooltip):
        icon = self.icons.get_icon(icon_name, icon_state, icon_color)
        self.SetIcon(icon, tooltip)

    def on_left_down(self, _):
        self.update_state()
        self.domain.toggle(entity_id=self.entity_id)
        time.sleep(0.1)
        self.update_state()
    
    def on_right_up(self, _):
        menu = wx.Menu()
        add_menu_item(menu, 'Toggle', self.on_left_down, bold=True)
        if self.has_color_control:
            add_menu_item(menu, 'Change Color', lambda _: self.pick_color())
        menu.AppendSeparator()
        add_menu_item(menu, 'Configure HomeTray', lambda _: self.settings.configure())
        add_menu_item(menu, 'Close HomeTray', self.on_exit)
        add_menu_item(menu, 'Change Color', lambda _: self.pick_color())
        self.PopupMenu(menu)
        menu.Destroy()

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

def add_menu_item(menu: wx.Menu, label: str, func, bold: bool = False, position: int = -1):
    item = wx.MenuItem(menu, -1, label)
    menu.Bind(wx.EVT_MENU, func, id=item.GetId())
    if bold:
        font: wx.Font = item.GetFont()
        font.SetWeight(wx.FONTWEIGHT_HEAVY)
        item.SetFont(font)
    if position != -1:
        menu.Insert(position, item)
    else:
        menu.Append(item)
    return item
