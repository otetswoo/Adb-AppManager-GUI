#!/bin/bash
# Build script for .deb package

set -e

# Configuration
APP_NAME="android-app-manager"
VERSION="1.0.0"
MAINTAINER="Your Name <your.email@example.com>"
DESCRIPTION="GUI Android application manager using ADB"
HOMEPAGE="https://github.com/yourusername/android-app-manager"

# Directories
BUILD_DIR="build/deb"
DEB_DIR="${BUILD_DIR}/${APP_NAME}_${VERSION}"
INSTALL_DIR="${DEB_DIR}/opt/${APP_NAME}"
DEBIAN_DIR="${DEB_DIR}/DEBIAN"
APPLICATIONS_DIR="${DEB_DIR}/usr/share/applications"
ICONS_DIR="${DEB_DIR}/usr/share/icons/hicolor/256x256/apps"
MAN_DIR="${DEB_DIR}/usr/share/man/man1"

echo "Building ${APP_NAME} v${VERSION} .deb package..."

# Clean build directory
rm -rf "${BUILD_DIR}"
mkdir -p "${INSTALL_DIR}" "${DEBIAN_DIR}" "${APPLICATIONS_DIR}" "${ICONS_DIR}" "${MAN_DIR}"

# Copy application files
echo "Copying application files..."
cp -r src/* "${INSTALL_DIR}/"
cp requirements.txt "${INSTALL_DIR}/"
cp README.md "${INSTALL_DIR}/"
cp LICENSE "${INSTALL_DIR}/"

# Copy data files
if [ -f "data/uad_lists.json" ]; then
    mkdir -p "${INSTALL_DIR}/android_manager/data"
    cp data/uad_lists.json "${INSTALL_DIR}/android_manager/data/"
fi

# Create launcher script
cat > "${INSTALL_DIR}/run.sh" << 'EOF'
#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${SCRIPT_DIR}"
exec python3 -m android_manager.main "$@"
EOF
chmod +x "${INSTALL_DIR}/run.sh"

# Create symlink
mkdir -p "${DEB_DIR}/usr/bin"
ln -sf "/opt/${APP_NAME}/run.sh" "${DEB_DIR}/usr/bin/android-manager"

# Copy desktop file
cp scripts/android-manager.desktop "${APPLICATIONS_DIR}/"

# Create man page
cat > "${MAN_DIR}/android-manager.1" << 'EOF'
.TH ANDROID-MANAGER 1 "2024-01-01" "1.0.0" "Android App Manager"
.SH NAME
android-manager \- GUI Android application manager
.SH SYNOPSIS
.B android-manager
.SH DESCRIPTION
Android App Manager is a GUI application for managing Android
applications via ADB (Android Debug Bridge).
.SH OPTIONS
No command-line options are supported.
.SH SEE ALSO
.BR adb (1)
EOF

# Create DEBIAN/control
cat > "${DEBIAN_DIR}/control" << EOF
Package: ${APP_NAME}
Version: ${VERSION}
Section: admin
Priority: optional
Architecture: all
Depends: python3 (>= 3.8), python3-pip, adb
Recommends: android-sdk-platform-tools
Maintainer: ${MAINTAINER}
Description: ${DESCRIPTION}
 Android App Manager provides a graphical interface to manage
 Android applications using ADB. Features include:
 .
  * View all installed applications
  * Enable/disable applications
  * Uninstall applications (including system apps)
  * Install APK files
  * Batch operations
  * Dark/Light theme support
  * Integration with Universal Android Debloater lists
Homepage: ${HOMEPAGE}
EOF

# Create postinst script
cat > "${DEBIAN_DIR}/postinst" << 'EOF'
#!/bin/bash
set -e

# Install Python dependencies
if [ -f /opt/android-app-manager/requirements.txt ]; then
    pip3 install -r /opt/android-app-manager/requirements.txt || true
fi

# Update desktop database
if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database
fi

exit 0
EOF
chmod +x "${DEBIAN_DIR}/postinst"

# Create prerm script
cat > "${DEBIAN_DIR}/prerm" << 'EOF'
#!/bin/bash
set -e
exit 0
EOF
chmod +x "${DEBIAN_DIR}/prerm"

# Build the package
echo "Building .deb package..."
dpkg-deb --build "${DEB_DIR}" "${APP_NAME}_${VERSION}_all.deb"

echo "Package created: ${APP_NAME}_${VERSION}_all.deb"
echo "Done!"
