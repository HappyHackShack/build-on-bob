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

do_Build() {
    HOST="$1"
    [[ $HOST == "" ]] && { echo -e "${YELLOW}What do you want me to build ?${END}"; exit 1; }
    ${OPT_BOB}/bob.py build host $HOST
}

do_Complete() {
    HOST="$1"
    [[ $HOST == "" ]] && { echo -e "${YELLOW}What do you want me to complete ?${END}"; exit 1; }
    ${OPT_BOB}/bob.py complete host $HOST
}

do_Create() {
    MAC="$1"
    IP="$2"
    HOST="$3"
    [[ $HOST == "" ]] && { echo -e "${YELLOW}What do you want me to create ?${END}"; exit 1; }
    ${OPT_BOB}/bob.py create host $MAC $IP $HOST
    systemctl restart dnsmasq
}

do_Delete() {
    HOST="$1"
    [[ $HOST == "" ]] && { echo -e "${YELLOW}What do you want me to delete ?${END}"; exit 1; }
    ${OPT_BOB}/bob.py delete host $HOST
    systemctl restart dnsmasq
}

do_Edit() {
    HOST="$1"
    OS="$2"
    [[ $OS == "" ]] && { echo -e "${YELLOW}What do you want me to edit ?${END}"; exit 1; }
    ${OPT_BOB}/bob.py edit host $HOST $OS 
}

do_Fetch() {
    NOUN="$1"
    shift
    flavor='lts'

    cd ${BOB_HTML_DIRECTORY}/alpine
    for file in initramfs modloop vmlinuz
    do
        wget -nc ${ALPINE_BASE_URL}/releases/x86_64/netboot/${file}-${flavor}
    done
}

do_List() {
    NOUN="$1"
    # Assume hosts (for now)
    ${OPT_BOB}/bob.py list hosts
}


show_Help() {
    echo -e """\nBOB the workman - your gateway to automated builds of Physicals (and virtuals)
    
    Call with: ${CYAN}$0 <action> [<object>] [<extra_parameters> ...]${END}
    The following ${WHITE}Actions${END} are possible:

    ${WHITE}create${END} - you can create ${MAGENTA}hosts${END}.\n
    ${WHITE}delete${END} - you can delete ${MAGENTA}hosts${END}.\n
    ${WHITE}edit${END} - ???????\n
    ${WHITE}help${END} - show this help :)\n
    ${WHITE}list${END} - you can list ${MAGENTA}hosts${END}.\n
    ${WHITE}test${END} - run the developer test function.\n
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
    log $ALERT "v serious"
    log $EMERG "P A N I C"

    echo -e "$RED RED $GREEN GRN $YELLOW YELL $BLUE BLUE $MAGENTA MAG $CYAN CYAN $GRAY GRAY $BLACK BLK $END."
    echo -e "$L_RED RED $L_GREEN GRN $L_YELLOW YELL $L_BLUE BLUE $L_MAGENTA MAG $L_CYAN CYAN $L_GRAY GRAY $WHITE WHT $END."
    echo -e "$BG_RED RED $BG_GREEN GRN $BG_YELLOW YELL $BG_BLUE BLUE $BG_MAGENTA MAG $BG_CYAN CYAN $BG_GRAY GRAY $BG_WHITE BLK $END."

}

###====================================================================================================================
### MAIN

VERB="$1"
shift

case $VERB in
    build)
        do_Build $*
        ;;
    complete)
        do_Complete $*
        ;;
    create)
        do_Create $*
        ;;
    delete)
        do_Delete $*
        ;;
    edit)
        do_Edit $*
        ;;
    fetch)
        do_Fetch $*
        ;;
    help)
        show_Help
        ;;
    list)
        do_List $*
        ;;
    test)
        tester
        ;;
    *)
        log $ERROR "What do you want me to do ?"
        show_Help
        ;;
esac
