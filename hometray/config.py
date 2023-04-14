"""Handles all configuration related tasks."""
from __future__ import annotations

import configparser
from collections.abc import Iterable
from typing import Any
from typing import Callable
from typing import Generic
from typing import get_args
from typing import TypeVar

T = TypeVar('T')


class ConfigProperty(Generic[T]):
    """A generic config property"""

    _configured: bool = False
    _config_parser: configparser.ConfigParser
    _section: str
    _key: str
    _default: T
    _deserialize: Callable[[str], T]
    _serialize: Callable[[T], str]
    _save: Callable[[], None]

    @classmethod
    def configure(cls, config_parser: configparser.ConfigParser, section: str, key: str, default: T, deserialize: Callable[[str], T] | None = None, serialize: Callable[[T], str] | None = None, save: Callable[[], None] | None = None) -> ConfigProperty[T]:
        """Generate a confgiured instance of the property"""

        def identity(x: T) -> T:
            return x

        def nop() -> None:
            pass

        instance = cls()
        instance._config_parser = config_parser
        instance._section = section
        instance._key = key
        instance._default = default
        instance._deserialize = identity if deserialize is None else deserialize  # type: ignore
        instance._serialize = identity if serialize is None else serialize  # type: ignore
        instance._save = nop if save is None else save
        return instance

    def __get__(self, instance: Any | None, owner: Any | None) -> T:
        print('__get__', instance, owner)
        if not self._config_parser.has_option(self._section, self._key):
            return self._default
        return self._deserialize(self._config_parser.get(self._section, self._key))

    def __set__(self, instance: Any | None, value: ConfigProperty[Any] | T) -> None:
        print('__set__', instance, value, type(self))
        if not self._configured:
            self.__dict__ = value.__dict__
            self._configured = True
        else:
            self._config_parser.set(self._section, self._key, value=self._serialize(value))
            self._save()


class SerializationHelpers:
    """Helper class for serializing and deserializing config values"""

    @staticmethod
    def deserialize_list(value: str) -> list[str]:
        """Deserialize a comma separated list"""
        return list(filter(lambda x: x != '', value.split(',')))

    @staticmethod
    def serialize_list(value: list[str]) -> str:
        """Serialize a list to a comma separated string"""
        return ','.join(value)

    @staticmethod
    def deserialize_color(value: str) -> list[int]:
        return list(map(int, value.split(',')))

    @staticmethod
    def serialize_color(value: list[int]) -> str:
        return ','.join(map(str, value))


class Config:
    """Configuration file wrapper class"""

    token: ConfigProperty[str] = ConfigProperty()
    api_url: ConfigProperty[str] = ConfigProperty()
    entities: ConfigProperty[list[str]] = ConfigProperty()
    domains: ConfigProperty[list[str]] = ConfigProperty()
    domain_entities_ignore: ConfigProperty[list[str]] = ConfigProperty()
    update_interval: ConfigProperty[int] = ConfigProperty()

    color_use_rgb_value: ConfigProperty[bool] = ConfigProperty()
    color_on: ConfigProperty[list[int]] = ConfigProperty()
    color_off: ConfigProperty[list[int]] = ConfigProperty()
    color_unknown: ConfigProperty[list[int]] = ConfigProperty()

    def __init__(self, filename: str, section: str, color_section: str):
        super().__init__()

        self._filename = filename
        self._main_section = section
        self._color_section = color_section

        self._config = configparser.ConfigParser()
        self._config.read(self._filename)

        self._ensure_section_exists(self._main_section)
        self._ensure_section_exists(self._color_section)

        # main section
        self.token = ConfigProperty.configure(self._config, self._main_section, 'Token', None, save=self.save)
        self.api_url = ConfigProperty.configure(self._config, self._main_section, 'ApiUrl', None, save=self.save)
        self.entities = ConfigProperty.configure(self._config, self._main_section, 'Entities', [], SerializationHelpers.deserialize_list, SerializationHelpers.serialize_list, self.save)
        self.domains = ConfigProperty.configure(self._config, self._main_section, 'Domains', [], SerializationHelpers.deserialize_list, SerializationHelpers.serialize_list, self.save)
        self.domain_entities_ignore = ConfigProperty.configure(self._config, self._main_section, 'DomainEntitiesIgnore', [], SerializationHelpers.deserialize_list, SerializationHelpers.serialize_list, self.save)
        self.update_interval = ConfigProperty.configure(self._config, self._main_section, 'UpdateInterval', 5, int, str, self.save)

        # color section
        self.color_use_rgb_value = ConfigProperty.configure(self._config, self._color_section, 'UseRGBValue', True, bool, str, self.save)
        self.color_on = ConfigProperty.configure(self._config, self._color_section, 'On', [253, 213, 27], SerializationHelpers.deserialize_color, SerializationHelpers.serialize_color, self.save)
        self.color_off = ConfigProperty.configure(self._config, self._color_section, 'Off', [225, 225, 225], SerializationHelpers.deserialize_color, SerializationHelpers.serialize_color, self.save)
        self.color_unknown = ConfigProperty.configure(self._config, self._color_section, 'Unknown', [100, 100, 100], SerializationHelpers.deserialize_color, SerializationHelpers.serialize_color, self.save)

    @classmethod
    def load(cls: type[Config], filename: str = 'config.ini', section: str = 'HASS', color_section: str = 'COLORS') -> Config:
        """Load the config from the given file"""
        return cls(filename, section, color_section)

    def save(self) -> None:
        with open(self._filename, 'w', encoding='utf8') as configfile:
            self._config.write(configfile)

    def _ensure_section_exists(self, section_name: str) -> None:
        if not self._config.has_section(section_name):
            self._config.add_section(section_name)


if __name__ == '__main__':
    c = Config.load()
    print(c.token)
    print(c.color_on)
