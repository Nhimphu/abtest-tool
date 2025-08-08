#!/usr/bin/env bash
set -euo pipefail
mkdir -p translations
# создаём ts, если нет
[ -f translations/app_ru.ts ] || echo '<TS version="2.1" language="ru_RU"></TS>' > translations/app_ru.ts
[ -f translations/app_en.ts ] || echo '<TS version="2.1" language="en_US"></TS>' > translations/app_en.ts
# рекурсивно собираем строки из всех .py под src/
pyside6-lupdate -no-obsolete -recursive src \
  -ts translations/app_ru.ts translations/app_en.ts -verbose
# компилим в .qm
pyside6-lrelease translations/app_ru.ts translations/app_en.ts -verbose
