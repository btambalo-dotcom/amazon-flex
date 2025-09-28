# Flex v14 (Admin cria usuários)
ENV:
- FLASK_APP=app:create_app
- SECRET_KEY=<forte>
- (opcional) DB_FILE=flex_v14.db
- (opcional) ADMIN_USER=admin
- (opcional) ADMIN_PASS=admin123

Build:
pip install -r requirements.txt

Start:
gunicorn -w 2 -b 0.0.0.0:10000 'app:create_app()'
