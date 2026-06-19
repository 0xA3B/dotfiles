function brew-update --description "Update, upgrade, and cleanup Homebrew"
    brew update
    brew upgrade --yes
    brew cleanup
end
