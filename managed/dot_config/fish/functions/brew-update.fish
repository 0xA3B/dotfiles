function brew-update --description "Update, upgrade, and cleanup Homebrew"
    brew update
    brew upgrade --no-ask
    brew cleanup
end
