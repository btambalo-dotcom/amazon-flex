
# Amazon Flex — Gestão de Corridas (Flask)

App em Flask (Python) para cadastrar **estações da Amazon**, lançar **corridas** com cálculo automático de **horas trabalhadas**, e gerar **relatórios** com **% de margem de lucro**. Inclui opção para **excluir corridas antigas** a partir de uma data escolhida.

Compatível para **GitHub** e **Render** (deploy com `gunicorn`).

## Recursos
- ⚙️ Cadastro/edição/remoção de **Estações**
- 🚗 Corridas com **data/hora inicial e final** (calcula horas automaticamente)
- ⛽ Campos de **milhagem**, **custo** (combustível/manutenção/outros), **receita** e **gorjetas**
- 📈 **Relatório por período** com:
  - Totais (receita, gorjetas, custo, lucro)
  - **Margem de lucro (%)**
  - Filtro por **Estação**
  - Botão para **excluir corridas mais antigas** que uma data
- 🧱 Persistência em **SQLite** (arquivo), apontado por variável `DATABASE_URL`. Em produção (Render), use **Disco Persistente**.
- 🌐 Templates simples com **Bootstrap** (em português)

## Requisitos
- Python 3.10+
- `pip install -r requirements.txt`

## Como rodar local
```bash
cp .env.example .env  # ajuste se quiser
pip install -r requirements.txt
flask --app app run  # http://127.0.0.1:5000
```

## Banco de dados
- Por padrão, usa `sqlite:///instance/app.db` (arquivo local).
- Você pode definir `DATABASE_URL` (ex.: `sqlite:////data/app.db` em produção).

Na **primeira execução**, as tabelas são criadas automaticamente se não existirem.

## Deploy no Render (passo a passo)
1. Faça **fork** ou suba este repo no **GitHub**.
2. No Render, crie um **Web Service** apontando para este repositório.
3. **Runtime:** Python 3.10+
4. **Build Command:** `pip install -r requirements.txt`
5. **Start Command:** `gunicorn app:app`
6. **Environment**:
   - `PYTHON_VERSION` = `3.10.12` (ou superior)
   - `PORT` será injetada pelo Render automaticamente
   - **(Recomendado)** `DATABASE_URL` = `sqlite:////data/app.db`
7. **Disco Persistente**:
   - Adicione um **Persistent Disk** (por exemplo, 1GB) montado em `/data`
   - Assim os dados não serão perdidos nos deploys
8. Opcional: ajuste `render.yaml` para infra como código (já incluído).

## Estrutura
```
amazon-flex-app-v4/
├─ app.py
├─ models.py
├─ forms.py
├─ utils.py
├─ requirements.txt
├─ Procfile
├─ render.yaml
├─ .env.example
├─ instance/            # para SQLite local
├─ templates/
│  ├─ base.html
│  ├─ index.html
│  ├─ stations.html
│  ├─ station_form.html
│  ├─ runs.html
│  ├─ run_form.html
│  └─ reports.html
└─ static/
   └─ custom.css
```

## Notas
- **Margem de lucro (%)** = `(Lucro / Receita Bruta) * 100`, onde `Lucro = Receita + Gorjetas - Custo`.
- O botão **"Excluir corridas mais antigas"** remove corridas **com data de início anterior** à data que você escolher (atenção, é irreversível).
- Todos os textos estão em **Português** (Brasil).
