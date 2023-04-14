"""Main entry point for the application"""
from __future__ import annotations

import sys
import wx
import wx.adv
from homeassistant_api import Client

if getattr(sys, 'frozen', False):
    from hometray.iconmanager import IconManager
    from hometray.tray import EntityTrayIcon
    from hometray.config import Config
    from hometray.settings import Settings
else:
    from iconmanager import IconManager  # type:ignore
    from tray import EntityTrayIcon  # type:ignore
    from config import Config  # type:ignore
    from settings import Settings  # type:ignore


class App(wx.App):
    """Main application class"""

    frame: wx.Frame
    tray_icons: list[EntityTrayIcon]

    # pylint: disable=invalid-name
    def OnInit(self) -> bool:
        """Called when the application is initialized."""

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
                full_id = f'{domain}.{entity}'
                if full_id in config.domain_entities_ignore or full_id in config.entities:
                    continue

                self.tray_icons.append(EntityTrayIcon(self.frame, full_id, client, icons, config, settings))

        for entity in config.entities:
            self.tray_icons.append(EntityTrayIcon(self.frame, entity, client, icons, config, settings))

        return True

    # pylint: disable=invalid-name
    def OnExit(self) -> int:
        """Called when the application is exiting."""
        for tray_icon in self.tray_icons:
            tray_icon.cleanup()

        return 0


def main() -> int:
    """Main entry point for the application"""
    app = App(False)
    app.MainLoop()
    return 0


if __name__ == '__main__':
    sys.exit(main())
