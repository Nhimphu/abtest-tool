#!/usr/bin/env bash
set -euo pipefail
mkdir -p translations
[ -f translations/app_ru.ts ] || echo '<TS version="2.1" language="ru_RU"></TS>' > translations/app_ru.ts
[ -f translations/app_en.ts ] || echo '<TS version="2.1" language="en_US"></TS>' > translations/app_en.ts
pyside6-lupdate -no-obsolete -recursive src -ts translations/app_ru.ts translations/app_en.ts -verbose
pyside6-lrelease translations/app_ru.ts translations/app_en.ts -verbose
echo "i18n updated."
