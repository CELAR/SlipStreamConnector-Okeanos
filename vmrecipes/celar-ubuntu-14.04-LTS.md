These steps are needed in order to upgrade "Ubuntu 14.04 Server LTS" to an image suitable for SlipStream, with the following capabilities:

1. Orchestrator VM
2. VM for which "Build Image" is supported.

```
# convenience, skip if want to user-interaction
$ export DEBIAN_FRONTEND=noninteractive

$ aptitude update
$ aptitude -y upgrade
$ aptitude -y dist-upgrade

# This installs pip 1.5.4 which should be enough
$ aptitude -y install python-pip

# This is needed for the installation of kamaki
$ aptitude -y install python-dev

# Install kamaki, needed for Orchestrator
# In order to install an RC version, you have to explicitly specify it, as in:
#   $ pip install kamaki==0.13rc6
# Version 0.13rc6 is important for the upcoming (still unreleased on 2014-11-14)
# 0.16 version of Synnefo, so you probably need that.
$ pip install kamaki

# Prepare installation of snf-image-creator
$ apt-add-repository -y ppa:grnet/synnefo
$ aptitude update

# Install snf-image-creator
# Please answer Yes to “Create or update superadmin appliance now”
$ aptitude -y install snf-image-creator

# Sanity check
# It should normally finish with ===== TEST FINISHED OK =====
$ libguestfs-test-tool || update-guestfs-appliance

# Utilities. You can skip these.
$ aptitude -y install git
$ aptitude -y install openjdk-7-jdk
$ aptitude -y install ocaml opam
$ aptitude -y install atool htop

# ZSH goodies, again just for convenience
$ aptitude -y install zsh
$ chsh -s /bin/zsh
$ git clone --recursive https://github.com/sorin-ionescu/prezto.git "${ZDOTDIR:-$HOME}/.zprezto"
$ ln -s "${ZDOTDIR:-$HOME}"/.zprezto/runcoms/zlogin ~/.zlogin
$ ln -s "${ZDOTDIR:-$HOME}"/.zprezto/runcoms/zlogout ~/.zlogout
$ ln -s "${ZDOTDIR:-$HOME}"/.zprezto/runcoms/zpreztorc ~/.zpreztorc
$ ln -s "${ZDOTDIR:-$HOME}"/.zprezto/runcoms/zprofile ~/.zprofile
$ ln -s "${ZDOTDIR:-$HOME}"/.zprezto/runcoms/zshenv ~/.zshenv
$ ln -s "${ZDOTDIR:-$HOME}"/.zprezto/runcoms/zshrc ~/.zshrc
$ echo "alias ll='ls -al --color'" >> ~/.zshrc
$ echo "alias psg='ps -ef | grep -i'" >> ~/.zshrc
```

## Very important [as of 2014-10-15]
[README](../README.md) already contains the details for the breaking change about `kamaki`. Since no verion of `kamaki` installed via `pip` is going to work out of the box, we have to configure it manually. Our Ubuntu box already has certificates installed and we can directly feed them to `kamaki`. So consider the following as the last step in the above procedure:

```
$ kamaki config set ca_certs /etc/ssl/certs/ca-certificates.crt
```