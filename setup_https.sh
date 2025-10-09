#!/bin/bash
# Project Phoenix - HTTPS Setup Script
# This script sets up self-signed SSL certificates and hostname configuration

set -e

echo "========================================"
echo "Project Phoenix - HTTPS Setup"
echo "========================================"
echo ""

# Get device hostname
HOSTNAME=$(hostname)
echo "Your device hostname: $HOSTNAME"
echo ""

# Check if OpenSSL is installed
if ! command -v openssl &> /dev/null; then
    echo "ERROR: OpenSSL is not installed"
    echo "Install it with: pkg install openssl"
    exit 1
fi

echo "Generating self-signed SSL certificate..."
echo ""

# Generate certificate with both hostname and localhost
openssl req -x509 -newkey rsa:2048 -nodes \
    -keyout key.pem \
    -out cert.pem \
    -days 365 \
    -subj "/C=US/ST=State/L=City/O=ProjectPhoenix/CN=$HOSTNAME" \
    -addext "subjectAltName=DNS:$HOSTNAME,DNS:localhost,DNS:*.local,IP:127.0.0.1"

if [ $? -eq 0 ]; then
    echo ""
    echo "✓ SSL certificates generated successfully!"
    echo "  - cert.pem (certificate)"
    echo "  - key.pem (private key)"
    echo ""
else
    echo ""
    echo "✗ Failed to generate certificates"
    exit 1
fi

# Get local IP
echo "Finding your local IP address..."
LOCAL_IP=$(ip addr show wlan0 2>/dev/null | grep "inet " | awk '{print $2}' | cut -d/ -f1)

if [ -z "$LOCAL_IP" ]; then
    LOCAL_IP=$(ifconfig wlan0 2>/dev/null | grep "inet " | awk '{print $2}')
fi

echo ""
echo "========================================"
echo "Setup Complete!"
echo "========================================"
echo ""
echo "HTTPS is now enabled!"
echo ""
echo "Your device hostname: $HOSTNAME"
if [ -n "$LOCAL_IP" ]; then
    echo "Your local IP: $LOCAL_IP"
fi
echo ""
echo "In your Project Phoenix app Settings:"
echo "  Server URL: https://$HOSTNAME:5000"
echo ""
echo "OR using IP address:"
if [ -n "$LOCAL_IP" ]; then
    echo "  Server URL: https://$LOCAL_IP:5000"
fi
echo ""
echo "Note: You will need to accept the self-signed"
echo "      certificate warning in your browser/app."
echo ""
echo "Start the backend with: python backend.py"
echo "========================================"
