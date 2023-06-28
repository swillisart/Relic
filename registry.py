import winreg


def protocolRegistryEntry(command, protocol):
    """Creates a registry entry for the `<protocol>://<path>` 
    IE: relic://asset.
    """
    REG_PATH = 'SOFTWARE\\Classes\\{}'.format(protocol)
    REG_CMD = REG_PATH + '\\Shell\\Open\\Command'

    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, REG_PATH) as reg_key:
        winreg.SetValueEx(reg_key, '', 0, winreg.REG_SZ, 'URL:{} Protocol'.format(protocol))
        winreg.SetValueEx(reg_key, 'URL Protocol', 0, winreg.REG_SZ, '')

    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, REG_CMD) as reg_key:
        winreg.SetValueEx(reg_key, '', 0, winreg.REG_SZ, (command))
