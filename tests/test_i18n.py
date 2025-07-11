import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from i18n import i18n, detect_language


def test_i18n_loaded():
    assert 'RU' in i18n and 'EN' in i18n
    assert 'title' in i18n['EN']


def test_detect_language_returns_string():
    lang = detect_language()
    assert lang in ('RU', 'EN')
