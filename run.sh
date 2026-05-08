#!/bin/bash
# Запуск Android App Manager
cd "$(dirname "$0")/src"
python -m android_manager.main "$@"
