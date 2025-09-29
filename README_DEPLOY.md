# Amazon Flex Tracker v14.4 (PT-BR) — Gorjetas + CRUD + PDF + Líquido + Tema Escuro

## Novidades
- Campo e somatório de **gorjetas** (UI, API e relatórios)
- **Editar/Excluir** agendamentos
- **Exportar PDF** dos relatórios (`/relatorios/pdf?inicio=YYYY-MM-DD&fim=YYYY-MM-DD`)
- **Total Líquido** = Valor + Gorjetas − Combustível − Despesas
- **Tema Escuro** (toggle salvo em localStorage)
- Auto-migração SQLite e usuário admin via `ADMIN_EMAIL`/`ADMIN_PASSWORD`

## Deploy (Render)
- Build: `pip install -r requirements.txt`
- Start: `gunicorn -w 2 -b 0.0.0.0:$PORT 'amazon_flex:create_app()'`
- Disco: `/opt/render/project/src/instance`
- ENV: `SECRET_KEY`, `DB_FILE`, `ADMIN_EMAIL`, `ADMIN_PASSWORD`

## Uso
- Entrar: `/entrar` (use o admin seedado)
- Calendário: `/calendario`
- Novo/Editar/Excluir: botões na tela e rotas `/agendamento/...`
- Relatórios: `/relatorios` → informe início/fim → **Exportar PDF**
