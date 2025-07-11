GUI-приложение для расчёта sample size, A/B/n анализов, построения графиков.

![Coverage](coverage.svg)

```bash
git clone https://github.com/Nhimphu/abtest-tool.git
cd abtest-tool
python -m venv venv
venv\Scripts\Activate
pip install -r requirements.txt
python src/main.py

# Тест
pytest -q

```

OpenAPI спецификация доступна на `/spec`, интерактивная документация
Swagger‑UI отображается по адресу `/docs`.

## Plugins

Дополнительные тяжёлые функции вынесены в папку `plugins/`. Основное
приложение загружается без них, но при наличии директории `plugins`
модули подключаются автоматически с помощью `plugin_loader`. Так можно
подключить экспорт PDF/Excel, DWH‑коннекторы и расширенный Байесовский
анализ, не устанавливая лишние зависимости в базовой сборке.

## Additional Features

- CUPED adjustment and SRM check helpers (SRM warnings shown before analysis)
- Simple alpha-spending curve generation
- Interactive α-spending plots in the UI with zoom controls
- Markdown export utility
- Markdown and notebook export utilities with a common template
- Basic API to run A/B analyses (`analysis_api.py`)
- Feature flag API with an in-memory store (`flags_api.py`)
- Bandit helpers: UCB1 and epsilon-greedy
- Webhook helper for early stop notifications
- Sequential analysis functions accept a `webhook_url` parameter
- Light/Dark theme toggle and sortable history table
- Simple segmentation helpers and custom metric expressions parsed via AST for security

