import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import cli


def test_run_analysis_json(tmp_path, capsys):
    data = {"users_a": 100, "conv_a": 10, "users_b": 120, "conv_b": 30}
    src_file = tmp_path / "data.json"
    src_file.write_text(json.dumps(data))

    cli.main(["run-analysis", "--source", str(src_file), "--output-format", "json"])
    out = capsys.readouterr().out.strip()
    res = json.loads(out)
    assert "p_value_ab" in res
    assert "significant_ab" in res


def test_run_analysis_text(tmp_path, capsys):
    data = {"users_a": 50, "conv_a": 5, "users_b": 50, "conv_b": 8}
    src_file = tmp_path / "data.json"
    src_file.write_text(json.dumps(data))

    cli.main(["run-analysis", "--source", str(src_file), "--output-format", "text"])
    out = capsys.readouterr().out
    assert "p_value_ab" in out

