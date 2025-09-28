# Amazon Flex Tracker

## Deploy no Render
1. Configure variáveis de ambiente:
   - `FLASK_APP=app:create_app`
   - `SECRET_KEY=sua_chave_segura`
   - `DB_FILE=flex_v13.db`

2. Build Command:
   ```bash
   pip install -r requirements.txt && flask db upgrade 0001
   ```

3. Start Command:
   ```bash
   gunicorn -w 2 -b 0.0.0.0:10000 'app:create_app()'
   ```
