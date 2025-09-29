
# Flex Tracker v14.4 — CSV/Excel/PDF + Calendário + CRUD (PT-BR)

## Novidades
- Exportar relatório em **CSV** e **Excel (XLSX)** além de **PDF**.
- Botões na tela **/relatorios**.

## Deploy Render
Env:
- `SECRET_KEY=<sua-chave>`
- `DB_FILE=flex.db`

Disco:
- Montar em `/opt/render/project/src/instance`

Build:
`pip install -r requirements.txt`

Start:
`bash -lc 'mkdir -p instance && exec gunicorn -w 2 -b 0.0.0.0:10000 "amazon_flex:create_app()"'`
