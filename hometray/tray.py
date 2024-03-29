"""Defines elements for the system tray"""
from __future__ import annotations

import sys
import threading
import time
from typing import Callable
from typing import Any

import homeassistant_api as ha
import schedule
import wx
import wx.adv

if getattr(sys, 'frozen', False):
    from hometray.iconmanager import IconManager
    from hometray.config import Config
    from hometray.settings import Settings
else:
    from iconmanager import IconManager  # type:ignore
    from config import Config  # type:ignore
    from settings import Settings  # type:ignore


class EntityTrayIcon(wx.adv.TaskBarIcon):
    """Defines a system tray icon for a Home Assistant entity"""

    def __init__(self, frame: wx.Frame, entity_id: str, client: ha.Client, icons: IconManager, config: Config, settings: Settings) -> None:
        super().__init__()
        self.frame: wx.Frame = frame
        self.entity_id: str = entity_id
        self.domain_id: str = entity_id.split('.')[0]
        self.client: ha.Client = client
        self.icons: IconManager = icons
        self.config: Config = config
        self.settings: Settings = settings

        self.has_color_control = False

        schedule.every(self.config.update_interval).seconds.do(self.update_state)
        self.stop_updater: threading.Event = run_continuously()

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

    def update_state(self) -> None:
        """Gets the current state of the entity and updates the icon"""

        entity = self.client.get_entity(entity_id=self.entity_id)
        entity_state = entity.state.state
        entity_icon = entity.state.attributes['icon'] if 'icon' in entity.state.attributes else 'default'
        entity_name = entity.state.attributes['friendly_name'] if 'friendly_name' in entity.state.attributes else self.entity_id

        if entity_state == 'on':
            if self.config.color_use_rgb_value and 'rgb_color' in entity.state.attributes:
                self.rgb_color = entity.state.attributes['rgb_color']
                self.has_color_control = True

            else:
                self.rgb_color = self.config.color_on
        elif entity_state == 'off':
            self.rgb_color = self.config.color_off
        else:
            self.rgb_color = self.config.color_unknown

        self.set_icon(entity_icon, entity_state, self.rgb_color, entity_name)

    def pick_color(self) -> None:
        """Opens a color picker dialog"""

        data = wx.ColourData()
        data.SetChooseFull(True)
        color = wx.Colour()
        color.Set(*self.config.color_on)
        data.SetColour(color)
        dialog = wx.ColourDialog(self.frame, data)

        def set_color(color: wx.Colour) -> None:
            rgb = [color.Red(), color.Green(), color.Blue()]
            self.specific_domain.turn_on(entity_id=self.entity_id, rgb_color=rgb)
            self.rgb_color = rgb

        dialog.Bind(wx.EVT_COLOUR_CHANGED, lambda e: set_color(e.Colour))
        dialog.CenterOnScreen()
        dialog.ShowModal()
        dialog.Destroy()

    def set_icon(self, icon_name: str, icon_state: str, icon_color: list[int], tooltip: str | None) -> None:
        """Sets the icon and tooltip for the tray icon"""
        icon = self.icons.get_icon(icon_name, icon_state, icon_color)
        self.SetIcon(icon, tooltip)

    def on_left_down(self, _: Any) -> None:
        """Toggles the entity when the icon is clicked"""
        self.update_state()
        self.domain.toggle(entity_id=self.entity_id)
        time.sleep(0.1)
        self.update_state()

    def on_right_up(self, _: Any) -> None:
        """Displays the right-click menu"""
        menu = wx.Menu()
        add_menu_item(menu, 'Toggle', self.on_left_down, bold=True)
        if self.has_color_control:
            add_menu_item(menu, 'Change Color', lambda _: self.pick_color())
        menu.AppendSeparator()
        add_menu_item(menu, 'Configure HomeTray', lambda _: self.settings.configure())
        add_menu_item(menu, 'Close HomeTray', self.on_exit_clicked)
        add_menu_item(menu, 'Change Color', lambda _: self.pick_color())
        self.PopupMenu(menu)
        menu.Destroy()

    def cleanup(self) -> None:
        """Cleans up the tray icon"""
        self.stop_updater.set()
        self.RemoveIcon()
        self.frame.Close()
        wx.CallAfter(self.Destroy)

    def on_exit_clicked(self, _: Any) -> None:
        """Closes the application"""
        wx.Exit()


def run_continuously(interval: int = 1) -> threading.Event:
    """
    Continuously run, while executing pending jobs at each
    elapsed time interval.
    https://schedule.readthedocs.io/en/stable/background-execution.html
    """

    cease_continuous_run: threading.Event = threading.Event()

    class ScheduleThread(threading.Thread):
        @classmethod
        def run(cls: type[ScheduleThread]) -> None:
            while not cease_continuous_run.is_set():
                schedule.run_pending()
                time.sleep(interval)

    continuous_thread: ScheduleThread = ScheduleThread()
    continuous_thread.start()
    return cease_continuous_run


def add_menu_item(menu: wx.Menu, label: str, func: Callable[[Any], None], bold: bool = False, position: int = -1) -> wx.MenuItem:
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
