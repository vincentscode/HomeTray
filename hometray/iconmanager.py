import os
import sys
import re
import wx
import wx.svg

class IconManager(object):
    icon_handles = {}

    def __init__(self) -> None:
        super(IconManager, self).__init__()

    @property
    def _icon_base(self):
        return self._resource_path('icons')

    def _resource_path(self, relative_path):
        try:
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(".")

        return os.path.join(base_path, relative_path)
    
    def _get_icon_path(self, icon_name, state):
        icon_name = icon_name.replace(":", "-").lower()
        state = state.lower()

        icon_path = f"{self._icon_base}/{icon_name}-{state}.svg"
        if os.path.isfile(icon_path):
            return icon_path

        default_states = ["on", "off", "unavailable"]
        for fallback_state in default_states:
            icon_path = f"{self._icon_base}/{icon_name}-{fallback_state}.svg"
            if os.path.isfile(icon_path):
                return icon_path

        print("Icon not found:", icon_path)
        default_path = f"{self._icon_base}/default-{state}.svg"
        if os.path.isfile(default_path):
            return default_path
    
        return f"{self._icon_base}/unknown.svg"

    def _rgb_to_hex(self, rgb):
        r, g, b = rgb
        return '#%02x%02x%02x' % (r, g, b)

    def get_icon(self, icon_name, state, color):
        if not self.icon_handles.get(icon_name, {}).get(state, {}).get(str(color)):
            icon_path = self._get_icon_path(icon_name, state)

            with open(icon_path, "r") as f:
                icon_data = f.read()
                icon_data = re.sub(r'fill="#[0-9a-f]{3,6}"', f'fill="{self._rgb_to_hex(color)}"', icon_data)

            taskbar_height = wx.GetClientDisplayRect().GetPosition().y

            svg: wx.svg.SVGimage = wx.svg.SVGimage.CreateFromBytes(icon_data.encode(), units="px", dpi=300, do_copy=False)
            icon: wx.Bitmap = svg.ConvertToScaledBitmap(wx.Size(taskbar_height, taskbar_height))

            self.icon_handles.setdefault(icon_name, {})
            self.icon_handles[icon_name].setdefault(state, {})
            self.icon_handles[icon_name][state].setdefault(str(color), icon)

        return self.icon_handles[icon_name][state][str(color)]
