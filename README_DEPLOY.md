# Amazon Flex Tracker v13 (UI Pro + Auto-init DB)
Environment:
- FLASK_APP=app:create_app
- SECRET_KEY=<valor forte>
- (opcional) DB_FILE=flex_v13.db

Build Command:
pip install -r requirements.txt

Start Command:
gunicorn -w 2 -b 0.0.0.0:10000 'app:create_app()'
