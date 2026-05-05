# REC Recruitment Dashboard

Інтерактивний HTML-дашборд рекрутингу для команди **Recruitment Team (REC)** на основі даних з Jira.

🔗 **Live**: <https://olenapizniak.github.io/claude-reports/reports/REC_recruitment_dashboard.html>

---

## Що тут є

```
claude-reports/
├── reports/
│   └── REC_recruitment_dashboard.html    ← головний дашборд (single-file HTML + Chart.js)
├── scripts/
│   └── update_rec_dashboard.py           ← скрипт що фетчить дані з Jira і оновлює HTML
├── .github/workflows/
│   └── update-rec-dashboard.yml          ← GitHub Actions cron (оновлення кожні 30 хв)
├── .claude/
│   └── skills/rec-dashboard/SKILL.md     ← скіл для Claude Code (зашитий контекст проєкту)
└── CLAUDE.md                              ← короткі інструкції для AI про проєкт
```

---

## Дашборд має 3 таби

| Таб | Що показує |
|-----|------------|
| **Workload** | Навантаження команди — active vacancies, tasks, hires per recruiter |
| **Open Vacancies** | KPI (active/plan/in-progress/hires needed), чарти opened/hires this week, S1 (open this week), S5 (per department), Roles by Days Open, Hiring Reasons & Teams |
| **Closed Vacancies** | Vacancy Dynamics (open vs hired), Closed Vacancies by Department (month/quarter/year), Hiring Sources by department/seniority, інсайти |

---

## Як це автоматично оновлюється

```
Кожні 30 хв
  → GitHub Actions cron (.github/workflows/update-rec-dashboard.yml)
  → запускає scripts/update_rec_dashboard.py
  → скрипт фетчить дані з Jira API через JIRA_EMAIL + JIRA_API_TOKEN (GitHub Secrets)
  → замінює AUTO-маркери в HTML свіжими даними
  → git commit + push
  → GitHub Pages деплой через ~1-2 хв
  → live-сайт показує оновлені дані
```

Також є **кнопка 🔄 Оновити з Jira** прямо у дашборді — відкриває GitHub Actions де можна вручну запустити workflow.

---

## Як редагувати дашборд

### Найпростіший спосіб — Claude Code on the Web (без локального setup'у)

1. Зайди на <https://claude.ai/code> (потрібна Claude Pro/Max підписка)
2. **Connect GitHub** → авторизуй свій акаунт
3. Обери репо `OlenaPizniak/claude-reports`
4. Створи нову сесію
5. Перевір: команда `/skills` має показати **`project:rec-dashboard`** ✓
6. Просто пиши задачі природньою мовою, наприклад:

   ```
   у дашборді reports/REC_recruitment_dashboard.html у табі "Closed Vacancies"
   додай блок "Hires by Recruiter" — bar chart з кількістю найнятих по кожному рекрутеру

   використай скіл rec-dashboard
   ```

Claude автоматично:
- Завантажить скіл (бо він лежить у репо)
- Зробить запити до Jira (якщо потрібні нові дані)
- Згенерує код, відредагує HTML
- Перевірить у preview-сервері
- Закомітить і відкриє Pull Request

Ти або інший власник репо — ревʼю → мерж → live-сайт оновлений.

### Локально (для фінального контролю / великих змін)

```bash
git clone https://github.com/OlenaPizniak/claude-reports.git
cd claude-reports
claude
```

Скіл підхопиться автоматично з `.claude/skills/rec-dashboard/`.

---

## Скіл `rec-dashboard`

Файл: [.claude/skills/rec-dashboard/SKILL.md](.claude/skills/rec-dashboard/SKILL.md)

Скіл містить:
- Усі custom field IDs Jira (recruiter, sourcer, seniority, factual close date, candidate source, etc.)
- Patterns даних (формати масивів `OP`, `HW`, `CV`, `RECR`, `SRCR`, `TASKS`)
- CSS-конвенції (змінні `--blue`, `.section`, `.cv-card`, etc.)
- Логіка фільтрів (parent ↔ sub-task status, fcd ↔ hd fallback)
- Auto-update маркери (`<!--<<<AUTO_*_START>>>-->`)
- Типові помилки і як їх уникнути

Скіл оновлюється разом з дашбордом — будь-яка нова конвенція або patterns одразу записуються сюди, щоб наступні правки використовували актуальну інформацію.

---

## Доступи що потрібні

| Що | Навіщо | Як отримати |
|----|--------|-------------|
| **GitHub collaborator** до репо | щоб робити PR і пушити | запит до власника репо |
| **Atlassian-акаунт** + доступ до проекту REC | щоб скрипти оновлення працювали і Claude міг робити запити | newsiteam.atlassian.net + API token на <https://id.atlassian.com/manage-profile/security/api-tokens> |
| **Claude Pro/Max** | для роботи через claude.ai/code | <https://claude.ai/upgrade> |

---

## Технічний стек

- **Frontend**: single-file HTML + vanilla JS + Chart.js (CDN) — без билдів і фреймворків
- **Backend / data**: Python скрипт + Jira REST API
- **CI/CD**: GitHub Actions (cron + manual dispatch) + GitHub Pages
- **AI**: Claude Code + project-level skill для контексту

---

## Зв'язані репозиторії

- [okr-report](https://github.com/OlenaPizniak/okr-report) — Story Points + OKR аналітика для PLAT project (раніше було в цьому ж репо, винесено окремо)
