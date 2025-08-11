# -*- coding: utf-8 -*-
"""
Idempotent fixer:
- pyproject.toml: set python ">=3.11,<3.13"; ensure PySide6 dev dep with same marker.
- Replace pylupdate6 usage in workflows with pyside6-lupdate script call.
- Ensure scripts/update_translations.sh exists (pyside6-lupdate/lrelease).
- Remove any 'poetry lock' steps from workflows.
Run:  poetry run python scripts/safe_repo_fix.py
"""
from __future__ import annotations

import glob
import os
import pathlib
import re
import stat

def read(p): return pathlib.Path(p).read_text(encoding="utf-8")
def write(p, s):
    path = pathlib.Path(p)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(s, encoding="utf-8")

def upsert_i18n_script():
    p = "scripts/update_translations.sh"
    want = """#!/usr/bin/env bash
set -euo pipefail
mkdir -p translations
[ -f translations/app_ru.ts ] || echo '<TS version="2.1" language="ru_RU"></TS>' > translations/app_ru.ts
[ -f translations/app_en.ts ] || echo '<TS version="2.1" language="en_US"></TS>' > translations/app_en.ts
pyside6-lupdate -no-obsolete -recursive src -ts translations/app_ru.ts translations/app_en.ts -verbose
pyside6-lrelease translations/app_ru.ts translations/app_en.ts -verbose
echo "i18n updated."
"""
    if not os.path.exists(p) or "pyside6-lupdate" not in read(p):
        write(p, want)
        os.chmod(p, os.stat(p).st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

def fix_pyproject():
    p = "pyproject.toml"
    if not os.path.exists(p):
        return
    s = read(p)
    # python range
    s = re.sub(r'(?m)^(python\s*=\s*")[^"]+"', r'\1>=3.11,<3.13"', s)
    # ensure PySide6 dev dep marker (works whether group exists or not)
    if "[tool.poetry.group.dev.dependencies]" not in s:
        s += '\n[tool.poetry.group.dev.dependencies]\n'
    if "PySide6" not in s:
        s += 'PySide6 = { version = "^6.7.2", python = ">=3.11,<3.13" }\n'
    else:
        s = re.sub(r'(?m)^PySide6\s*=.*$', 'PySide6 = { version = "^6.7.2", python = ">=3.11,<3.13" }', s)
    write(p, s)

def fix_workflows():
    for wf in glob.glob(".github/workflows/*.yml"):
        s = read(wf)
        orig = s
        # remove poetry lock steps
        s = re.sub(r'(?ms)^(\s*- name:.*\n\s*run:\s*poetry\s+lock[^\n]*\n(?:\s+.*\n)*)', '', s)
        # pin python 3.12
        s = re.sub(r'python-version:\s*["\']?\d+\.\d+["\']?', 'python-version: "3.12"', s)
        # ensure install uses --with dev --sync
        s = re.sub(r'(?ms)^(\s*- name: .*install.*\n\s*run:\s*poetry\s+install[^\n]*)(.*)$',
                   lambda m: m.group(1).split('\n')[0].replace('poetry install', 'poetry install --no-interaction --with dev --sync') + '\n', s)
        # replace pylupdate6 calls with our script
        s = re.sub(r'pylupdate6[^\n]*', 'poetry run bash scripts/update_translations.sh', s)
        if s != orig:
            write(wf, s)

def main():
    upsert_i18n_script()
    fix_pyproject()
    fix_workflows()
    print("OK: scripts/update_translations.sh, pyproject.toml, workflows updated idempotently.")

if __name__ == "__main__":
    main()
