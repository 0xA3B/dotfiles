# Initialize Homebrew environment and preferences early so later modules can
# rely on Homebrew-managed commands and paths.

set -l brewbin /opt/homebrew/bin/brew
if test -f $brewbin
    $brewbin shellenv fish | source

    set -gx HOMEBREW_NO_AUTO_UPDATE 1
    set -gx HOMEBREW_NO_ANALYTICS 1
    set -gx HOMEBREW_NO_ENV_HINTS 1

    fish_add_path --move --prepend --path "$HOMEBREW_PREFIX/opt/coreutils/libexec/gnubin"

    # Point TLS clients at Homebrew's CA bundle, which adds the System keychain roots trusted for
    # TLS to the Mozilla set. After a keychain root changes, run `brew postinstall ca-certificates`.
    set -l ca_bundle "$HOMEBREW_PREFIX/etc/ca-certificates/cert.pem"
    if test -f $ca_bundle
        set -gx SSL_CERT_FILE $ca_bundle
        set -gx REQUESTS_CA_BUNDLE $SSL_CERT_FILE
        set -gx NODE_EXTRA_CA_CERTS $SSL_CERT_FILE
        set -gx CURL_CA_BUNDLE $SSL_CERT_FILE
    end
end
