# Amazon Flex Tracker — v12 (com DB_FILE e migração 0001)

## Variáveis de ambiente (Render → Environment)
- `FLASK_APP=app:create_app`
- `SECRET_KEY=<um valor forte>`
- (opcional) `DB_FILE=flex_v12.db`  ← cria/usa um novo banco sem conflitar com `flex.db`

## Build Command (recomendado)
```bash
pip install -r requirements.txt && flask db upgrade 0001
```

## Start Command
```bash
gunicorn -w 2 -b 0.0.0.0:10000 'app:create_app()'
```

## Estrutura
- `app.py` → factory + modelos + rotas básicas
- `migrations/versions/0001_init_schema.py` → cria `users`, `shifts`, `trips`, `expenses`, `scheduled_rides`
- `templates/` → telas simples (login/registro/dashboard/despesas/relatórios/calendário)

## Após deploy
- Acesse `/register` para criar o primeiro usuário, depois faça login em `/login`.
- Cadastre turnos (/shift/new), corridas (/trip/new), despesas (/expenses/new), agende corridas no calendário (/calendar).
- Gere relatório em `/reports` (HTML, CSV e PDF).
