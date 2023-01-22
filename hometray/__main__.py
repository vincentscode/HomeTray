import wx
import wx.adv
import sys
from homeassistant_api import Client

if getattr(sys, 'frozen', False):
    from hometray.iconmanager import IconManager
    from hometray.tray import EntityTrayIcon
    from hometray.config import Config
    from hometray.settings import Settings
else:
    from iconmanager import IconManager
    from tray import EntityTrayIcon
    from config import Config
    from settings import Settings


class App(wx.App):
    def OnInit(self):
        # init GUI
        self.frame = wx.Frame(None)
        self.SetTopWindow(self.frame)

        # load config
        config = Config.load()
        settings = Settings(config)
        settings.initial_setup()
        
        # init hass client
        client = Client(config.api_url, config.token, cache_session=False)

        # init tray icons
        icons = IconManager()

        self.tray_icons = []
        for domain in config.domains:
            for entity in client.get_entities()[domain].entities:
                full_id = f"{domain}.{entity}"
                if full_id in config.domain_entities_ignore or full_id in config.entities:
                    continue

                self.tray_icons.append(EntityTrayIcon(self.frame, full_id, client, icons, config, settings))

        for entity in config.entities:
            self.tray_icons.append(EntityTrayIcon(self.frame, entity, client, icons, config, settings))

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
