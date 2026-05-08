#!/bin/bash
set -e

APP_NAME="adb-appmanager-gui"
VERSION="1.0.0"
MAINTAINER="otetswoo"
DESCRIPTION="GUI Android application manager using ADB"

BUILD_DIR="build/deb"
DEB_DIR="${BUILD_DIR}/${APP_NAME}_${VERSION}"
INSTALL_DIR="${DEB_DIR}/opt/${APP_NAME}"
DEBIAN_DIR="${DEB_DIR}/DEBIAN"

echo "Building ${APP_NAME} .deb package..."

# Clean and create directories
rm -rf "${BUILD_DIR}"
mkdir -p "${INSTALL_DIR}" "${DEBIAN_DIR}"
mkdir -p "${DEB_DIR}/usr/bin"
mkdir -p "${DEB_DIR}/usr/share/applications"
mkdir -p "${DEB_DIR}/usr/share/icons/hicolor/256x256/apps"

# Copy source code
echo "Copying source files..."
cp -r src/* "${INSTALL_DIR}/"
cp requirements.txt "${INSTALL_DIR}/" 2>/dev/null || true
cp README.md "${INSTALL_DIR}/" 2>/dev/null || true
cp LICENSE "${INSTALL_DIR}/" 2>/dev/null || true

# Copy data files
if [ -f "data/uad_lists.json" ]; then
    mkdir -p "${INSTALL_DIR}/android_manager/data"
    cp data/uad_lists.json "${INSTALL_DIR}/android_manager/data/"
fi

# Copy icon file from icons directory
if [ -f "src/android_manager/ui/icons/icon-256.png" ]; then
    cp src/android_manager/ui/icons/icon-256.png "${INSTALL_DIR}/"
    # Also install to system icon directory for desktop integration
    cp src/android_manager/ui/icons/icon-256.png "${DEB_DIR}/usr/share/icons/hicolor/256x256/apps/adb-appmanager.png"
fi

# Create launcher
cat > "${INSTALL_DIR}/run.sh" << 'EOF'
#!/bin/bash
cd /opt/adb-appmanager-gui
exec python3 -m android_manager.main "$@"
EOF
chmod +x "${INSTALL_DIR}/run.sh"

# Create system symlink
ln -s "/opt/${APP_NAME}/run.sh" "${DEB_DIR}/usr/bin/adb-appmanager"

# Copy desktop file
if [ -f "scripts/android-manager.desktop" ]; then
    cp scripts/android-manager.desktop "${DEB_DIR}/usr/share/applications/"
fi

# Create control file
cat > "${DEBIAN_DIR}/control" << EOF
Package: ${APP_NAME}
Version: ${VERSION}
Section: admin
Priority: optional
Architecture: all
Depends: python3 (>= 3.8), python3-pip, adb
Maintainer: ${MAINTAINER}
Description: ${DESCRIPTION}
 Adb AppManager GUI provides a graphical interface to manage
 Android applications using ADB. Features include:
 .
  * View all installed applications
  * Enable/disable applications
  * Uninstall applications (including system apps)
  * Install APK files
  * Batch operations
  * Dark/Light theme support
  * RU/EN interface languages
Homepage: https://github.com/otetswoo/Adb-AppManager-GUI
EOF

# Create postinst
cat > "${DEBIAN_DIR}/postinst" << 'EOF'
#!/bin/bash
set -e
if [ -f /opt/adb-appmanager-gui/requirements.txt ]; then
    pip3 install -r /opt/adb-appmanager-gui/requirements.txt || true
fi
if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database
fi
exit 0
EOF
chmod +x "${DEBIAN_DIR}/postinst"

# Build
dpkg-deb --build "${DEB_DIR}" "${APP_NAME}_${VERSION}_all.deb"

echo "✅ Package created: ${APP_NAME}_${VERSION}_all.deb"
ls -lh *.deb
