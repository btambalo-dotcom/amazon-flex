# Amazon Flex Tracker (Flask + SQLite)

Pequeno app web para motorista Amazon Flex registrar:
- Horas trabalhadas por dia (ou início/fim para cálculo automático)
- Valor das corridas (pagamento base + gorjetas)
- Gasto de combustível da corrida
- Hodômetro (início/fim) para calcular milhas percorridas
- Relatórios por período com totais e métricas (milhas, lucro líquido, $/hora, $/milha)

## Rodar localmente
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
export FLASK_APP=app:create_app
export FLASK_ENV=development
flask db upgrade  # cria o banco
flask run
```

Acesse: http://127.0.0.1:5000

## Deploy no Render (resumo)
1. Faça fork/suba este projeto no GitHub.
2. No Render, crie um **Web Service**.
3. Runtime: Python 3.12 (ou superior compatível).
4. Build Command: `pip install -r requirements.txt && flask db upgrade`
5. Start Command: `gunicorn -w 2 -b 0.0.0.0:10000 'app:create_app()'`
   - Se não quiser Gunicorn, pode usar `flask run --host=0.0.0.0 --port=10000` (não é ideal em produção).
6. Defina a env var `FLASK_APP=app:create_app`.
7. Banco: por padrão é SQLite (arquivo `instance/flex.db`). Para persistência no Render, habilite **Persistent Disk**.
   - Mount path sugerido: `/opt/render/project/src/instance` com 1GB+.
   - O app já usa este path por padrão para gravar o SQLite.

## Dicas
- Você pode criar **Turnos** (dia + início/fim) e **Corridas** vinculadas ao turno.
- Se preencher início/fim, o app calcula horas automaticamente; ou informe horas manualmente.
- Informe hodômetro e/ou combustível por corrida para métricas.
- A página **Relatórios** permite filtrar por data e ver totais e médias.


## Autenticação
- Acesse `/register` para criar seu login e senha (armazenados com hash).
- Depois use `/login`. As páginas do app exigem estar logado.

## Calendário (agendamentos)
- Página **Calendário**: visualização mensal/semanal/diária (FullCalendar).
- Botão **+ Agendar corrida** para criar itens com título, data/hora e pagamento esperado.
- Clique em um evento no calendário para **editar/excluir**.
- Endpoint JSON: `/api/scheduled` (usado pelo FullCalendar).

