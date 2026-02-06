#!/bin/bash

# RadioCalico Service Installation Script (PostgreSQL + Nginx)
# This script installs and enables the systemd services for RadioCalico

set -e

echo "Installing RadioCalico systemd services (PostgreSQL + Nginx)..."

# Check if running with sudo
if [ "$EUID" -ne 0 ]; then
    echo "Error: This script must be run with sudo"
    echo "Usage: sudo ./install-services-pg.sh"
    exit 1
fi

# Check if PostgreSQL is installed
if ! command -v psql &> /dev/null; then
    echo "Error: PostgreSQL is not installed"
    echo "Please install PostgreSQL first:"
    echo "  - Ubuntu/Debian: sudo apt install postgresql postgresql-contrib"
    echo "  - RHEL/CentOS: sudo dnf install postgresql postgresql-server"
    echo "  - Arch: sudo pacman -S postgresql"
    exit 1
fi

# Check if Nginx is installed
if ! command -v nginx &> /dev/null; then
    echo "Error: Nginx is not installed"
    echo "Please install Nginx first:"
    echo "  - Ubuntu/Debian: sudo apt install nginx"
    echo "  - RHEL/CentOS: sudo dnf install nginx"
    echo "  - Arch: sudo pacman -S nginx"
    exit 1
fi

# Check if Python venv exists
if [ ! -d "/home/roju/radiocalico/venv" ]; then
    echo "Error: Python virtual environment not found"
    echo "Please create it first:"
    echo "  python3 -m venv venv"
    echo "  source venv/bin/activate"
    echo "  pip install -r requirements.txt"
    exit 1
fi

# Prompt for PostgreSQL password
echo ""
echo "PostgreSQL Configuration"
echo "========================"
read -sp "Enter PostgreSQL password for 'radiocalico' user: " POSTGRES_PASSWORD
echo

# Create log directory if it doesn't exist
echo "Creating log directory..."
mkdir -p /var/log
touch /var/log/radiocalico-nginx.log
touch /var/log/radiocalico-nginx-error.log
touch /var/log/radiocalico-flask.log
touch /var/log/radiocalico-flask-error.log
touch /var/log/radiocalico-poller.log
touch /var/log/radiocalico-poller-error.log
chown roju:roju /var/log/radiocalico-*.log
chown nginx:nginx /var/log/radiocalico-nginx*.log 2>/dev/null || chown roju:roju /var/log/radiocalico-nginx*.log

# Setup PostgreSQL database
echo "Setting up PostgreSQL database..."
echo "Please enter your PostgreSQL superuser password when prompted"

# Create database and user if they don't exist
sudo -u postgres psql <<EOF
SELECT 'CREATE DATABASE radiocalico' WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'radiocalico')\\gexec
SELECT 'CREATE USER radiocalico WITH PASSWORD ''$POSTGRES_PASSWORD''' WHERE NOT EXISTS (SELECT FROM pg_user WHERE usename = 'radiocalico')\\gexec
GRANT ALL PRIVILEGES ON DATABASE radiocalico TO radiocalico;
EOF

# Copy and update service files with password
echo "Copying service files to /etc/systemd/system/..."
sed "s/CHANGE_ME/$POSTGRES_PASSWORD/g" radiocalico-flask-pg.service > /etc/systemd/system/radiocalico-flask-pg.service
sed "s/CHANGE_ME/$POSTGRES_PASSWORD/g" radiocalico-metadata-poller-pg.service > /etc/systemd/system/radiocalico-metadata-poller-pg.service
cp radiocalico-nginx.service /etc/systemd/system/radiocalico-nginx.service

# Setup Nginx configuration
echo "Setting up Nginx configuration..."
cp nginx.conf /etc/nginx/nginx.conf

# Allow nginx user to access static files
chown -R nginx:nginx /home/roju/radiocalico/public 2>/dev/null || true
chmod -R 755 /home/roju/radiocalico/public

# Reload systemd daemon
echo "Reloading systemd daemon..."
systemctl daemon-reload

# Enable services to start on boot
echo "Enabling services to start on boot..."
systemctl enable radiocalico-nginx.service
systemctl enable radiocalico-flask-pg.service
systemctl enable radiocalico-metadata-poller-pg.service

# Start the services
echo "Starting services..."
systemctl start radiocalico-flask-pg.service
sleep 3
systemctl start radiocalico-metadata-poller-pg.service
sleep 2
systemctl start radiocalico-nginx.service

# Check status
echo ""
echo "Service status:"
echo "==============="
systemctl status radiocalico-nginx.service --no-pager -l
echo ""
systemctl status radiocalico-flask-pg.service --no-pager -l

echo ""
echo "Installation complete!"
echo ""
echo "RadioCalico is now running at: http://localhost"
echo ""
echo "Useful commands:"
echo "  sudo systemctl status radiocalico-nginx        # Check Nginx status"
echo "  sudo systemctl status radiocalico-flask-pg     # Check Flask status"
echo "  sudo systemctl status radiocalico-metadata-poller-pg  # Check poller status"
echo "  sudo systemctl stop radiocalico-nginx          # Stop Nginx"
echo "  sudo systemctl stop radiocalico-flask-pg       # Stop Flask"
echo "  sudo systemctl restart radiocalico-nginx       # Restart Nginx"
echo "  sudo systemctl restart radiocalico-flask-pg    # Restart Flask"
echo "  sudo journalctl -u radiocalico-nginx -f        # View Nginx logs"
echo "  sudo journalctl -u radiocalico-flask-pg -f     # View Flask logs"
echo "  sudo systemctl disable radiocalico-nginx       # Disable Nginx autostart"
echo ""
echo "Database commands:"
echo "  psql -U radiocalico -d radiocalico              # Connect to database"
echo "  sudo -u postgres psql -d radiocalico            # Connect as superuser"
