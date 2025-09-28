# Amazon Flex Tracker v13.4 (SQLite + Render)

## Variáveis de ambiente (Render → Settings → Environment)
- `FLASK_APP=amazon_flex:create_app`
- `SECRET_KEY=<sua-chave-forte>`
- (opcional) `DB_FILE=flex.db`  → banco salvo em `instance/<DB_FILE>`

## Disco (Render)
- Mount path: `/opt/render/project/src/instance`

## Build Command
```
pip install -r requirements.txt
```

## Start Command (sem Procfile)
```
bash -lc 'mkdir -p instance && export PYTHONPATH=/opt/render/project/src && exec gunicorn --factory -w 2 -b 0.0.0.0:10000 amazon_flex:create_app'
```

## Migrações (opcional, se quiser usar Alembic)
```
# primeira vez
flask --app amazon_flex:create_app db upgrade
# se mudar os models depois
flask --app amazon_flex:create_app db migrate -m "update"
flask --app amazon_flex:create_app db upgrade
```

## Testes
- `/` redireciona para `/dashboard` se logado; senão mostra landing.
- `/health` → `{"ok": true, "db_file": "...", "version": "v13.4"}`
