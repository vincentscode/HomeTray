import configparser

class Config(object):
    def __init__(self, filename: str, section: str, color_section: str):
        super(Config, self).__init__()

        self._filename = filename
        self._main_section = section
        self._color_section = color_section

        self._config = configparser.ConfigParser()
        self._config.read(self._filename)
        
        if not self._config.has_section(self._main_section):
            self._config.add_section(self._main_section)
        
    @classmethod
    def load(cls, filename="config.ini", section='HASS', color_section='COLORS') -> "Config":
        return cls(filename, section, color_section)

    @property
    def token(self) -> str:
        return self._config.get(self._main_section, 'Token', fallback=None)

    @token.setter
    def token(self, value: str) -> None:
        self._config.set(self._main_section, 'Token', value=value)
        self._save()

    @property
    def api_url(self) -> str:
        return self._config.get(self._main_section, 'ApiUrl', fallback=None)

    @api_url.setter
    def api_url(self, value: str) -> None:
        self._config.set(self._main_section, 'ApiUrl', value=value)
        self._save()

    @property
    def entities(self) -> list[str]:
        entites = self._config.get(self._main_section, 'Entities', fallback="")
        return [x for x in entites.split(',') if x != '']

    @entities.setter
    def entities(self, value: list[str]) -> None:
        self._config.set(self._main_section, 'Entities', value=','.join(value))
        self._save()

    @property
    def domains(self) -> list[str]:
        domains = self._config.get(self._main_section, 'Domains', fallback="")
        return [x for x in domains.split(',') if x != '']

    @domains.setter
    def domains(self, value: list[str]) -> None:
        self._config.set(self._main_section, 'Domains', value=','.join(value))
        self._save()

    @property
    def domain_entities_ignore(self) -> list[str]:
        domain_entities_ignore = self._config.get(self._main_section, 'DomainEntitiesIgnore', fallback="")
        return [x for x in domain_entities_ignore.split(',') if x != '']

    @domain_entities_ignore.setter
    def domain_entities_ignore(self, value: list[str]) -> None:
        self._config.set(self._main_section, 'DomainEntitiesIgnore', value=','.join(value))
        self._save()

    @property
    def update_interval(self) -> list[int]:
        return self._config.getint(self._main_section, 'UpdateInterval', fallback=5)

    @property
    def color_use_rgb_value(self) -> list[int]:
        return self._config.getboolean(self._color_section, 'UseRGBValue', fallback=True)

    @property
    def color_on(self) -> list[int]:
        default = [253, 213, 27]
        return [int(x) for x in self._config.get(self._color_section, 'On', fallback=','.join(map(lambda x: str(x), default))).split(",")]

    @property
    def color_off(self) -> list[int]:
        default = [225, 225, 225]
        return [int(x) for x in self._config.get(self._color_section, 'Off', fallback=','.join(map(lambda x: str(x), default))).split(",")]

    @property
    def color_unknown(self) -> list[int]:
        default = [100, 100, 100]
        return [int(x) for x in self._config.get(self._color_section, 'Unknown', fallback=','.join(map(lambda x: str(x), default))).split(",")]

    def _save(self) -> None:
        with open(self._filename, 'w') as configfile:
            self._config.write(configfile)
