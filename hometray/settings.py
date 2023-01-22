import sys
import wx
import wx.svg
import wx.adv

if getattr(sys, 'frozen', False):
    from hometray.config import Config
else:
    from config import Config

class Settings(object):
    def __init__(self, config: Config) -> None:
        super(Settings, self).__init__()
        self.config = config
    
    def initial_setup(self) -> None:
        if not self.config.token:
            token = self.ask(message='Please enter your Home Assistant Long-Lived Access Token. You can generate it at https://my.home-assistant.io/redirect/profile/.')
            if token != '':
                self.config.token = token
            else:
                raise Exception('No token provided')

        if not self.config.api_url:
            api_url = self.ask(message='Please enter Home Assistant API Url. It should look something like this: http://192.168.0.125:8123/api')
            if api_url != '':
                self.config.api_url = api_url
            else:
                raise Exception('No api url provided')

        if not self.config.entities and not self.config.domains:
            entities = self.ask(message='Please enter the IDs (seperated by a comma) of the entities you like to add.')
            if entities != '':
                self.config.entities = [x for x in entities.split(",") if x.strip() != '']
            else:
                self.config.entities = []

    def configure(self) -> None:
        window = wx.Frame(None, title="Settings", size=(300,450))
        panel = wx.Panel(window)

        def save(self, event, window, api_url, token, entities, domains, domain_entities_ignore) -> None:
            self.config.api_url = api_url.GetValue()
            self.config.token = token.GetValue()
            self.config.entities = [x for x in entities.GetValue().split(",") if x.strip() != '']
            self.config.domains = [x for x in domains.GetValue().split(",") if x.strip() != '']
            self.config.domain_entities_ignore = [x for x in domain_entities_ignore.GetValue().split(",") if x.strip() != '']
            self.config.save()
            window.Close()

        def cancel(self, event, window) -> None:
            window.Close()

        api_url_name = wx.StaticText(panel, label="Home Assistant API URL:")
        api_url = wx.TextCtrl(panel, value=self.config.api_url)
        token_name = wx.StaticText(panel, label="Home Assistant Long-Lived Access Token:")
        token = wx.TextCtrl(panel, value=self.config.token, style=wx.TE_PASSWORD)
        entities_name = wx.StaticText(panel, label="Entities:")
        entities = wx.TextCtrl(panel, value=",".join(self.config.entities))
        domains_name = wx.StaticText(panel, label="Domains:")
        domains = wx.TextCtrl(panel, value=",".join(self.config.domains))
        domain_entities_ignore_name = wx.StaticText(panel, label="Domain Entities Ignore:")
        domain_entities_ignore = wx.TextCtrl(panel, value=",".join(self.config.domain_entities_ignore))
        
        save_button = wx.Button(panel, label="Save")
        save_button.Bind(wx.EVT_BUTTON, lambda event: save(event, window, api_url, token, entities, domains, domain_entities_ignore))
        cancel_button = wx.Button(panel, label="Cancel")
        cancel_button.Bind(wx.EVT_BUTTON, lambda event: cancel(event, window))

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(api_url_name, 0, wx.ALL|wx.EXPAND, 5)
        sizer.Add(api_url, 0, wx.ALL|wx.EXPAND, 5)
        sizer.Add(token_name, 0, wx.ALL|wx.EXPAND, 5)
        sizer.Add(token, 0, wx.ALL|wx.EXPAND, 5)
        sizer.Add(entities_name, 0, wx.ALL|wx.EXPAND, 5)
        sizer.Add(entities, 0, wx.ALL|wx.EXPAND, 5)
        sizer.Add(domains_name, 0, wx.ALL|wx.EXPAND, 5)
        sizer.Add(domains, 0, wx.ALL|wx.EXPAND, 5)
        sizer.Add(domain_entities_ignore_name, 0, wx.ALL|wx.EXPAND, 5)
        sizer.Add(domain_entities_ignore, 0, wx.ALL|wx.EXPAND, 5)
        sizer.Add(save_button, 0, wx.ALL|wx.EXPAND, 5)
        sizer.Add(cancel_button, 0, wx.ALL|wx.EXPAND, 5)
        panel.SetSizer(sizer)
        sizer.Fit(window)

        window.Show()

    def ask(self, parent=None, message='', default_value='') -> str:
        dlg = wx.TextEntryDialog(parent, message, caption="Settings", value=default_value)
        dlg.ShowModal()
        result = dlg.GetValue()
        dlg.Destroy()
        return result
