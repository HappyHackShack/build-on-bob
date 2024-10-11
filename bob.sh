#!/bin/bash

source /etc/bob/engine.sh

# What level do you want to log to teh screen
DEBUG_LEVEL=5
# What level do you want to log to syslog
SYSLOG_LEVEL=3
# The tag to apply to any syslog messages
SYSLOG_TAG='BOB'

# Logging Levels (from syslog)
EMERG=0
ALERT=1
CRIT=2
ERROR=3
WARN=4
NOTICE=5
INFO=6
DEBUG=7

# Colours
BLACK='\e[30m'
RED='\e[31m'
GREEN='\e[32m'
YELLOW='\e[33m'
BLUE='\e[34m'
MAGENTA='\e[35m'
CYAN='\e[36m'
GRAY='\e[90m'
L_GRAY='\e[37m'
L_RED='\e[91m'
L_GREEN='\e[92m'
L_YELLOW='\e[93m'
L_BLUE='\e[94m'
L_MAGENTA='\e[95m'
L_CYAN='\e[96m'
WHITE='\e[97m'
BG_BLACK='\e[40m'
BG_RED='\e[41;30m'
BG_GREEN='\e[42;30m'
BG_YELLOW='\e[43;30m'
BG_BLUE='\e[44;30m'
BG_MAGENTA='\e[45;30m'
BG_CYAN='\e[46;30m'
BG_GRAY='\e[47;30m'
END='\e[0m'
LOG_LEVEL_NAMES=( "EMERG" "ALERT" "CRIT" "ERROR" "WARN" "NOTICE" "INFO" "DEBUG" )
LOG_LEVEL_COLOURS=( "${BG_RED}${WHITE}" "${BG_RED}" "${L_RED}" "${RED}" "${L_YELLOW}" "${CYAN}" "${BLUE}" "${GRAY}" )

OPT_BOB='/opt/bob'
MY_DIR=$( dirname `realpath $0` )
[[ $MY_DIR =~ ^/usr/local/sbin$ ]] || OPT_BOB="${MY_DIR}/opt_bob"

[ "$UID" == "0" ] || { echo -e "${YELLOW}You need to be root to do this${END}"; exit 1; }
# If help invoked from command line
SHOW_HELP_BANNER=1

###====================================================================================================================
### FUNCTIONS

log() {
    # $1 = Level of message
    # $2 = the message
    LEVEL="$1"
    MSG="$2"
    CLR="${LOG_LEVEL_COLOURS[$LEVEL]}"
    TITLE="${LOG_LEVEL_NAMES[$LEVEL]}"
    # Shall we log to teh screen ?
    [[ $LEVEL -le $DEBUG_LEVEL ]] && echo -e "${CLR}${TITLE}: ${MSG}${END}"
    # Shall we send to syslog ?
    [[ $LEVEL -le $SYSLOG_LEVEL ]] && logger -t $SYSLOG_TAG -p $LEVEL "${TITLE}: ${MSG}"
}

do_Command() {
    OBJ="$1"
    shift

    case $OBJ in
        "")
            CONTEXT='_SHELL_'
            ;;
        h|host)
            do_Host_Command $*
            ;;
        f|fetch)
            cd ${BOB_HTML_DIRECTORY}
            ${BOB_HOME_DIRECTORY/}/fetch-from-cache.sh   
            ;;
        ?|help)
            show_Help
            ;;
        i|ipam)
            CONTEXT='ipam'
            ;;              
        o|os)
            do_OS_Command $*
            ;;
        s|status)
            export SYSTEMD_COLORS=1
            for SVC in dnsmasq nginx wendy; do 
            echo -e "${CYAN}-----------------------------------------  ${SVC}  ------------------------------------------${END}"
            systemctl status $SVC | head -n 9
            done
            ;;
        sn|subnet)
            CONTEXT='subnet'
            ;;              
        t|tail)
            tail -n 3 -f /var/log/nginx/access.log
            ;;
        test)
            tester
            ;;
        w|watch)
            watch -cn 1 cat /tmp/build_status
            ;;
        *)
            log $ERROR "What do you want me to do ?"
            show_Help
            ;;
    esac
}

do_Host_Command() {
    ACTION="$1"
    shift

    case $ACTION in
        "")
            CONTEXT='host'
            ;;
        a|add)
            host_Add $*
            ;;
        b|build)
            host_Build $*
            ;;
        c|complete)
            host_Complete $*
            ;;
        d|delete)
            host_Delete $*
            ;;
        e|edit)
            host_Edit $*
            ;;
        l|list)
            host_List $*
            ;;
        *)
            echo "What ?"
            ;;
    esac
}

do_OS_Command() {
    ACTION="$1"
    shift

    case $ACTION in
        "")
            CONTEXT='os'
            ;;
        l|list)
            os_List $*
            ;;
        *)
            echo "What ?"
            ;;
    esac
}

host_Add() {
    HOST="$1"
    IP="$2"
    MAC="$3"
    OS="$4"
    VER="$5"
    [[ $HOST == "" ]] && { echo -e "${YELLOW}What do you want me to add ?${END}"; return; }
    ${OPT_BOB}/bob.py host add "$HOST" "$IP" "$MAC" "$OS" "$VER"
    systemctl restart dnsmasq
}

host_Build() {
    HOST="$1"
    OS="$2"
    VER="$3"
    [[ $HOST == "" ]] && { echo -e "${YELLOW}What do you want me to build ?${END}"; return; }
    ${OPT_BOB}/bob.py host build "$HOST" "$OS" "$VER"
}

host_Complete() {
    HOST="$1"
    [[ $HOST == "" ]] && { echo -e "${YELLOW}What do you want me to complete ?${END}"; return; }
    ${OPT_BOB}/bob.py host complete "$HOST"
}

host_Delete() {
    HOST="$1"
    [[ $HOST == "" ]] && { echo -e "${YELLOW}What do you want me to delete ?${END}"; return; }
    ${OPT_BOB}/bob.py host delete "$HOST"
    systemctl restart dnsmasq
}

host_Edit() {
    HOST="$1"
    KEY="$2"
    VALUE="$3"
    [[ $VALUE == "" ]] && { echo -e "${YELLOW}What do you want me to edit ?${END}"; return; }
    ${OPT_BOB}/bob.py host edit "$HOST" "$KEY" "$VALUE"
    # Slight overkill to do this for every edit
    systemctl restart dnsmasq
}

host_List() {
    ${OPT_BOB}/bob.py host list "$1"
}

os_List() {
    ${OPT_BOB}/bob.py os list "$1"
}

show_Help() {
    [[ $SHOW_HELP_BANNER == 0 ]] || {
        echo -e """\nBoB the workman - your gateway to automated builds of Physicals (and virtuals)
    
    Call with: ${CYAN}$0 <action> [<object>] [<extra_parameters> ...]${END}"""
    }
    echo -e """    The following ${WHITE}Actions${END} are possible:

    ${WHITE}f  | fetch${END}   - perform a fetch
    ${WHITE}h  | host${END}    - perform ${MAGENTA}host${END} actions
    ${WHITE}?  | help${END}    - show this help :)
    ${WHITE}i  | ipam${END}    - perform ${MAGENTA}ipam${END} actions
    ${WHITE}o  | os${END}      - perform ${MAGENTA}ipam${END} actions
    ${WHITE}s  | status${END}  - show the status of Bob components
    ${WHITE}sn | subnet${END}  - perform ${MAGENTA}ipam${END} actions
    ${WHITE}t  | tail${END}    - tail the web (Wendy) logs.
    ${WHITE}w  | watch${END}   - start watching the build status file.\n
    For more details, run : ${CYAN}man bob${END}
    """
}

tester() {
    echo $MY_DIR
    echo $OPT_BOB

    log $DEBUG "Hello world"
    log $INFO "yada yada"
    log $NOTICE "something"
    log $WARN "Oh dear"
    log $ERROR "wen't wrong"
    log $CRIT "badly"
    # log $ALERT "v serious"
    # log $EMERG "P A N I C"

    echo -e "$RED RED $GREEN GRN $YELLOW YELL $BLUE BLUE $MAGENTA MAG $CYAN CYAN $GRAY GRAY $BLACK BLK $END."
    echo -e "$L_RED RED $L_GREEN GRN $L_YELLOW YELL $L_BLUE BLUE $L_MAGENTA MAG $L_CYAN CYAN $L_GRAY GRAY $WHITE WHT $END."
    echo -e "$BG_RED RED $BG_GREEN GRN $BG_YELLOW YELL $BG_BLUE BLUE $BG_MAGENTA MAG $BG_CYAN CYAN $BG_GRAY GRAY $BG_WHITE BLK $END."
}

bob_shell() {
    SHOW_HELP_BANNER=0

    [[ $CONTEXT == '_SHELL_' ]] && CONTEXT=''
    while :
    do
        echo -n "Bob"
        [[ $CONTEXT == '' ]] || echo -n " "
        echo -n "$CONTEXT> "
        read NOUN

        case $NOUN in
            "")
                CONTEXT=''
                ;;
            q|quit)
                break
                ;;
            *)
                do_Command $CONTEXT $NOUN
                ;;
        esac
    done
}

###====================================================================================================================
### MAIN

do_Command $*
[[ "$CONTEXT" == '' ]] || bob_shell
