# Amazon Flex Tracker v13.5 (Plug-and-Play, sem Alembic)

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

## Start Command
```
bash -lc 'mkdir -p instance && exec gunicorn --factory -w 2 -b 0.0.0.0:10000 amazon_flex:create_app'
```

> Na primeira execução o app cria automaticamente o schema do banco (`db.create_all()`).
> Rota de saúde: `/health` → `{"ok": true, "db_file": "...", "version": "v13.5"}`
