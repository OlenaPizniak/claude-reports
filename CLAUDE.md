# Project: REC Recruitment Dashboard

## Контекст
Jira проєкт: **Recruitment Team** (REC)
Cloud ID: `657e24cd-f643-4482-aba5-7e848607df28`
Атлассіан хост: `https://newsiteam.atlassian.net`

## Артефакт
`reports/REC_recruitment_dashboard.html` — інтерактивний HTML-дашборд з трьома табами:
- **Workload** — навантаження команди (active vacancies, hires)
- **Open Vacancies** — відкриті вакансії, KPI, графіки
- **Closed Vacancies** — закриті вакансії, TTF/TTH, hiring sources

Live URL: <https://olenapizniak.github.io/claude-reports/reports/REC_recruitment_dashboard.html>

## Custom Fields (Jira)
| Field | ID | Опис |
|-------|----|------|
| Start date | `customfield_11223` | Дата старту вакансії |
| Recruiter | `customfield_13935` | Multi-user picker |
| Sourcer | `customfield_23510` | User picker |
| Seniority | `customfield_22876` | Multi-select (Intern/Junior/Middle/Senior/Lead/Expert) |
| Factual close date | `customfield_22878` | Коли закрилась вакансія (ручне поле) |
| First contact date | `customfield_23407` | Перший контакт з кандидатом (для TTH) |
| Hiring Manager | `customfield_23509` | Текст |
| Number of hires | `customfield_23545` | Number |
| Team and subteams | `customfield_23547` | Cascading select (Department / Sub-team) |
| Reason for opening | `customfield_22877` | Replacement / Extension / Consultation |
| Employee status | `customfield_23581` | Staff / Non-staff / Expert |
| Candidate Source | `customfield_24344` | Single select (Dou, LinkedIn Sourced, etc.) |

## Issue Types
- **Open position** (id 16298) — головна вакансія
- **Vacancy sub-task** (id 16698) — sub-task для multi-hire вакансій
- **Task** (id 3) — окремі задачі рекрутингу

## Скіл
Використовувати скіл `rec-dashboard` для створення/оновлення дашборду:
```
Use the rec-dashboard skill to [task]
```

## Auto-update
- GitHub Actions cron: `.github/workflows/update-rec-dashboard.yml` — кожні 30 хв
- Скрипт: `scripts/update_rec_dashboard.py` — фетчить дані з Jira і замінює AUTO-маркери в HTML
- Secrets: `JIRA_EMAIL`, `JIRA_API_TOKEN` (Settings → Secrets → Actions)

## Зв'язаний репозиторій
Story Points + OKR аналітика (PLAT project) знаходиться в окремому репо:
<https://github.com/OlenaPizniak/okr-report>
