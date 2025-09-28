# Amazon Flex Tracker (Flask)

## Executar localmente
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
export FLASK_APP=app:create_app
flask db upgrade
flask run
```

## Render (produção)
- **Environment**:
  - `FLASK_APP=app:create_app`
  - `SECRET_KEY` (defina um valor forte)
- **Build Command**:
  `pip install -r requirements.txt && flask db upgrade`
- **Start Command**:
  `gunicorn -w 2 -b 0.0.0.0:10000 'app:create_app()'`
- **Persistent Disk** montado em `/opt/render/project/src/instance` (guarda `flex.db` e `uploads/`).

## Recursos
- Turnos, corridas, recibos (upload), hodômetro, métricas (MPG, $/mi).
- Relatórios com filtro por data e exportação CSV.
- Autenticação (registro, login, logout).
- Calendário com agendamentos.
