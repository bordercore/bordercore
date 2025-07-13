#!/bin/bash
#
# build-ec2.sh — Provision and configure a web server on EC2
#
#   This script automates the setup of a web server environment on a new EC2 instance:
#     • Ensures the "www-data" system user exists
#     • Creates and chowns required web directories
#     • Enables Nginx site configurations via symlinks
#     • Removes the default Nginx site if present
#     • Adds Nginx log rotation configuration

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
    "/home/git"
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

# apt update
apt install net-tools
apt install -y certbot
apt install -y fcgiwrap
apt install -y gunicorn
apt install -y libxml2-dev
apt install -y libxslt1-dev
apt install -y nginx
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

cd /home/git
sudo -u www-data git init --bare

sudo -u www-data python3 -m venv $INSTALL_DIR/../env

cp $INSTALL_DIR/config/supervisor/gunicorn.conf /etc/supervisor/conf.d/
cp $INSTALL_DIR/config/supervisor/spawn-fcgi.conf /etc/supervisor/conf.d/
