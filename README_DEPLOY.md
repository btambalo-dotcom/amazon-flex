# Amazon Flex Tracker v14.0 (UI Pro + Calendário)

- UI profissional com Bootstrap 5 (cards, sombras, layout limpo)
- Calendário com FullCalendar (CDN)
- Agendamento de corridas (ScheduledRide) com formulário
- Plug-and-play: auto-migração leve (adiciona colunas/tabelas faltantes), SQLite absoluto
- Rota `/health` → versão `v14.0`

## Render
**Environment**
- `SECRET_KEY=<sua-chave-forte>`
- `DB_FILE=flex.db`

**Disk**
- Mount path: `/opt/render/project/src/instance`

**Build Command**
```
pip install -r requirements.txt
```

**Start Command**
```
bash -lc 'mkdir -p instance && exec gunicorn -w 2 -b 0.0.0.0:10000 "amazon_flex:create_app()"'
```

Acesse `/calendar` para ver os agendamentos e `/scheduled/new` para criar.
