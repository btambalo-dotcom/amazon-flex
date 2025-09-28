# Deploy no Render — Pacote v9 (single-head + build condicional)

## Use este Build Command (padrão recomendado)
Detecta se o banco já existe e escolhe automaticamente `stamp` ou `upgrade`:
```bash
pip install -r requirements.txt && if [ -f instance/flex.db ]; then flask db stamp 0001; else flask db upgrade 0001; fi
```

> Se preferir, depois que o serviço já estiver estável, você pode voltar para:
> ```bash
> pip install -r requirements.txt && flask db upgrade
> ```

## Start Command
```bash
gunicorn -w 2 -b 0.0.0.0:10000 'app:create_app()'
```

## Environment
- `FLASK_APP=app:create_app`
- `SECRET_KEY=<valor forte>`

## Persistent Disk
- Monte em: `/opt/render/project/src/instance` (guarda `flex.db` e `uploads/`).

## Estrutura de migrações (garantida)
```
migrations/
  env.py
  README
  script.py.mako
  versions/
    0001_init_schema.py   # ÚNICA revisão
```

## Pós-deploy
- `/register` → crie usuário
- `/login`
- `/calendar` (Converter em turno)
- `/reports` (Exportar CSV/PDF)
- `/expenses` (categorias de despesas)
