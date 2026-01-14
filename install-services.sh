#!/bin/bash

# RadioCalico Service Installation Script
# This script installs and enables the systemd services for RadioCalico

set -e

echo "Installing RadioCalico systemd services..."

# Check if running with sudo
if [ "$EUID" -ne 0 ]; then
    echo "Error: This script must be run with sudo"
    echo "Usage: sudo ./install-services.sh"
    exit 1
fi

# Create log directory if it doesn't exist
echo "Creating log directory..."
mkdir -p /var/log
touch /var/log/radiocalico-express.log
touch /var/log/radiocalico-express-error.log
touch /var/log/radiocalico-flask.log
touch /var/log/radiocalico-flask-error.log
chown roju:roju /var/log/radiocalico-*.log

# Copy service files to systemd directory
echo "Copying service files to /etc/systemd/system/..."
cp radiocalico-express.service /etc/systemd/system/
cp radiocalico-flask.service /etc/systemd/system/

# Reload systemd daemon
echo "Reloading systemd daemon..."
systemctl daemon-reload

# Enable services to start on boot
echo "Enabling services to start on boot..."
systemctl enable radiocalico-express.service
systemctl enable radiocalico-flask.service

# Start the services
echo "Starting services..."
systemctl start radiocalico-express.service
systemctl start radiocalico-flask.service

# Check status
echo ""
echo "Service status:"
echo "==============="
systemctl status radiocalico-express.service --no-pager -l
echo ""
systemctl status radiocalico-flask.service --no-pager -l

echo ""
echo "Installation complete!"
echo ""
echo "Useful commands:"
echo "  sudo systemctl status radiocalico-express    # Check Express server status"
echo "  sudo systemctl status radiocalico-flask      # Check Flask server status"
echo "  sudo systemctl stop radiocalico-express      # Stop Express server"
echo "  sudo systemctl stop radiocalico-flask        # Stop Flask server"
echo "  sudo systemctl restart radiocalico-express   # Restart Express server"
echo "  sudo systemctl restart radiocalico-flask     # Restart Flask server"
echo "  sudo journalctl -u radiocalico-express -f    # View Express logs"
echo "  sudo journalctl -u radiocalico-flask -f      # View Flask logs"
echo "  sudo systemctl disable radiocalico-express   # Disable Express autostart"
echo "  sudo systemctl disable radiocalico-flask     # Disable Flask autostart"
