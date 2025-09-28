
# Amazon Flex Tracker v13.3 (SQLite + Render)

## Environment (Render → Settings → Environment)
- `FLASK_APP=app:create_app`
- `SECRET_KEY=<sua-chave-forte>`
- (opcional) `DB_FILE=flex.db`  → banco salvo em `instance/<DB_FILE>`

## Disk
- Mount path: `/opt/render/project/src/instance`

## Build Command
```
pip install -r requirements.txt
```

## Pre-Deploy Command
- deixe **em branco**

## Start Command (se não usar Procfile)
```
bash -lc 'mkdir -p instance && export PYTHONPATH=/opt/render/project/src FLASK_APP=app:create_app; python -m flask db upgrade -v && exec gunicorn --factory -w 2 -b 0.0.0.0:10000 app:create_app'
```

Após o deploy, teste:
- `/`  → "Amazon Flex Tracker v13.3 OK"
- `/health` → `{"ok": true, "db_file": "...", "version": "v13.3"}`
