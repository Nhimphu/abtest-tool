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
- Interactive α-spending plots in the UI
- Markdown export utility
- Notebook export utility
- Basic API to run A/B analyses (`analysis_api.py`)
- Feature flag API with an in-memory store (`flags_api.py`)
- Bandit helpers: UCB1 and epsilon-greedy
- Webhook helper for early stop notifications
- Light/Dark theme toggle and sortable history table
- Simple segmentation helpers and custom metric expressions

