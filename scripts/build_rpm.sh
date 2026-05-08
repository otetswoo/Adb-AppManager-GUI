#!/bin/bash
set -e

APP_NAME="adb-appmanager-gui"
VERSION="1.0.0"
RELEASE="1"

BUILD_DIR="build/rpm"
RPM_BUILD_DIR="${BUILD_DIR}/rpmbuild"
BUILDROOT="${RPM_BUILD_DIR}/BUILDROOT/${APP_NAME}-${VERSION}-${RELEASE}.x86_64"
INSTALL_DIR="${BUILDROOT}/opt/${APP_NAME}"

echo "Building ${APP_NAME} .rpm package..."

# Clean and create directories
rm -rf "${BUILD_DIR}"
mkdir -p "${RPM_BUILD_DIR}"/{BUILD,RPMS,SOURCES,SPECS,SRPMS}
mkdir -p "${INSTALL_DIR}"
mkdir -p "${BUILDROOT}/usr/bin"
mkdir -p "${BUILDROOT}/usr/share/applications"
mkdir -p "${BUILDROOT}/usr/share/icons/hicolor/256x256/apps"

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

# Copy icon file
if [ -f "src/android_manager/ui/Adb-appmanager-icon.jpg" ]; then
    cp src/android_manager/ui/Adb-appmanager-icon.jpg "${INSTALL_DIR}/"
    # Also install to system icon directory for desktop integration
    cp src/android_manager/ui/Adb-appmanager-icon.jpg "${BUILDROOT}/usr/share/icons/hicolor/256x256/apps/adb-appmanager.jpg"
fi

# Create launcher
cat > "${INSTALL_DIR}/run.sh" << 'EOF'
#!/bin/bash
cd /opt/adb-appmanager-gui
exec python3 -m android_manager.main "$@"
EOF
chmod +x "${INSTALL_DIR}/run.sh"

# Create system symlink
ln -s "/opt/${APP_NAME}/run.sh" "${BUILDROOT}/usr/bin/adb-appmanager"

# Copy desktop file
if [ -f "scripts/android-manager.desktop" ]; then
    cp scripts/android-manager.desktop "${BUILDROOT}/usr/share/applications/"
fi

# Create spec file
cat > "${RPM_BUILD_DIR}/SPECS/${APP_NAME}.spec" << EOF
Name:           ${APP_NAME}
Version:        ${VERSION}
Release:        ${RELEASE}%{?dist}
Summary:        GUI Android application manager

License:        MIT
URL:            https://github.com/otetswoo/Adb-AppManager-GUI

BuildArch:      noarch
Requires:       python3 >= 3.8
Requires:       android-tools-adb

%description
Adb AppManager GUI provides a graphical interface to manage
Android applications using ADB. Features include:
- View all installed applications
- Enable/disable applications
- Uninstall applications (including system apps)
- Install APK files
- Batch operations
- Dark/Light theme support
- RU/EN interface languages

%install
mkdir -p %{buildroot}/opt/${APP_NAME}
cp -r %{_builddir}/src/* %{buildroot}/opt/${APP_NAME}/

%post
if [ -f /opt/${APP_NAME}/requirements.txt ]; then
    pip3 install -r /opt/${APP_NAME}/requirements.txt || true
fi
if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database
fi

%files
/opt/${APP_NAME}/
/usr/bin/adb-appmanager
/usr/share/applications/android-manager.desktop

%changelog
* $(date +"%a %b %d %Y") otetswoo - ${VERSION}-${RELEASE}
- Initial package release
EOF

# Build RPM
rpmbuild -bb --define "_topdir ${RPM_BUILD_DIR}" "${RPM_BUILD_DIR}/SPECS/${APP_NAME}.spec"

# Copy result
cp "${RPM_BUILD_DIR}/RPMS/noarch/"*.rpm . 2>/dev/null || \
cp "${RPM_BUILD_DIR}/RPMS/x86_64/"*.rpm . 2>/dev/null || true

echo "✅ Package created:"
ls -lh *.rpm 2>/dev/null || echo "⚠ RPM build may have failed, check output above"
