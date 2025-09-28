# Amazon Flex Tracker — v10 (DB_FILE)

## Como rodar no Render
- **Environment**:
  - FLASK_APP=app:create_app
  - SECRET_KEY=<um valor forte>
  - (opcional) DB_FILE=flex_v2.db  ← cria um banco novo sem conflitar com flex.db

- **Build Command** (simples):
  ```bash
  pip install -r requirements.txt && flask db upgrade 0001
  ```

- **Start Command**:
  ```bash
  gunicorn -w 2 -b 0.0.0.0:10000 'app:create_app()'
  ```
