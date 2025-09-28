# Amazon Flex Tracker v13.6 (Plug-and-Play com Auto-Migração SQLite)

## Variáveis de ambiente (Render → Settings → Environment)
- `FLASK_APP=amazon_flex:create_app` (opcional para o Gunicorn)
- `SECRET_KEY=<sua-chave-forte>`
- `DB_FILE=flex.db` (ou outro nome, ex: `flex_prod.db`)

## Disco (Render)
- Mount path: `/opt/render/project/src/instance`

## Build Command
```
pip install -r requirements.txt
```

## Start Command (sem --factory)
```
bash -lc 'mkdir -p instance && exec gunicorn -w 2 -b 0.0.0.0:10000 "amazon_flex:create_app()"'
```

### Como funciona a auto-migração
- Na inicialização, o app:
  1) chama `db.create_all()` para criar tabelas inexistentes; e
  2) verifica colunas faltantes em `users`, `shifts`, `trips`, `expenses` e adiciona com `ALTER TABLE` quando necessário.
- Dados existentes são preservados.
- A rota `/health` retorna a versão `v13.6`.
