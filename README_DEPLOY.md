# Amazon Flex Tracker v12 FULL (login, agenda, despesas, relatório + Alembic)

## Environment (Render)
- FLASK_APP=app:create_app
- SECRET_KEY=<um valor forte>
- (opcional) DB_FILE=flex_v12.db
- (ou) SQLALCHEMY_DATABASE_URI=sqlite:///instance/flex_v12.db

## Build Command
pip install -r requirements.txt && python -m flask --app app:create_app db upgrade 0001

## Start Command
gunicorn -w 2 -b 0.0.0.0:10000 'app:create_app()'

## Rotas
/ (landing) → /dashboard quando logado
/register, /login, /logout
/shifts/new, /trips/new
/expenses, /expenses/new
/calendar, /calendar/new
/reports/pdf?start=YYYY-MM-DD&end=YYYY-MM-DD
/health (checagem)
