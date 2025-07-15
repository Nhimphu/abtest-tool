import json
import os
import sys
import logging

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import cli


def _setup_caplog(caplog):
    caplog.set_level(logging.INFO)


def test_run_analysis_json(tmp_path, caplog):
    _setup_caplog(caplog)
    data = {"users_a": 100, "conv_a": 10, "users_b": 120, "conv_b": 30}
    src_file = tmp_path / "data.json"
    src_file.write_text(json.dumps(data))

    cli.main(["run-analysis", "--source", str(src_file), "--output-format", "json"])
    res = json.loads(caplog.records[-1].message)
    assert "p_value_ab" in res
    assert "significant_ab" in res


def test_run_analysis_text(tmp_path, caplog):
    _setup_caplog(caplog)
    data = {"users_a": 50, "conv_a": 5, "users_b": 50, "conv_b": 8}
    src_file = tmp_path / "data.json"
    src_file.write_text(json.dumps(data))

    cli.main(["run-analysis", "--source", str(src_file), "--output-format", "text"])
    out = caplog.text
    assert "p_value_ab" in out

