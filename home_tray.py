import sched
import time
import configparser
import wx
import wx.adv
from _thread import start_new_thread
from homeassistant_api import Client

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

icon_base = resource_path('icons/')
icons = {
    "default": {
        "on": "on.png",
        "off": "off.png"
    },
    "phu:light-strip": {
        "on": "phu-light-strip-on.png",
        "off": "phu-light-strip-off.png"
    },
    "mdi:ceiling-light": {
        "on": "mdi-ceiling-light-on.png",
        "off": "mdi-ceiling-light-off.png"
    },
    "mdi:desk-lamp": {
        "on": "mdi-desk-lamp-on.png",
        "off": "mdi-desk-lamp-off.png"
    },
    "mdi:lightbulb-night": {
        "on": "mdi-lightbulb-night-on.png",
        "off": "mdi-lightbulb-night-off.png"
    },

}

def get_icon_path(icon_name, state):
    default_state = "off"
    default_icon = "default"
    if icon_name in icons.keys():
        if state in icons[icon_name].keys():
            return icon_base + icons[icon_name][state]

        print(f"No icon of type \"{icon_name}\" for state \"{state}\"")
        return icon_base + icons[icon_name][default_state]
    
    print(f"No icon of type \"{icon_name}\"")
    if state in icons[default_icon].keys():
        return icon_base + icons[default_icon][state]

    return icon_base + icons[default_icon][default_state]


def create_menu_item(menu, label, func):
    item = wx.MenuItem(menu, -1, label)
    menu.Bind(wx.EVT_MENU, func, id=item.GetId())
    menu.Append(item)
    return item

class TaskBarIcon(wx.adv.TaskBarIcon):
    def __init__(self, frame, entity_id, client):
        super(TaskBarIcon, self).__init__()
        self.frame = frame
        self.entity_id = entity_id
        self.client = client

        self.scheduler = sched.scheduler(time.time, time.sleep)
        def update_task(scheduler): 
            self.update_state()
            self.scheduled_event = self.scheduler.enter(5, 1, update_task, (scheduler,))
        self.scheduled_event = self.scheduler.enter(5, 1, update_task, (self.scheduler,))
        start_new_thread(self.scheduler.run, ())

        self.Bind(wx.adv.EVT_TASKBAR_LEFT_DOWN, self.on_left_down)

        self.update_state()

    def update_state(self):
        entity = self.client.get_entity(entity_id=self.entity_id)
        entity_state = entity.state.state
        entity_icon = entity.state.attributes["icon"] if "icon" in entity.state.attributes else "default"
        entity_name = entity.state.attributes["friendly_name"]

        if entity_state == "on":
            if "rgb_color" in entity.state.attributes:
                rgb_color = entity.state.attributes["rgb_color"]
            else:
                rgb_color = [253, 213, 27]
        else:
            rgb_color = [225, 225, 225]

        icon = get_icon_path(entity_icon, entity_state)
        self.set_icon(icon, entity_name)
        self.state = entity_state

    def set_icon(self, icon_path, tooltip):
        icon = wx.Icon(icon_path)
        self.SetIcon(icon, tooltip)

    def on_left_down(self, event):
        self.update_state()
        light = self.client.get_domain('homeassistant')
        light.toggle(entity_id=self.entity_id)
        print(self.entity_id, "toggle")
        time.sleep(0.1)
        self.update_state()

    def CreatePopupMenu(self):
        menu = wx.Menu()
        create_menu_item(menu, 'Exit', self.on_exit)
        return menu

    def cleanup(self):
        if self.scheduled_event:
            try:
                self.scheduler.cancel(self.scheduled_event)
            except:
                pass

        self.RemoveIcon()
        self.frame.Close()
        wx.CallAfter(self.Destroy)

    def on_exit(self, event):
        wx.Exit()

def ask(parent=None, message='', default_value=''):
    dlg = wx.TextEntryDialog(parent, message, caption="Initial Setup", value=default_value)
    dlg.ShowModal()
    result = dlg.GetValue()
    dlg.Destroy()
    return result

class App(wx.App):
    def OnInit(self):
        # init GUI
        self.frame = wx.Frame(None)
        self.SetTopWindow(self.frame)

        # load config
        config = configparser.ConfigParser()
        domains = ""
        domain_entities_ignore = ""
        try:
            config.read('config.ini')
            token = config['HASS']['Token']
            api_url = config['HASS']['ApiUrl']
            entities = config['HASS']['Entities']
            if config.has_option('HASS', 'Domains'):
                domains = config['HASS']['Domains']
            if config.has_option('HASS', 'DomainEntitiesIgnore'):
                domain_entities_ignore = config['HASS']['DomainEntitiesIgnore']
        except KeyError:
            config['HASS'] = {}
            token = config['HASS']['Token'] = ask(message='Please enter your Home Assistant Long-Lived Access Token. You can generate it at https://my.home-assistant.io/redirect/profile/.')
            api_url = config['HASS']['ApiUrl'] = ask(message='Please enter Home Assistant API Url. It should look something like this: http://192.168.0.125:8123/api')
            entities = config['HASS']['Entities'] = ask(message='Please enter the IDs (seperated by a comma) of the entities you like to add.')
            with open('config.ini', 'w') as configfile:
                config.write(configfile)

        entities = [x for x in entities.split(',') if x != '']
        domains = [x for x in domains.split(',') if x != '']
        domain_entities_ignore = [x for x in domain_entities_ignore.split(',') if x != '']
        
        # init hass client
        client = Client(api_url, token, cache_session=False)

        # init tray icons
        self.tray_icons = []
        for domain in domains:
            for entity in client.get_entities()[domain].entities:
                full_id = f"{domain}.{entity}"
                if full_id in domain_entities_ignore or full_id in entities:
                    continue

                self.tray_icons.append(TaskBarIcon(self.frame, full_id, client))

        for entity in entities:
            self.tray_icons.append(TaskBarIcon(self.frame, entity, client))

        return True

    def OnExit(self):
        for tray_icon in self.tray_icons:
            tray_icon.cleanup()

        return 0

def main():
    app = App(False)
    app.MainLoop()


if __name__ == '__main__':
    main()
