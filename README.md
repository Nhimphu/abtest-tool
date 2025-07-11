GUI-приложение для расчёта sample size, A/B/n анализов, построения графиков.

```bash
git clone https://github.com/Nhimphu/abtest-tool.git
cd abtest-tool
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python src/main.py

# Запуск тестов
pytest -q
```

## Additional Features

- CUPED adjustment and SRM check helpers
- Simple alpha-spending curve generation
- Interactive α-spending plots in the UI (zoomable)
- Markdown export utility
- Notebook export utility
- Template PDF/Notebook reports
- Basic API to run A/B analyses (`analysis_api.py`)
- Use `curl -X POST -H 'Content-Type: application/json' -d '{"users_a":100, "conv_a":10, "users_b":100, "conv_b":15}' http://localhost:5000/abtest` to call the API
- Bandit helpers: UCB1 and epsilon-greedy
- Webhook helper for early stop notifications
- Algorithm switcher in the UI chooses between Thompson, UCB1 and ε-greedy
- Light/Dark theme toggle and sortable history table
- Simple segmentation helpers and custom metric expressions
- No-code feature flag editor in the UI
- CUPED correction and automatic SRM warnings
- Segmentation filters and custom metric field in the interface
- Export to Markdown and Notebook, plus PDF template
- Basic collaboration tools (undo/redo/share)
- JSON-based translations with auto language detection
- CI pipeline runs tests with coverage and pre-commit (black, flake8, bandit)

