#!/bin/env python3

from pyfiglet import figlet_format as figlet
import os
import requests
import sys

API = 'http://localhost:7999'
CONTEXT = ''
SHOW_HELP_BANNER = 1

BLACK = '\x1b[30m'
RED  ='\x1b[31m'
GREEN = '\x1b[32m'
YELLOW = '\x1b[33m'
BLUE = '\x1b[34m'
MAGENTA = '\x1b[35m'
CYAN = '\x1b[36m'
GRAY = '\x1b[90m'
L_GRAY = '\x1b[37m'
L_RED = '\x1b[91m'
L_GREEN = '\x1b[92m'
L_YELLOW = '\x1b[93m'
L_BLUE = '\x1b[94m'
L_MAGENTA = '\x1b[95m'
L_CYAN = '\x1b[96m'
WHITE = '\x1b[97m'
BG_BLACK = '\x1b[40m'
BG_RED = '\x1b[41;30m'
BG_GREEN = '\x1b[42;30m'
BG_YELLOW = '\x1b[43;30m'
BG_BLUE = '\x1b[44;30m'
BG_MAGENTA = '\x1b[45;30m'
BG_CYAN = '\x1b[46;30m'
BG_GRAY = '\x1b[47;30m'
END = '\x1b[0m'


def do_Command(Args):
    global CONTEXT

    OBJ = Args.pop(0) if Args else ''

    if OBJ == '':
        CONTEXT = '_SHELL_'
    elif OBJ in ('f', 'fetch'):
        pass #run_Fetch_Command()
    elif OBJ in ('G', 'gcs'):
        cache_scripts_gen()
    elif OBJ in ('h', 'host'):
        do_Host_Command(Args)
    elif OBJ in ('i', 'ipam'):
        do_Ipam_Command(Args)
    elif OBJ in ('n', 'node'):
        do_Node_Command(Args)
    elif OBJ in ('o', 'os'):
        do_OS_Command(Args)
    elif OBJ in ('s', 'status'):
        for svc in ['dnsmasq','nginx','wendy']: #run_Status_Command()
            print(f"{CYAN}-----------------------------------------  {svc}  -----------------------------------------{END}")
            os.system(f'SYSTEMD_COLORS=1 systemctl status {svc} | head -n 9')
    elif OBJ in ('sn', 'subnet'):
        do_Subnet_Command(Args)
    elif OBJ in ('t', 'tail'):
        os.system('tail -n 3 -f /var/log/nginx/access.log')
    elif OBJ in ('w', 'watch'):
        pass
    elif OBJ in ('?', 'help'):
        show_Help()
    else:
        print(f"{RED}What do you want to do ?{END}")
        show_Help()


def bob_Shell():
    global CONTEXT, SHOW_HELP_BANNER
    SHOW_HELP_BANNER = 0

    if CONTEXT == '_SHELL_':
        CONTEXT = ''
    while True:
        ctx = '' if CONTEXT == '' else f' {CONTEXT}'
        Noun = input(f'BoB{ctx}> ')

        if Noun == '':
            CONTEXT = ''
            print()
        elif Noun in ('q', 'quit'):
            break
        else:
            if CONTEXT:
                do_Command([CONTEXT] + Noun.split(' '))
            else:
                do_Command(Noun.split(' '))


def cache_scripts_gen():
    req = requests.post(f'{API}/cache/scripts')
    if req.status_code == 200:
        print(f'{GREEN}Scripts genetated{END}')
    else:
        print(f"{RED}There was a problem{END}")


def show_Help():
    if SHOW_HELP_BANNER:
        bob = figlet('BoB the Workman', font='slant', width=120)
        print(f"""{bob} - your gateway to automated builds of Physicals (and virtuals)\n
Call with: {CYAN}bob <system-action> | <object> [<action>] [<extra_parameters> ...]{END}""")
    print(f"""  The following {WHITE}Objects{END} can be worked with:
    {WHITE}G  | gcs{END}     - generate cache scripts (fetch and populate)
    {WHITE}h  | host{END}    - perform {MAGENTA}host{END} actions
    {WHITE}i  | ipam{END}    - perform {MAGENTA}IPAM{END} actions
    {WHITE}n  | node{END}    - perform {MAGENTA}node{END} actions
    {WHITE}o  | os{END}      - perform {MAGENTA}OS{END} actions
    {WHITE}sn | subnet{END}  - perform {MAGENTA}subnet{END} actions
  The following {WHITE}System Actions{END} can be performed:
    {WHITE}f  | fetch{END}  - perform a fetch
    {WHITE}?  | help{END}   - show this help :)
    {WHITE}s  | status{END} - show the status of Bob components
    {WHITE}t  | tail{END}   - tail the web (Wendy) logs.
    {WHITE}w  | watch{END}  - start watching the build status file.
For more details, run : {CYAN}man bob{END}""")


## HOST Functions ---------------------------------------------------------------------------------

def do_Host_Command(Args):
    global CONTEXT
    
    ACTION = Args.pop(0) if Args else ''

    if ACTION == '':
        CONTEXT = 'host'
    elif ACTION in ('a', 'add'):
        if len(Args) > 2:
            host_Add(Args)
        else:
            print(f'{RED}Please specify at least <hostname> <IP> <MAC> {END}')
    elif ACTION in ('b', 'build'):
        if Args:
            host_Build(Args)
    elif ACTION in ('c', 'complete'):
        if Args:
            host_Complete(Args)
        else:
            print(f'{RED}Please specify host to complete{END}')
    elif ACTION in ('d', 'delete'):
        if Args:
            host_Delete(Args)
        else:
            print(f'{RED}Please specify host to delete{END}')
    elif ACTION in ('e', 'edit'):
            pass
    elif ACTION in ('l', 'list'):
            host_List()
    elif ACTION == '?':
            print(f'{CYAN}host {WHITE}a{END}dd | build | complete | delete | edit | list{END}')


def host_Add(Args):
    host = {'name':Args.pop(0), 'ip':Args.pop(0), 'mac':Args.pop(0)}
    if Args:
        host['os_name'] = Args.pop(0)
    if Args:
        host['os_version'] = Args.pop(0)
    #
    req = requests.post(f'{API}/host', json=host)
    #
    if req.status_code == 200:
        print(f'{GREEN}New host created added{END}')
    elif req.status_code == 422:
        Detail = req.json()['detail']
        if type(Detail) == str:
            print(f'{RED}Error: {Detail}{END}')
        else:
            for deet in Detail:
                print(f"{RED}{deet['msg']}{END}")
    else:
        print(f'{YELLOW}Unknown response {END}')
        print(req)
        print(req.text)


def host_Build(Args):
    hn = Args.pop(0)
    Params = {}
    if Args:
        Params['os_name'] = Args.pop(0)
    if Args:
        Params['os_version'] = Args.pop(0)
    #
    req = requests.patch(f'{API}/host/{hn}/build', json = Params)
    #
    if req.status_code == 200:
        print(f'Build mode enabled for {hn}')
    elif req.status_code == 404:
        print(f'{RED}Host not found{END}')
    else:
        print(f'{YELLOW}Unknown response{END}')


def host_Complete(Args):
    hn = Args.pop(0)
    req = requests.patch(f'{API}/host/{hn}/complete')
    if req.status_code == 200:
        print(f'Build mode disabled for {hn}')
    elif req.status_code == 404:
        print(f'{RED}Host not found{END}')
    else:
        print(f'{YELLOW}Unknown response{END}')


def host_Delete(Args):
    hn = Args.pop(0)
    req = requests.delete(f'{API}/host/{hn}')
    if req.status_code == 200:
            print(f'Host "{hn}" deleted')
    elif req.status_code == 404:
        print(f'{RED}Host not found{END}')
    else:
        print(f'{YELLOW}Unknown response{END}')


def host_List():
    req = requests.get(f'{API}/host')
    Hosts = req.json()
    if len(Hosts) == 0:
        print( f"{YELLOW}You don't have any hosts yet{END}")
    else:
        print(f'{BG_GRAY}  Hostname        MAC               / IP              OS        Version          Disk        Build ?   {END}')
        for h in Hosts:
            bld = GRAY if h['target'] == 'local' else RED
            print(f"  {h['name']:15} {BLUE}{h['mac']} / {CYAN}{h['ip']:15}{END} {h['os_name']:9} {h['os_version']:16} {h['disk']:11} {bld}{h['target']}{END}")


## IPAM Functions ---------------------------------------------------------------------------------

def do_Ipam_Command(Args):
    global CONTEXT
    
    Args.append('')
    ACTION = Args.pop(0)

    if ACTION == '':
        CONTEXT = 'ipam'
    elif ACTION in ('l', 'list'):
        ipam_List()
    else:
        print(f"{RED}What ?{END}")


## NODE Functions ---------------------------------------------------------------------------------

def do_Node_Command(Args):
    global CONTEXT
    
    Args.append('')
    ACTION = Args.pop(0)

    if ACTION == '':
        CONTEXT = 'node'
    elif ACTION in ('l', 'list'):
        node_List()
    else:
        print(f"{RED}What ?{END}")


## OS Functions ---------------------------------------------------------------------------------

def do_OS_Command(Args):
    global CONTEXT
    
    Args.append('')
    ACTION = Args.pop(0)

    if ACTION == '':
        CONTEXT = 'os'
    elif ACTION in ('l', 'list'):
        os_List()
    else:
        print(f"{RED}What ?{END}")


def os_List():
    Systems = requests.get(f'{API}/os').json()
    if len(Systems) == 0:
        print( f"{YELLOW}You don't have any Operating Systems yet{END}")
    else:
        print(f'{BG_GRAY}  Name         Version          URL                                                            {END}')
        for os in Systems:
            Versions = requests.get(f"{API}/osver/{os['name']}").json()
            for osv in Versions:
                print(f"  {osv['os_name']:12} {osv['os_version']:16} {os['base_url']}/{osv['url']}")


## SUBNET Functions ---------------------------------------------------------------------------------

def do_Subnet_Command(Args):
    global CONTEXT
    
    Args.append('')
    ACTION = Args.pop(0)

    if ACTION == '':
        CONTEXT = 'subnet'
    elif ACTION in ('l', 'list'):
        subnet_List()
    else:
        print(f"{RED}What ?{END}")


def subnet_List():
    req = requests.get(f'{API}/subnet')
    Subnets = req.json()
    if len(Subnets) == 0:
        print( f"{YELLOW}You don't have any subnets yet{END}")
    else:
        print(f'{BG_GRAY}  Network                    Gateway         Name Servers                   Node                       {END}')
        for sn in Subnets:
            net = f"{sn['network']} / {sn['cidr']}"
            print(f"  {net:26} {sn['gateway']:15} {sn['nameservers']:30} {sn['node']:24}{END}")


###=======================================================================
### MAIN

sys_argv = sys.argv
sys_argv.pop(0)
do_Command(sys_argv)
if CONTEXT != '':
    bob_Shell()
