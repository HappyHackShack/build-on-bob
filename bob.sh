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

do_Add() {
    HOST="$1"
    IP="$2"
    MAC="$3"
    [[ $HOST == "" ]] && { echo -e "${YELLOW}What do you want me to add ?${END}"; exit 1; }
    ${OPT_BOB}/bob.py add host "$HOST" "$IP" "$MAC"
    systemctl restart dnsmasq
}

do_Build() {
    HOST="$1"
    OS="$2"
    [[ $HOST == "" ]] && { echo -e "${YELLOW}What do you want me to build ?${END}"; exit 1; }
    ${OPT_BOB}/bob.py build host "$HOST" "$OS"
}

do_Complete() {
    HOST="$1"
    [[ $HOST == "" ]] && { echo -e "${YELLOW}What do you want me to complete ?${END}"; exit 1; }
    ${OPT_BOB}/bob.py complete host "$HOST"
}

do_Delete() {
    HOST="$1"
    [[ $HOST == "" ]] && { echo -e "${YELLOW}What do you want me to delete ?${END}"; exit 1; }
    ${OPT_BOB}/bob.py delete host "$HOST"
    systemctl restart dnsmasq
}

do_Edit() {
    HOST="$1"
    KEY="$2"
    VALUE="$3"
    [[ $VALUE == "" ]] && { echo -e "${YELLOW}What do you want me to edit ?${END}"; exit 1; }
    ${OPT_BOB}/bob.py edit host "$HOST" "$KEY" "$VALUE"
}

do_Fetch() {
    # Start with the alpine boot files
    flavor='lts'
    cd ${BOB_HTML_DIRECTORY}/alpine
    for file in initramfs modloop vmlinuz; do
        echo -n -e "${GRAY}ALPINE.${file}: ${END}"
        wget -nc ${ALPINE_BASE_URL}/releases/x86_64/netboot/${file}-${flavor}
    done

    # Now get each of the cloud images
    cd ../images
    fetch_Cloud_Image "$ALPINE_QCOW_URL" "$ALPINE_IMAGE_FILE"
    fetch_Cloud_Image "$ROCKY_QCOW_URL" "$ROCKY_IMAGE_FILE"
    fetch_Cloud_Image "$UBUNTU_QCOW_URL" "$UBUNTU_IMAGE_FILE"
}

do_List() {
    NOUN="$1"
    # Assume hosts (for now)
    ${OPT_BOB}/bob.py list "$NOUN"
}


fetch_Cloud_Image() {
    URL="$1"
    FILE="$2"
    QCOW="${FILE}.qcow2"
    RAW="${FILE}.raw"
    RAW_GZ="${RAW}.gz"
    #
    echo -e "${CYAN}Checking ${FILE}${END}"
    [ -f ${QCOW} ] || {
        echo -e "${YELLOW}Fetching ${FILE}${END}"
        wget "$URL" -O "${QCOW}"
    }
    [ -f ${RAW}.gz ] || {
        echo -e "${YELLOW}Converting ${FILE} ...${END}"
        qemu-img convert -O raw "${QCOW}" "${RAW}"
        echo -e "${YELLOW}and gzipping ${FILE} ...${END}"
        gzip "${RAW}"
    }
}


show_Help() {
    echo -e """\nBoB the workman - your gateway to automated builds of Physicals (and virtuals)
    
    Call with: ${CYAN}$0 <action> [<object>] [<extra_parameters> ...]${END}
    The following ${WHITE}Actions${END} are possible:

    ${WHITE}a | add${END}      - you can add a new ${MAGENTA}<Host>${END}. <IP> <MAC>
    ${WHITE}b | build${END}    - you can put a ${MAGENTA}host${END} into build mode.
    ${WHITE}c | complete${END} - you can complete the build of a ${MAGENTA}host${END}.
    ${WHITE}d | delete${END}   - you can delete a ${MAGENTA}host${END}.
    ${WHITE}e | edit${END}     - set the ${MAGENTA}<host> <hostname|mac|ip_addr|disk> <value>${END}
    ${WHITE}h | help${END}     - show this help :)
    ${WHITE}l | list${END}     - you can list ${MAGENTA}h|hosts | r|recipes${END}.
    ${WHITE}s | status${END}   - show the status of BoB.
    ${WHITE}t | tail${END}     - tail the web (Wendy) logs.
    ${WHITE}    test${END}     - run the developer test function.
    ${WHITE}w | watch${END}    - start watching the build status file.\n
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
    a|add)
        do_Add $*
        ;;
    b|build)
        do_Build $*
        ;;
    c|complete)
        do_Complete $*
        ;;
    d|delete)
        do_Delete $*
        ;;
    e|edit)
        do_Edit $*
        ;;
    f|fetch)
        do_Fetch $*
        ;;
    h|help)
        show_Help
        ;;
    l|list)
        do_List $*
        ;;
    s|status)
        systemctl status wendy
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
