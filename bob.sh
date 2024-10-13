#!/bin/bash

# What level do you want to log to teh screen
DEBUG_LEVEL=5
# What level do you want to log to syslog
SYSLOG_LEVEL=3
# The tag to apply to any syslog messages
SYSLOG_TAG='BOB'
#
WENDY_CLI='http://localhost:5000/cli'

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

# Get the two directories from the YAML config
BOB_HOME_DIRECTORY=$( grep bob_home_directory /etc/bob/config.yaml | awk '{ print $2 }' )
BOB_HTML_DIRECTORY=$( grep bob_html_directory /etc/bob/config.yaml | awk '{ print $2 }' )
OPT_BOB="$BOB_HOME_DIRECTORY"
MY_DIR=$( dirname `realpath $0` )
[[ $MY_DIR =~ ^/home/ ]] && OPT_BOB="${MY_DIR}/opt_bob"

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
        f|fetch)
            cd ${BOB_HTML_DIRECTORY}
            ${BOB_HOME_DIRECTORY/}/fetch-from-cache.sh   
            ;;
        h|host)
            do_Host_Command $*
            ;;
        i|ipam)
            do_IPAM_Command $*
            ;;              
        o|os)
            do_OS_Command $*
            ;;
        r|recipe)
            do_Recipe_Command $*
            ;;
        s|status)
            export SYSTEMD_COLORS=1
            for SVC in dnsmasq nginx wendy; do 
            echo -e "${CYAN}-----------------------------------------  ${SVC}  ------------------------------------------${END}"
            systemctl status $SVC | head -n 9
            done
            ;;
        sn|subnet)
            do_Subnet_Command $*
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
        "?"|help)
            show_Help
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
            curl -X POST "${WENDY_CLI}/host/add?name=${1}&ip=${2}&mac=${3}&os=${4}&version=${5}"
            ;;
        b|build)
            curl -X PATCH "${WENDY_CLI}/host/build?name=${1}&os=${2}&version=${3}"
            ;;
        c|complete)
            curl -X PATCH "${WENDY_CLI}/host/complete?name=${1}&mac=${1}"
            ;;
        d|delete)
            curl -X DELETE "${WENDY_CLI}/host/delete?name=${1}"
            ;;
        e|edit)
            curl -X PATCH "${WENDY_CLI}/host/edit?name=${1}&${2}&${3}&${4}&${5}&${6}&${7}"
            ;;
        l|list)
            curl "${WENDY_CLI}/host/list?filter=$1"
            ;;
        *)
            echo "What ?"
            ;;
    esac
}

do_IPAM_Command() {
    ACTION="$1"
    shift

    case $ACTION in
        "")
            CONTEXT='ipam'
            ;;
        l|list)
            curl "${WENDY_CLI}/ipam/list"
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
            curl "${WENDY_CLI}/os/list"
            ;;
        *)
            echo "What ?"
            ;;
    esac
}

do_Recipe_Command() {
    ACTION="$1"
    shift

    case $ACTION in
        "")
            CONTEXT='recipe'
            ;;
        l|list)
            curl "${WENDY_CLI}/recipe/list"
            ;;
        *)
            echo "What ?"
            ;;
    esac
}

do_Subnet_Command() {
    ACTION="$1"
    shift

    case $ACTION in
        "")
            CONTEXT='subnet'
            ;;
        l|list)
            curl "${WENDY_CLI}/subnet/list"
            ;;
        *)
            echo "What ?"
            ;;
    esac
}

show_Help() {
    [[ $SHOW_HELP_BANNER == 0 ]] || {
        echo -e """\nBoB the workman - your gateway to automated builds of Physicals (and virtuals)
    
    Call with: ${CYAN}$0 <action> [<object>] [<extra_parameters> ...]${END}"""
    }
    echo -e """  The following ${WHITE}Objects${END} can be worked with:
    ${WHITE}h  | host${END}    - perform ${MAGENTA}host${END} actions
    ${WHITE}i  | ipam${END}    - perform ${MAGENTA}IPAM${END} actions
    ${WHITE}o  | os${END}      - perform ${MAGENTA}OS${END} actions
    ${WHITE}r  | recipes${END} - perform ${MAGENTA}recipe${END} actions
    ${WHITE}sn | subnet${END}  - perform ${MAGENTA}subnet${END} actions
  The following ${WHITE}System Actions${END} can be performed:
    ${WHITE}f  | fetch${END}  - perform a fetch
    ${WHITE}?  | help${END}   - show this help :)
    ${WHITE}s  | status${END} - show the status of Bob components
    ${WHITE}t  | tail${END}   - tail the web (Wendy) logs.
    ${WHITE}w  | watch${END}  - start watching the build status file.
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
        read -e NOUN

        case $NOUN in
            "")
                CONTEXT=''
                echo
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
