import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import pytest
from flags import FeatureFlagStore


def test_create_and_update_flag():
    store = FeatureFlagStore()
    flag = store.create_flag('new', enabled=True, rollout=50)
    assert flag.name == 'new'
    assert flag.enabled is True
    assert flag.rollout == 50

    updated = store.update_flag('new', enabled=False, rollout=20)
    assert updated.enabled is False
    assert updated.rollout == 20
    assert store.get_flag('new').enabled is False


def test_create_duplicate_flag():
    store = FeatureFlagStore()
    store.create_flag('foo')
    with pytest.raises(ValueError):
        store.create_flag('foo')


def test_update_invalid_rollout():
    store = FeatureFlagStore()
    store.create_flag('bar')
    with pytest.raises(ValueError):
        store.update_flag('bar', rollout=120)
