# Deploy no Render — Pacote v8 (single-head)

## Arquivos importantes
- `migrations/versions/0001_init_schema.py` (ÚNICO arquivo de versão!)
- `requirements.txt` (inclui gunicorn, Flask-Migrate, ReportLab, etc.)

## Passo a passo (garantido)
1) Suba este projeto para o seu repositório (GitHub). Confirme que em `migrations/versions/` existe **apenas**:
   ```
   0001_init_schema.py
   ```

2) No Render → *Settings → Build & Deploy* → **Clear build cache**.

3) **Build Command** temporário com verificação:
   ```bash
   pip install -r requirements.txt && ls -la migrations/versions && flask db upgrade 0001
   ```
   - O `ls` mostrará os arquivos de `migrations/versions` vistos pelo Render (deve listar só `0001_init_schema.py`).
   - O `upgrade 0001` evita ambiguidade com `head`.

4) **Start Command**
   ```bash
   gunicorn -w 2 -b 0.0.0.0:10000 'app:create_app()'
   ```

5) **Environment**
   - `FLASK_APP=app:create_app`
   - `SECRET_KEY=<valor forte>`

6) **Persistent Disk**
   - Monte em: `/opt/render/project/src/instance` (guarda `flex.db` e uploads).

7) Se já existir `instance/flex.db` de tentativas anteriores e você não precisa dos dados:
   - No Shell do Render: `rm -f instance/flex.db`
   - Faça **Manual Deploy**.

> Depois que subir, você pode simplificar o **Build Command** para:
> ```bash
> pip install -r requirements.txt && flask db upgrade
> ```

## Rotas úteis pós-deploy
- `/register`, `/login`
- `/calendar` (com **Converter em turno**)
- `/reports` (**Exportar CSV/PDF**)
- `/expenses` (categorias de despesas)
