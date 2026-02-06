#!/bin/bash

# RadioCalico Service Uninstallation Script (PostgreSQL + Nginx)
# This script stops, disables, and removes the systemd services for RadioCalico

set -e

echo "Uninstalling RadioCalico systemd services (PostgreSQL + Nginx)..."

# Check if running with sudo
if [ "$EUID" -ne 0 ]; then
    echo "Error: This script must be run with sudo"
    echo "Usage: sudo ./uninstall-services-pg.sh"
    exit 1
fi

# Stop services
echo "Stopping services..."
systemctl stop radiocalico-metadata-poller-pg.service 2>/dev/null || true
systemctl stop radiocalico-flask-pg.service 2>/dev/null || true
systemctl stop radiocalico-nginx.service 2>/dev/null || true

# Disable services
echo "Disabling services..."
systemctl disable radiocalico-metadata-poller-pg.service 2>/dev/null || true
systemctl disable radiocalico-flask-pg.service 2>/dev/null || true
systemctl disable radiocalico-nginx.service 2>/dev/null || true

# Remove service files
echo "Removing service files from /etc/systemd/system/..."
rm -f /etc/systemd/system/radiocalico-metadata-poller-pg.service
rm -f /etc/systemd/system/radiocalico-flask-pg.service
rm -f /etc/systemd/system/radiocalico-nginx.service

# Reload systemd daemon
echo "Reloading systemd daemon..."
systemctl daemon-reload
systemctl reset-failed

# Ask about database removal
echo ""
read -p "Do you want to remove the PostgreSQL database and user? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Removing PostgreSQL database and user..."
    sudo -u postgres psql <<EOF
DROP DATABASE IF EXISTS radiocalico;
DROP USER IF EXISTS radiocalico;
EOF
    echo "Database removed."
else
    echo "Database kept intact."
fi

echo ""
echo "Uninstallation complete!"
echo ""
echo "Note: Log files have been kept at /var/log/radiocalico-*.log"
echo "To remove them, run: sudo rm /var/log/radiocalico-*.log"
