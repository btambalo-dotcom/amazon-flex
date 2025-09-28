# Amazon Flex Tracker v11 (com login, agenda, despesas, relatório e migrações)

## Variáveis (Render → Environment)
- FLASK_APP=app:create_app
- SECRET_KEY=<um valor forte>
- (opcional) DB_FILE=flex_v11.db   ← cria banco novo sem conflitar com flex.db
- (opcional) SQLALCHEMY_DATABASE_URI=sqlite:///instance/flex_v11.db   ← se quiser travar a URI

## Build Command
pip install -r requirements.txt && python -m flask --app app:create_app db upgrade 0001

## Start Command
gunicorn -w 2 -b 0.0.0.0:10000 'app:create_app()'

## Rotas principais
- /            → landing (ou redireciona para /dashboard quando logado)
- /register    → criar conta (email + senha)
- /login       → login
- /dashboard   → visão geral
- /shifts/new  → cadastrar turno
- /trips/new   → cadastrar corrida (vincula a um turno)
- /expenses    → lista despesas
- /expenses/new→ nova despesa
- /calendar    → agenda de corridas
- /calendar/new→ novo agendamento
- /reports/pdf?start=YYYY-MM-DD&end=YYYY-MM-DD  → PDF por período
