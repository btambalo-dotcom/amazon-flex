<<<<<<< HEAD
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
=======
# Amazon Flex Tracker v13 (UI Pro + Auto-init DB)
Environment:
- FLASK_APP=app:create_app
- SECRET_KEY=<valor forte>
- (opcional) DB_FILE=flex_v13.db

Build Command:
pip install -r requirements.txt

Start Command:
>>>>>>> 01eee6848cb942cadd61e316da7825d7f027a623
gunicorn -w 2 -b 0.0.0.0:10000 'app:create_app()'
