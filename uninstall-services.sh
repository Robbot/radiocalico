#!/bin/bash

# RadioCalico Service Uninstallation Script
# This script stops, disables, and removes the systemd services for RadioCalico

set -e

echo "Uninstalling RadioCalico systemd services..."

# Check if running with sudo
if [ "$EUID" -ne 0 ]; then
    echo "Error: This script must be run with sudo"
    echo "Usage: sudo ./uninstall-services.sh"
    exit 1
fi

# Stop the services
echo "Stopping services..."
systemctl stop radiocalico-express.service || true
systemctl stop radiocalico-flask.service || true

# Disable services
echo "Disabling services..."
systemctl disable radiocalico-express.service || true
systemctl disable radiocalico-flask.service || true

# Remove service files
echo "Removing service files..."
rm -f /etc/systemd/system/radiocalico-express.service
rm -f /etc/systemd/system/radiocalico-flask.service

# Reload systemd daemon
echo "Reloading systemd daemon..."
systemctl daemon-reload

echo ""
echo "Uninstallation complete!"
echo ""
echo "Note: Log files in /var/log/radiocalico-*.log have been preserved."
echo "To remove them, run: sudo rm /var/log/radiocalico-*.log"
