#!/bin/bash
# Build script for .rpm package

set -e

# Configuration
APP_NAME="android-app-manager"
VERSION="1.0.0"
RELEASE="1"
MAINTAINER="Your Name <your.email@example.com>"
DESCRIPTION="GUI Android application manager using ADB"
HOMEPAGE="https://github.com/yourusername/android-app-manager"

# Directories
BUILD_DIR="build/rpm"
RPM_DIR="${BUILD_DIR}/rpmbuild"
INSTALL_DIR="${RPM_DIR}/BUILDROOT/${APP_NAME}-${VERSION}-${RELEASE}.noarch/opt/${APP_NAME}"

echo "Building ${APP_NAME} v${VERSION} .rpm package..."

# Create RPM build directories
mkdir -p "${RPM_DIR}"/{BUILD,RPMS,SOURCES,SPECS,SRPMS}
mkdir -p "${INSTALL_DIR}"
mkdir -p "${RPM_DIR}/BUILDROOT/${APP_NAME}-${VERSION}-${RELEASE}.noarch/usr/bin"
mkdir -p "${RPM_DIR}/BUILDROOT/${APP_NAME}-${VERSION}-${RELEASE}.noarch/usr/share/applications"
mkdir -p "${RPM_DIR}/BUILDROOT/${APP_NAME}-${VERSION}-${RELEASE}.noarch/usr/share/icons/hicolor/256x256/apps"
mkdir -p "${RPM_DIR}/BUILDROOT/${APP_NAME}-${VERSION}-${RELEASE}.noarch/usr/share/man/man1"

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
ln -sf "/opt/${APP_NAME}/run.sh" "${RPM_DIR}/BUILDROOT/${APP_NAME}-${VERSION}-${RELEASE}.noarch/usr/bin/android-manager"

# Copy desktop file
cp scripts/android-manager.desktop "${RPM_DIR}/BUILDROOT/${APP_NAME}-${VERSION}-${RELEASE}.noarch/usr/share/applications/"

# Create man page
cat > "${RPM_DIR}/BUILDROOT/${APP_NAME}-${VERSION}-${RELEASE}.noarch/usr/share/man/man1/android-manager.1" << 'EOF'
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

# Create spec file
cat > "${RPM_DIR}/SPECS/${APP_NAME}.spec" << EOF
Name:           ${APP_NAME}
Version:        ${VERSION}
Release:        ${RELEASE}%{?dist}
Summary:        GUI Android application manager

License:        MIT
URL:            ${HOMEPAGE}
Source0:        %{name}-%{version}.tar.gz

BuildArch:      noarch
Requires:       python3 >= 3.8
Requires:       android-tools-adb
Recommends:     python3-pip

%description
Android App Manager provides a graphical interface to manage
Android applications using ADB. Features include:
- View all installed applications
- Enable/disable applications
- Uninstall applications (including system apps)
- Install APK files
- Batch operations
- Dark/Light theme support
- Integration with Universal Android Debloater lists

%prep
# No preparation needed

%install
mkdir -p %{buildroot}/opt/${APP_NAME}
cp -r %{_sourcedir}/src/* %{buildroot}/opt/${APP_NAME}/

%post
if [ -f /opt/${APP_NAME}/requirements.txt ]; then
    pip3 install -r /opt/${APP_NAME}/requirements.txt || true
fi
if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database
fi

%preun
# Cleanup if needed

%files
/opt/${APP_NAME}/
/usr/bin/android-manager
/usr/share/applications/android-manager.desktop
/usr/share/icons/hicolor/256x256/apps/
/usr/share/man/man1/android-manager.1*

%changelog
* $(date +"%a %b %d %Y") ${MAINTAINER} - ${VERSION}-${RELEASE}
- Initial package release
EOF

# Build the package
echo "Building .rpm package..."
cd "${RPM_DIR}"
rpmbuild -bb --define "_topdir ${RPM_DIR}" SPECS/${APP_NAME}.spec

# Copy RPM to current directory
cp RPMS/noarch/*.rpm ../../

echo "Package created: ${APP_NAME}-${VERSION}-${RELEASE}.noarch.rpm"
echo "Done!"
