
# Amazon Flex Tracker v13.2

## Render (config recomendado)
Environment:
- FLASK_APP=app:create_app
- SECRET_KEY=<sua-chave-forte>
- (opcional) DB_FILE=flex_v13.db

Disk:
- Mount path: /opt/render/project/src/instance

Build Command:
    pip install -r requirements.txt

Pre-Deploy Command:
    (deixe vazio)

Start Command (se não usar Procfile):
    bash -lc 'mkdir -p instance && export PYTHONPATH=/opt/render/project/src FLASK_APP=app:create_app; python -m flask db upgrade -v && exec gunicorn --factory -w 2 -b 0.0.0.0:10000 app:create_app'

Após deploy: acesse /health para ver {"ok": true}.
