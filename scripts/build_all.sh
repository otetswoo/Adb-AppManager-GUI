#!/bin/bash
# Build all packages

set -e

echo "Building all packages for Android App Manager..."
echo "================================================"

# Check if running on Linux
if [[ "$(uname)" != "Linux" ]]; then
    echo "Error: This script must be run on Linux"
    exit 1
fi

# Function to check dependencies
check_deps() {
    local missing=()
    
    # Check for Python
    if ! command -v python3 &> /dev/null; then
        missing+=("python3")
    fi
    
    # Check for dpkg-deb (for .deb)
    if ! command -v dpkg-deb &> /dev/null; then
        missing+=("dpkg-deb (dpkg package)")
    fi
    
    # Check for rpmbuild (for .rpm)
    if ! command -v rpmbuild &> /dev/null; then
        missing+=("rpmbuild (rpm-build package)")
    fi
    
    if [ ${#missing[@]} -gt 0 ]; then
        echo "Missing dependencies:"
        printf '%s\n' "${missing[@]}"
        echo ""
        echo "Install them with:"
        echo "  Debian/Ubuntu: sudo apt-get install ${missing[@]}"
        echo "  Fedora/RHEL: sudo dnf install python3 rpm-build dpkg-dev"
        exit 1
    fi
}

# Check dependencies
check_deps

# Make scripts executable
chmod +x scripts/*.sh

# Build .deb package
echo ""
echo "Building .deb package..."
./scripts/build_deb.sh

# Build .rpm package
echo ""
echo "Building .rpm package..."
./scripts/build_rpm.sh

echo ""
echo "================================================"
echo "Build complete!"
echo ""
echo "Packages created:"
echo "  android-app-manager_1.0.0_all.deb"
echo "  android-app-manager-1.0.0-1.noarch.rpm"
echo ""
echo "Installation:"
echo "  Debian/Ubuntu: sudo dpkg -i android-app-manager_1.0.0_all.deb"
echo "  Fedora/RHEL:   sudo rpm -i android-app-manager-1.0.0-1.noarch.rpm"
