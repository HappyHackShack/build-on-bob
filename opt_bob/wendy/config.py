import os
import yaml

BLACK = "\x1b[30m"
RED = "\x1b[31m"
GREEN = "\x1b[32m"
YELLOW = "\x1b[33m"
BLUE = "\x1b[34m"
MAGENTA = "\x1b[35m"
CYAN = "\x1b[36m"
GRAY = "\x1b[90m"
L_GRAY = "\x1b[37m"
L_RED = "\x1b[91m"
L_GREEN = "\x1b[92m"
L_YELLOW = "\x1b[93m"
L_BLUE = "\x1b[94m"
L_MAGENTA = "\x1b[95m"
L_CYAN = "\x1b[96m"
WHITE = "\x1b[97m"
BG_BLACK = "\x1b[40m"
BG_RED = "\x1b[41;30m"
BG_GREEN = "\x1b[42;30m"
BG_YELLOW = "\x1b[43;30m"
BG_BLUE = "\x1b[44;30m"
BG_MAGENTA = "\x1b[45;30m"
BG_CYAN = "\x1b[46;30m"
BG_GRAY = "\x1b[47;30m"
END = "\x1b[0m"

My_Dir = os.path.dirname(__file__)
Etc_Bob_Hosts = []
Config_File = "/etc/bob/config.yaml"
Hosts_File = "/etc/bob/hosts.yaml"
Recipe_File = f"{My_Dir}/../recipes.yaml"
Nginx_Base_Dir = "/usr/share/nginx/html"
Nginx_Ipxe_Dir = f"{Nginx_Base_Dir}/ipxe"
Nginx_Build_Dir = f"{Nginx_Base_Dir}/build"
Template_Dir = f"{My_Dir}/../templates"


class Bob_Config(dict):
    def get_os(self, osName):
        for os in self["os_cache"]:
            if os["name"] == osName:
                return os
        return None

    def get_os_list(self):
        return [os["name"] for os in self["os_cache"]]

    def get_os_version(self, osName, verTag):
        for os in self["os_cache"]:
            if os["name"] == osName:
                for version in os["versions"]:
                    if version["tag"] == verTag:
                        return version
        return None


with open(Config_File, "rt") as cfg:
    Config = Bob_Config(yaml.safe_load(cfg))

with open(Recipe_File, "rt") as rcp:
    Recipes = yaml.safe_load(rcp)
