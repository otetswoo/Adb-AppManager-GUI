# Android App Manager

GUI приложение для управления Android-приложениями через ADB.

🇬🇧 Forked from [mehran-mousavi/Adb-AppManager-GUI](https://github.com/mehran-mousavi/Adb-AppManager-GUI)

🇷🇺 Форк проекта [mehran-mousavi/Adb-AppManager-GUI](https://github.com/mehran-mousavi/Adb-AppManager-GUI)

## Возможности

- 📱 Просмотр всех установленных приложений
- 🔍 Поиск и фильтрация приложений
- ⚡ Включение/отключение приложений
- 🗑️ Удаление приложений (включая системные)
- 📦 Установка APK-файлов
- 📦 Экспорт APK-файлов с подключенного устройства
- 📋 Пакетное отключение приложений
- 🌓 Тёмная/светлая тема
- 🌍 Поддержка русского и английского языков
- 📊 Интеграция с Universal Android Debloater списками

## Установка

### Зависимости
- Python 3.8+
- ADB (Android Debug Bridge)
- PyQt5

### Из исходников
```bash
git clone https://github.com/otetswoo/Adb-AppManager-GUI
cd android-app-manager
pip install -r requirements.txt
python src/android_manager/main.py
```
![Preview](preview_v2.png)

Android App Manager is a Python-based GUI application that allows users to manage their Android applications via ADB (Android Debug Bridge).

## Features

- 📱 View all installed apps
- 🔍 Search and filter apps
- ⚡ Enable/disable apps
- 🗑️ Remove apps (including system apps)
- 📦 Install APK files
- 📦 Export APK files from a connected device
- 📋 Batch disable apps
- 🌓 Dark/light theme
- 🌍 Support for Russian and English
- 📊 Integration with Universal Android Debloater lists


## Requirements

- Python 3.8+
- ADB (Android Debug Bridge)
- PyQt5

## Usage

1. Connect your Android device to your computer.
2. Enable USB debugging on your Android device.
3. Run the script.

The application will start and display a GUI to manage your Android applications.

## Note

This tool uses ADB commands to manage applications. Please ensure you understand the implications of disabling/enabling applications on your Android device. Always use this tool responsibly.

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## License

[MIT](https://choosealicense.com/licenses/mit/)

## Disclaimer

This tool is for educational purposes only. The developer is not responsible for any misuse of this tool.
