# Initialize Homebrew environment and preferences early so later modules can
# rely on Homebrew-managed commands and paths.

brewbin="/opt/homebrew/bin/brew"
if [[ -f $brewbin ]]; then
  eval "$("$brewbin" shellenv zsh)"

  export HOMEBREW_NO_AUTO_UPDATE=1
  export HOMEBREW_NO_ANALYTICS=1
  export HOMEBREW_NO_ENV_HINTS=1

  gnubin="$HOMEBREW_PREFIX/opt/coreutils/libexec/gnubin"
  if [[ -d $gnubin ]]; then
    path=("$gnubin" $path)
  fi

  # Point TLS clients at Homebrew's CA bundle, which adds the System keychain roots trusted for
  # TLS to the Mozilla set. After a keychain root changes, run `brew postinstall ca-certificates`.
  ca_bundle="$HOMEBREW_PREFIX/etc/ca-certificates/cert.pem"
  if [[ -f $ca_bundle ]]; then
    export SSL_CERT_FILE="$ca_bundle"
    export REQUESTS_CA_BUNDLE="$SSL_CERT_FILE"
    export NODE_EXTRA_CA_CERTS="$SSL_CERT_FILE"
    export CURL_CA_BUNDLE="$SSL_CERT_FILE"
  fi
fi
