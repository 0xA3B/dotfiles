#############
# Functions #
#############

# Extracts different types of compressed files in one command
# Author: Jayson Grace
extract() {
    if [ -f $1 ] ; then
        case $1 in
            *.tar.bz2)   tar xvjf $1    ;;
            *.tar.gz)    tar xvzf $1    ;;
            *.bz2)       bunzip2 $1     ;;
            *.rar)       unrar x $1     ;;
            *.gz)        gunzip $1      ;;
            *.tar)       tar xvf $1     ;;
            *.tbz2)      tar xvjf $1    ;;
            *.tgz)       tar xvzf $1    ;;
            *.zip)       unzip $1       ;;
            *.Z)         uncompress $1  ;;
            *.7z)        7z x $1        ;;
            *)           echo "don't know how to extract '$1'..." ;;
        esac
    else
        echo "'$1' is not a valid file"
    fi
}

# Appends a directory to a path if it does not already exist
# Author: http://superuser.com/questions/39751/add-directory-to-path-if-its-not-already-there
addToPath() {
    if [ -d "$1" ] && [[ ":$PATH:" != *":$1:"* ]] ; then
        if [ $2 = "before" ] ; then
            PATH="$1${PATH:+":$PATH"}"
        else
            PATH="${PATH:+"$PATH:"}$1"
        fi
    fi
}
