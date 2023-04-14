"""Everything related to icons"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path
import wx
import wx.svg


class PathHelper:
    """Helper class for working with paths"""

    @staticmethod
    def to_absolute_path(relative_path: str | Path) -> Path:
        """Convert a relative path to an absolute path for the current environment"""

        if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
            base_path = Path(getattr(sys, '_MEIPASS'))  # pylint: disable=no-member
        else:
            base_path = Path(os.path.abspath('.'))

        res = base_path / Path(relative_path)
        print(base_path, relative_path, res)
        return res

class IconManager:
    """Manages icon handles for the application"""
    icon_handles: dict[str, dict[str, dict[str, wx.Bitmap]]] = {}

    _icon_base: Path = PathHelper.to_absolute_path('icons')

    def _get_icon_path(self, icon_name: str, state: str) -> str:
        icon_name = icon_name.replace(':', '-').lower()
        state = state.lower()

        icon_path = f'{self._icon_base}/{icon_name}-{state}.svg'
        if os.path.isfile(icon_path):
            return icon_path

        default_states = ['on', 'off', 'unavailable']
        for fallback_state in default_states:
            icon_path = f'{self._icon_base}/{icon_name}-{fallback_state}.svg'
            if os.path.isfile(icon_path):
                return icon_path

        print('Icon not found:', icon_path)
        default_path = f'{self._icon_base}/default-{state}.svg'
        if os.path.isfile(default_path):
            return default_path

        return f'{self._icon_base}/unknown.svg'

    def _rgb_to_hex(self, rgb: list[int]) -> str:
        r, g, b = rgb
        return f'#{r:02x}{g:02x}{b:02x}'

    def get_icon(self, icon_name: str, state: str, color: list[int]) -> wx.Bitmap:
        """Get the colored icon for the given entity and state"""

        if not self.icon_handles.get(icon_name, {}).get(state, {}).get(str(color)):
            icon_path = self._get_icon_path(icon_name, state)

            with open(icon_path, encoding='utf8') as f:
                icon_data = f.read()
                icon_data = re.sub(r'fill="#[0-9a-f]{3,6}"', f'fill="{self._rgb_to_hex(color)}"', icon_data)

            taskbar_height = wx.GetClientDisplayRect().GetPosition().y

            svg: wx.svg.SVGimage = wx.svg.SVGimage.CreateFromBytes(icon_data.encode(), units='px', dpi=300, do_copy=False)
            icon: wx.Bitmap = svg.ConvertToScaledBitmap(wx.Size(taskbar_height, taskbar_height))

            self.icon_handles.setdefault(icon_name, {})
            self.icon_handles[icon_name].setdefault(state, {})
            self.icon_handles[icon_name][state].setdefault(str(color), icon)

        return self.icon_handles[icon_name][state][str(color)]
