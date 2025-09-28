# Amazon Flex Tracker v11.2 (com Alembic incluso)
## Variáveis
- FLASK_APP=app:create_app
- SECRET_KEY=<um valor forte>
- (opcional) DB_FILE=flex_v11.db  → cria um novo banco sem conflitar com flex.db

## Build Command
pip install -r requirements.txt && python -m flask --app app:create_app db upgrade 0001

## Start Command
gunicorn -w 2 -b 0.0.0.0:10000 'app:create_app()'
