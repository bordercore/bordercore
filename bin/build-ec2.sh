#!/bin/bash
#
# build-ec2.sh — Provision and configure a web server on a new EC2 instance
#
# This script automates the setup of a Django/Nginx web server environment:
#   • Ensures the "www-data" system user exists and adds "ubuntu" to its group
#   • Creates and chowns key directories for logs and the Git bare repo
#   • Installs necessary packages including Nginx, Certbot, Supervisor, and Python tools
#   • Clones/pulls the application from GitHub into the www-data-owned directory
#   • Initializes and configures a bare Git repository for remote pushing
#   • Sets up post-receive Git hook to deploy code on push
#   • Configures Nginx by copying site configs and enabling them via symlinks
#   • Removes default Nginx site and sets up log rotation
#   • Copies Supervisor configs for Gunicorn and fcgiwrap
#   • Creates a Python virtual environment for the app
#
# Run this script with sudo on a fresh EC2 instance.

if [ "$EUID" -ne 0 ]; then
  echo "Please run via sudo." >&2
  exit 1
fi

INSTALL_DIR=/var/www/django/bordercore

# Check if user "www-data" exists
if id "www-data" &>/dev/null; then
    echo "User 'www-data' already exists."
else
    echo "User 'www-data' does not exist. Creating..."
    # Create the user with no login shell and no home directory
    useradd --system --no-create-home --shell /usr/sbin/nologin www-data
    echo "User 'www-data' created."
fi

# Add the user "ubuntu" to the "www-data" group
adduser ubuntu www-data

# List of directories to check/create
DIRECTORIES=(
    "/var/log/django"
    "/home/git/bordercore.git"
)

# Loop through each directory
for DIR in "${DIRECTORIES[@]}"; do
    if [ -d "$DIR" ]; then
        echo "Directory '$DIR' already exists."
    else
        echo "Creating directory '$DIR'..."
        mkdir -p "$DIR"
        echo "Directory '$DIR' created."
    fi
    chown www-data:www-data "$DIR"
    echo "Set ownership of '$DIR' to 'www-data'."
done

cp -pr $INSTALL_DIR/bordercore/static/html/* /var/www/html/
chown -R www-data:www-data /var/www/html/*

# apt update
apt install -y apache2-utils
apt install -y net-tools
apt install -y certbot
apt install -y fcgiwrap
apt install -y gunicorn
apt install -y libxml2-dev
apt install -y libxslt1-dev
apt install -y nginx
apt install -y python3-certbot-nginx
apt install -y python3-pip
apt install -y python3.12-venv
apt install -y spawn-fcgi
apt install -y supervisor

cd $INSTALL_DIR
sudo -u www-data git init
sudo -u www-data git pull https://github.com/bordercore/bordercore

# NGinx configuration
cp $INSTALL_DIR/config/nginx/nginx.conf /etc/nginx/
cp $INSTALL_DIR/config/nginx/bordercore.com /etc/nginx/conf.d/sites-available

DEFAULT_LINK="/etc/nginx/sites-enabled/default"
if [ -L "$DEFAULT_LINK" ]; then
  echo "Removing default nginx symlink: $DEFAULT_LINK"
  rm "$DEFAULT_LINK"
else
  echo "$DEFAULT_LINK not a symlink (or doesn’t exist), skipping."
fi

# Create nginx symlink if it doesn't exist
SYMLINK="/etc/nginx/sites-enabled/bordercore.com"
TARGET="/etc/nginx/sites-available/bordercore.com"

if [ -L "$SYMLINK" ]; then
    echo "Symlink '$SYMLINK' already exists."
else
    echo "Creating symlink '$SYMLINK' -> '$TARGET'..."
    ln -s "$TARGET" "$SYMLINK"
    echo "Symlink created."
fi

cp $INSTALL_DIR/config/nginx/logrotate.d/nginx /etc/logrotate.d/

cd /home/git/bordercore.git
sudo -u www-data git init --bare
sudo -u www-data git config http.receivepack true
cd $INSTALL_DIR
sudo -u www-data git remote add origin /home/git/bordercore.git
sudo -u www-data git push

GIT_HOOK_DIR=/home/git/bordercore.git/hooks
cp $INSTALL_DIR/config/git/post-receive "$GIT_HOOK_DIR"
chown www-data:www-data "$GIT_HOOK_DIR/post-receive"

sudo -u www-data python3 -m venv $INSTALL_DIR/../env

cp $INSTALL_DIR/config/supervisor/gunicorn.conf /etc/supervisor/conf.d/
cp $INSTALL_DIR/config/supervisor/spawn-fcgi.conf /etc/supervisor/conf.d/
