---
name: REC Recruitment Dashboard
description: Будує або оновлює інтерактивний HTML-дашборд рекрутингу на основі даних з Jira проекту REC (newsiteam.atlassian.net). Знає всі custom fields, patterns даних, структуру компонентів і типові помилки. Використовувати коли треба створити новий дашборд рекрутингу або оновити існуючий REC_recruitment_dashboard.html.
author: claude-code
tags: [recruitment, jira, dashboard, html, REC]
allowed-tools: Read, Write, Bash, Edit, Glob, Grep, mcp__9d92ed01-04ea-45ee-8a28-04392ecea6c7__searchJiraIssuesUsingJql, mcp__9d92ed01-04ea-45ee-8a28-04392ecea6c7__getJiraIssue, mcp__Claude_Preview__preview_start, mcp__Claude_Preview__preview_screenshot, mcp__Claude_Preview__preview_eval, mcp__Claude_Preview__preview_console_logs
---

# REC Recruitment Dashboard — Повний гайд

Цей skill містить всі напрацювання з побудови `REC_recruitment_dashboard.html`.
Використовуй для оновлення існуючого або побудови наступного рекрутинг-дашборду.

---

## Jira конфігурація

- **Project key**: `REC`
- **Cloud ID**: `657e24cd-f643-4482-aba5-7e848607df28`
- **Instance**: `https://newsiteam.atlassian.net`
- **MCP**: використовувати `mcp__9d92ed01-04ea-45ee-8a28-04392ecea6c7__searchJiraIssuesUsingJql` (НЕ curl/API token — немає доступу)
- **Issue types** (5):
  - `"Open position"` (id `16298`) — основні вакансії (FTE / Staff hire) → масиви `OP`, `WP`
  - `"Vacancy sub-task"` (id `16698`) — авто-створюється при `Number of hires > 1`, parent: Open position → масив `ST`
  - `"Recruitment Assignment"` (id `17332`) — **парадигма консультантів/контрактників** (Part-time / Project-based / Freelance / Consulting calls). Має 12 додаткових полів — див. секцію "Recruitment Assignment structure" нижче. Додано 2026-05-18.
  - `"Recruitment Assignment sub-task"` (id `17365`) — авто-створюється при `Number of specialists needed > 1`, parent: Recruitment Assignment.
  - `"Task"` (id `3`) — внутрішні задачі команди (research, операційні) → масив `TASKS`

---

## Custom Fields (перевірені)

| Поле | Field ID | Тип | Примітки |
|------|----------|-----|----------|
| Start date | `customfield_11223` | date string | Фільтр Section 1 — ТІЛЬКИ по цьому полю, НЕ по created |
| Recruiter | `customfield_13935` | multi-user array | `[0].displayName` — є і в OP, і в subtasks! Використовувати RECR lookup |
| Sourcer | `customfield_23510` | user picker object | `.displayName` — є і в OP, і в subtasks |
| Hiring Manager | `customfield_23509` | user picker | В OP зберігається як поле `so` (НЕ Sourcer!) |
| Seniority | `customfield_22876` | array `[{value:"Junior"}]` | Брати `[0].value`. 5 актуальних опцій: Intern/Junior/Middle/Senior/Lead. **Expert видалено 2026-05-15** — але історичні дані ще містять його, тому `snColor.Expert` лишається у HTML для коректного відображення старих чіпсів. |
| Number of hires | `customfield_23545` | integer | |
| **Factual close date** | `customfield_22878` | date string | Заповнюється РУКАМИ — часто пропускається. У JS зберігається як `v.fcd` |
| **First contact date** | `customfield_23407` | date string | Дата першого контакту з кандидатом → для TTH. У JS — `v.fcd_c` |
| **Team and subteams** | `customfield_23547` | cascading select | `value`=Department (`v.t`), `child.value`=sub-team (`v.sb`). Структура оновлена 2026-05-15 — див. секцію нижче. |
| **Candidate Source** | `customfield_24344` | option | Звідки прийшов кандидат (36 options — див. секцію нижче). У JS — `v.cs` |
| **Candidate source [Other]** | `customfield_25662` | textfield | Free-form text, заповнюється коли `cs="Other"`. У JS — `v.cs_other` |
| **Reason for opening** | `customfield_22877` | option | Replacement / Extention / Consultation. У JS — `v.r` |
| **End date** | `customfield_11232` | date string | Доступне в обох issue types (Open position + Recruitment Assignment). Додано 2026-05-18. |

### Recruitment Assignment — 12 додаткових полів (issuetype 17332 / 17365)

| Поле | Field ID | Тип | Примітки |
|------|----------|-----|----------|
| **Number of specialists needed** | `customfield_25663` | number (float) | Аналог `Number of hires` для консультантів. Тригер для авто-створення sub-task'ів. |
| **Type of cooperation** | `customfield_25664` | option | Consulting call(s) / Part-time / Project-based / Freelance / Other |
| **Type of cooperation [Other]** | `customfield_25665` | textfield | Free-text коли обрано "Other" |
| **Core requirements** | `customfield_25666` | textarea | Multi-line вимоги |
| **Nice-to-have requirements** | `customfield_25667` | textarea | Має пробіл наприкінці назви: `"Nice-to-have requirements "` |
| **Expected duration of engagement** | `customfield_25668` | textfield | Має пробіл наприкінці: `"Expected duration of engagement "` |
| **Will legal verification be required?** | `customfield_25669` | option | Yes / No / TBD |
| **Will NDA be required?** | `customfield_25670` | option | Yes / No (без TBD) |
| **Will Marketing Consent be needed?** | `customfield_25671` | option | Yes / No / TBD |
| **Budget range** | `customfield_25672` | textfield | Має пробіл наприкінці: `"Budget range "` |
| **Payment model** | `customfield_25673` | option | Має пробіл наприкінці. Hourly / Per deliverable / Fixed project fee / Monthly retainer / TBD |
| **Selection stages** | `customfield_25674` | textarea | Multi-line етапи відбору |

### Поле `hd` — Hired transition date (НЕ з custom field, з changelog!)

> Окрім `fcd` (custom field, заповнюється рукою), кожен Hired item має `hd` — **дату транзиту в статус Hired** з Jira changelog. Це окрема API-стежка:
>
> ```python
> GET /rest/api/3/issue/{KEY}/changelog
> # шукати entries з items[].field='status' AND items[].toString='Hired'
> # брати entry.created[:10] як hired-date
> ```
>
> Auto-updater (`scripts/update_rec_dashboard.py`) додає `hd` до кожного hired item у HW і CV. Helper `closeDate(v) = v.fcd || v.hd` використовується усюди в HTML для filter/aggregation.

---

## Team and subteams structure (customfield_23547) — оновлено 2026-05-15

Cascading select. `value`=Department (parent → JS `v.t`), `child.value`=sub-team (JS `v.sb`).
**ВАЖЛИВО**: написання має точно збігатися з Jira (case-sensitive, з пробілами).

### 13 департаментів і їх sub-teams (актуально станом на 2026-05-15)

| # | Department (parent `v.t`) | Sub-teams (`v.sb`) |
|---|----------------------------|---------------------|
| 1 | **Analytics** | Analytics, Web Analytics, Product, Data Analytics |
| 2 | **Brand Communications** | Brand Communications, Pr-Brand-Affiliate, SMM team, Influence marketing, E-mail Marketing |
| 3 | **Brand Design** | UX/UI, Brand Design, 2D, 3D |
| 4 | **Content** | Workout Content, Content Production, Content |
| 5 | **Customer Support** | Customer Support |
| 6 | **E-commerce** | Supply, Tech, Non-tech |
| 7 | **Employee Experience** | People Engagement, Operations |
| 8 | **Engineering** | Backend Core, BE Compliance, BE Core Platform, Coach, Coach Android, Coach iOS, DevOps, Embedded, Finance, Food Android, Food iOS, Hardware Android, Hardware iOS, Innovation, IT support, Mind, Mind Android, Mind iOS, Project, QA Core, Scrum, Security Operations, Web app, Workouts Android, Workouts iOS |
| 9 | **Finance** | Finance |
| 10 | **Legal** | Legal |
| 11 | **HR & TA** | HR, TA |
| 12 | **Marketing** | Creative, User Acquisition, Creative Marketing, PPC, SEO |
| 13 | **Product** | B2B, Business Analysts, Coach, Design, Growth Analytics, Product, Product Management, Retention, UX Research, Сreator platform (Cyrillic С!) |

### Що змінилося vs стара структура

| Зміна | Деталі |
|-------|--------|
| `Brand communications` → `Brand Communications` | Capital C |
| Додано: `Customer Support` | Новий dept |
| Видалено: `Leadership` | Більше нема як parent |
| `Content` отримав sub-teams | Workout Content, Content Production (раніше тільки Content) |
| `E-commerce` додано `Supply` | Раніше Tech, Non-tech |
| `Engineering` додано: `BE Compliance`, `BE Core Platform`, `Finance`, `Innovation`, `Project` | |
| `Product` додано: `Coach`, `Growth Analytics`, `Retention` | |
| `Marketing` додано: `Creative Marketing` | Раніше Creative окремо від Marketing |
| `Employee Experience` змінив sub-teams | Тепер: People Engagement, Operations |

### Gotchas (case-sensitive!)

- `E-commerce` — мала **c**, не E-Commerce
- `HR & TA` — з **пробілами** навколо `&`
- `Influence marketing` — мала **m** (на відміну від `Marketing` parent)
- `IT support`, `Web app` — мала перша літера у другому слові
- `Сreator platform` — починається з **Cyrillic С** (U+0421), не латинської C!
- Brand Communications — обидва слова з великої

### CV_DEPT_COLORS map (REC_recruitment_dashboard.html)

Має ключі для всіх 13 поточних департаментів + legacy aliases для backward compatibility:

```javascript
const CV_DEPT_COLORS={
  Marketing:'#3b6ef5', Product:'#10b981', Engineering:'#8b5cf6', Content:'#f59e0b',
  'E-commerce':'#ec4899', Legal:'#06b6d4', 'Brand Design':'#a855f7',
  'Brand Communications':'#f97316', Analytics:'#14b8a6', Finance:'#0ea5e9',
  'HR & TA':'#84cc16', 'Employee Experience':'#22d3ee', 'Customer Support':'#f43f5e',
  // Legacy aliases:
  'Brand communications':'#f97316', Leadership:'#dc2626'
};
```

При додаванні нового department у Jira → **обов'язково** додати ключ у `CV_DEPT_COLORS`. Інакше використається сірий fallback `#64748b`.

---

## Candidate Source structure (customfield_24344 + customfield_25662) — оновлено 2026-05-15

**Два поля працюють в парі**:

- `customfield_24344` "Candidate Source" — select з 36 опцій (включно з "Other")
- `customfield_25662` "Candidate source [Other]" — textfield, заповнюється коли в попередньому полі обрано "Other"

В CV-записах це проявляється як `v.cs` (option value) + `v.cs_other` (free text).

### 36 опцій Candidate Source

```
LinkedIn Sourced, LinkedIn Application, Djinni, Dou, Career Portal,
Internal Referral, External Referral, Internal Database,
Internal remote employee, Work.ua, Happy Monday, Robota.ua, Indeed,
Instagram, Hiring Event, Cresume, Upwork, Mate Academy, Support Team,
Vakansiatv, Balanced Body Site, Xiaohongshu, Motionintern, Network,
Law_events, Uniwork, Workado, Mediaplatforma, Behance, R9, Lezo,
WeChat, GoIT, After Courses, Genesis Transfer, Other
```

### Перейменування vs стара версія (важливо)

| Стара назва (видалена) | Нова назва |
|------------------------|------------|
| `Перехід Genesis` | `Genesis Transfer` |
| `Після курсів` | `After Courses` |
| `Internal Recommendation` | `Internal Referral` |
| `External Recommendation` | `External Referral` |
| `LinkedIn Applied` | `LinkedIn Application` |
| `Work` | `Work.ua` |
| `Robota` | `Robota.ua` |

Видалено: `Telegram`, `Employee`. Додано: `Mate Academy`, `Motionintern`, `Network`, `Lezo`.

### Gotcha: `Dou` зі звичайної D

Не `DOU` (як часто пишуть у мові) — у Jira саме `Dou`. Case-sensitive.

### Як показується "Other" з cs_other в дашборді

В дашборді (`reports/REC_recruitment_dashboard.html`) є helper:

```javascript
const _srcLabel=v=>v.cs==='Other'?(v.cs_other?`Other: ${v.cs_other}`:'Other'):v.cs;
```

Викликається в `rCVSources()`:
- Якщо `v.cs="Other"` + `v.cs_other="Friend's referral"` → label = `"Other: Friend's referral"` (окремий бар)
- Якщо `v.cs="Other"` без cs_other → label = `"Other"` (загальний бар)
- Якщо `v.cs="Dou"` → label = `"Dou"`

Це дозволяє різним free-text Other-відповідям бути окремими сегментами у Hiring Sources block замість зливатися в один "Other" bar.

Insights cards (Total Hires / Sources / Top Source) і click-to-popup також використовують `_srcLabel`.

### Conditional "Other source" колонка у popup

У `showCVSrcPopup(src, vacs, dept, sn)` детектиться по `src.startsWith('Other')`:

- popup для `"Other"` або `"Other: <text>"` → додається **8-а колонка** "Other source" зі значенням `v.cs_other` (порожні значення показуються як italic dash)
- popup для будь-якого іншого source (Dou, LinkedIn, etc) → колонка **НЕ** додається, popup має звичайні 7 колонок

Це дозволяє рекрутерам бачити прямо у popup'і вільний текст, який ввели у customfield_25662 коли обрали "Other".

---

## Recruitment Assignment structure (issue types 17332 / 17365) — додано 2026-05-19

**Парадигма консультантів/контрактників** — паралельна до Open position. Використовується для:
- Consulting call(s)
- Part-time
- Project-based
- Freelance

### Issue types

| Issue type | id | hierarchyLevel | Призначення |
|------------|----|----|-------------|
| Recruitment Assignment | `17332` | 0 (parent) | Основна задача |
| Recruitment Assignment sub-task | `17365` | -1 (sub-task) | Авто при `Number of specialists needed > 1` |

Sub-task має **той самий набір 27 полів** що й parent (всі 21 custom field + system) — потрібно для парадигми "кожен консультант = окремий sub-task із копією umbrella-метаданих".

### Автоматизації (4 правила) — копія патерна з Open position

| # | Назва | Тригер | Дія |
|---|-------|--------|-----|
| **Rule 1** | `[LP] subtasks creation for Number of specialists needed` | Field value changed: `Number of specialists needed` (Value added) на RA | Створює N−1 sub-task'ів якщо значення > 1 (до 9 гілок: > 1 → 1 sub, > 2 → 2 sub, …, > 9 → 9 sub) |
| **Rule 2** | `[RA] Decrement Number of specialists needed when sub-task Hired` | Work item transitioned → Hired, на RA sub-task | Branch: Parent → `Edit work item: Number of specialists needed = {{#=}}{{issue."Number of specialists needed"}} - 1{{/}}` |
| **Rule 3** | `[RA] Sync Number of specialists needed from parent to sub-tasks` | Field value changed: `Number of specialists needed` на RA | Branch: Sub-tasks → `Edit work item: Number of specialists needed = {{triggerIssue."Number of specialists needed"}}`. **Потрібна галочка "Allow other rule actions to trigger this rule"** у Rule details! |
| **Rule 4** | `Decrement Number of specialists needed when parent Hired` (опціональне) | Work item transitioned → Hired, на RA + умова "має sub-tasks" | `Number of specialists needed −= 1` тільки якщо є subs (solo parents → не чіпати, щоб аналітика лишилась коректною) |

### JSON template для копіювання полів у sub-task (Rule 1)

⚠️ **Дати** (`customfield_11223`, `11232`, `23407`) **не копіюються через Additional fields JSON** — Jira automation рендерить їх з timestamp/timezone який ламає JSON парсинг. Дати додавати через UI "Choose fields to set" (там datepicker handles format автоматично).

Робочий JSON для Additional fields (без дат — їх через UI):

```json
{
  "fields": {
    "priority": {"name": "{{issue.priority.name}}"}
    {{#issue.customfield_23509}},"customfield_23509": "{{issue.customfield_23509}}"{{/}}
    {{#issue.customfield_25662}},"customfield_25662": "{{issue.customfield_25662}}"{{/}}
    {{#issue.customfield_25663}},"customfield_25663": {{issue.customfield_25663}}{{/}}
    {{#issue.customfield_25665}},"customfield_25665": "{{issue.customfield_25665}}"{{/}}
    {{#issue.customfield_25666}},"customfield_25666": "{{issue.customfield_25666}}"{{/}}
    {{#issue.customfield_25667}},"customfield_25667": "{{issue.customfield_25667}}"{{/}}
    {{#issue.customfield_25668}},"customfield_25668": "{{issue.customfield_25668}}"{{/}}
    {{#issue.customfield_25672}},"customfield_25672": "{{issue.customfield_25672}}"{{/}}
    {{#issue.customfield_25674}},"customfield_25674": "{{issue.customfield_25674}}"{{/}}
    {{#issue.customfield_13935.size}},"customfield_13935": [{{#issue.customfield_13935}}{"accountId": "{{accountId}}"}{{^last}},{{/}}{{/}}]{{/}}
    {{#issue.customfield_23510}},"customfield_23510": {"accountId": "{{accountId}}"}{{/}}
    {{#issue.customfield_23547}},"customfield_23547": {"value": "{{value}}"{{#child.value}}, "child": {"value": "{{child.value}}"}{{/}}}{{/}}
    {{#issue.customfield_24344}},"customfield_24344": {"value": "{{value}}"}{{/}}
    {{#issue.customfield_25664}},"customfield_25664": {"value": "{{value}}"}{{/}}
    {{#issue.customfield_25669}},"customfield_25669": {"value": "{{value}}"}{{/}}
    {{#issue.customfield_25670}},"customfield_25670": {"value": "{{value}}"}{{/}}
    {{#issue.customfield_25671}},"customfield_25671": {"value": "{{value}}"}{{/}}
    {{#issue.customfield_25673}},"customfield_25673": {"value": "{{value}}"}{{/}}
  }
}
```

UI "Choose fields to set" — додати 5 полів:
- `Summary` = `{{issue.summary}}`
- `Description` = `{{issue.description}}`
- `Start date` = `{{issue.customfield_11223}}`
- `End date` = `{{issue.customfield_11232}}`
- `First contact date` = `{{issue.customfield_23407}}`

### Lessons learned (важливе для майбутніх правил)

1. **Conditional Mustache `{{#issue.X}}...{{/}}`** — обов'язково для всіх select/cascading/user полів. Якщо parent поле порожнє, `{"value": ""}` → API rejects з "Specify a valid value for X".
2. **Multi-user (Recruiter)** — використовувати `{{#issue.customfield_13935.size}}...{{/}}` для conditional + ітерація `{{#issue.customfield_13935}}{{^last}},{{/}}{{/}}` для масиву accountId'ів.
3. **Дати ламають JSON Additional fields** — використовувати UI "Choose fields to set" або Branch + Edit work item.
4. **`{{value}}` усередині `{{#issue.cf_X}}`** працює — Jira перемикає контекст на field object.
5. **`.jsonEncode` / `.jiraDate`** smart values — НЕ використовувати, поведінка нестабільна, ламає інші поля.

### Дашборд інтеграція (статус 2026-05-19)

Поки що RA та RA sub-task **НЕ рендеряться** на дашборді — це окрема парадигма (консультанти, не FTE hires). Auto-update script вже **фетчить** обидва types у нові арреї `RA` і `RAS` (готові для майбутніх блоків). Existing блоки (Workload / Open Vacancies / Closed Vacancies) працюють тільки з Open position + Vacancy sub-task.

Якщо буде потреба показати консультантів — додати окремі секції або таб "Consultants" на основі `RA` / `RAS` масивів.

---

## JQL запити

```
// Всі відкриті позиції (з рекрутером і сорсером)
project = REC AND issuetype = "Open position" AND statusCategory != Done ORDER BY key DESC
fields: ["summary","status","priority","customfield_11223","customfield_22876",
         "customfield_13935","customfield_23510","customfield_23509","customfield_23545"]
// maxResults: 100, обробляти через Bash+python3 (результат зазвичай > 100k символів)

// Всі активні Vacancy sub-tasks
project = REC AND issuetype = "Vacancy sub-task" AND statusCategory != Done ORDER BY key DESC
fields: ["summary","status","priority","customfield_11223","customfield_13935","customfield_23510","parent"]
// maxResults: 100

// Hired цього тижня (для HW)
project = REC AND status = Hired AND statusCategory = Done AND updated >= "YYYY-MM-DD"
// + expand=changelog для кожної задачі щоб отримати factual close date

// Recruitment Assignments (консультанти) — окрема парадигма
project = REC AND issuetype = "Recruitment Assignment" AND statusCategory != Done ORDER BY key DESC
fields: ["summary","status","priority","customfield_11223","customfield_11232","customfield_22876",
         "customfield_13935","customfield_23510","customfield_23509",
         "customfield_25663","customfield_25664","customfield_25666","customfield_25674"]

// Активні RA sub-tasks
project = REC AND issuetype = "Recruitment Assignment sub-task" AND statusCategory != Done ORDER BY key DESC
fields: ["summary","status","priority","customfield_11223","customfield_13935","parent",
         "customfield_25663","customfield_25664"]
```

### Обробка великих результатів JQL через Bash

```bash
cat "tool-results/...txt" | python3 -c "
import json, sys
data = json.load(sys.stdin)
text = data[0]['text']
issues = json.loads(text)['issues']
for i in issues:
    key = i['key']
    f = i['fields']
    rec_arr = f.get('customfield_13935')
    rec = rec_arr[0]['displayName'] if rec_arr else None
    src_obj = f.get('customfield_23510')
    src = src_obj['displayName'] if src_obj else None
    pk = f.get('parent',{}).get('key','?')  # для subtasks
    sd = f.get('customfield_11223')
    print(f'{key}|pk={pk}|rec={rec}|src={src}|sd={sd}')
"
```

---

## Архітектура даних

### Масиви

```javascript
// OP — всі відкриті позиції (базовий набір полів)
// Поля: key, s(ummary), st(atus), pr(iority), so(HiringMgr), re(Sourcer), h(ires), r(eason), t(eam), sb(team2), cr(eated)
// УВАГА: re = Sourcer (customfield_23510), so = HiringMgr (customfield_23509) — НЕ навпаки!
const OP=[...]

// WP — збагачені позиції (sn, sd заповнені — витягнуті окремо по тих, що є в поточному тижні)
// Поля: key, s, st, pr, sn, rec, src, sd, h, t, sb, cr
// ВАЖЛИВО: rec/src в WP можуть бути застарілими — завжди перекривати через RECR/SRCR!
const WP=[...]

// HW — hired this week, з factual close date з changelog
// Поля: key, s, type('position'|'subtask'), pk(якщо subtask), pr, sn, rec, src, fcd, h, t, sb
const HW=[...]

// ST — всі активні Vacancy sub-tasks (statusCategory != Done)
// Поля: key, pk(parent key), s, st(atus), sd, rec, src
// Актуальні на 2026-04-24: 39 записів
const ST=[...]
```

### Lookup таблиці

```javascript
// Start dates (customfield_11223) для всіх OP
const SD={"REC-286":"2026-04-24","REC-285":"2026-04-23", ...};

// Seniority (customfield_22876[0].value) для всіх OP
const SN={"REC-286":"Intern","REC-285":"Expert", ...};

// Recruiter (customfield_13935[0].displayName) — АВТОРИТЕТНЕ ДЖЕРЕЛО
// Витягується окремим JQL запитом, перекриває WP.rec
const RECR={
  "REC-285":"Victoria Kotenko","REC-284":"Victoria Kotenko",
  "REC-283":"Victoria Kotenko","REC-282":"Victoria Kotenko",
  "REC-274":"Yaroslava Bondarchuk","REC-272":"Yaroslava Bondarchuk",
  "REC-271":"Victoria Kotenko","REC-270":"Mariia Salabai",
  "REC-249":"Mariia Salabai","REC-245":"Victoria Kotenko",
  "REC-244":"Yaroslava Bondarchuk","REC-243":"Polina Serdiuk",
  "REC-242":"Alina Muravchyk","REC-240":"Victoria Kotenko",
  "REC-237":"Violetta Strelchenko","REC-236":"Anastasiia Shapovalenko",
  "REC-228":"Anastasiia Shapovalenko","REC-221":"Violetta Strelchenko",
  "REC-220":"Violetta Strelchenko","REC-213":"Alina Muravchyk",
  "REC-211":"Mariia Salabai","REC-210":"Victoria Kotenko",
  "REC-205":"Mariia Salabai","REC-204":"Victoria Kotenko",
  "REC-200":"Victoria Kotenko","REC-198":"Mariia Salabai",
  "REC-197":"Anastasiia Shapovalenko","REC-195":"Veronika Khovrina",
  "REC-193":"Veronika Khovrina","REC-192":"Veronika Khovrina",
  "REC-191":"Veronika Khovrina","REC-190":"Veronika Khovrina",
  "REC-188":"Anastasiia Prylutska","REC-184":"Yaroslava Bondarchuk",
  "REC-183":"Polina Serdiuk","REC-182":"Polina Serdiuk",
  "REC-181":"Polina Serdiuk","REC-178":"Veronika Khovrina",
  "REC-177":"Yaroslava Bondarchuk","REC-163":"Mariia Salabai",
  "REC-141":"Anastasiia Shapovalenko","REC-46":"Yaroslava Bondarchuk",
  "REC-40":"Yaroslava Bondarchuk",
};

// Sourcer (customfield_23510.displayName) — тільки ті, в кого є
const SRCR={
  "REC-249":"Kateryna Yaremenko","REC-198":"Kateryna Yaremenko",
  "REC-195":"Alina Muravchyk","REC-193":"Alina Muravchyk",
  "REC-190":"Kateryna Yaremenko","REC-188":"Kateryna Yaremenko",
  "REC-178":"Anastasiia Melnyk","REC-177":"Anastasiia Melnyk",
  "REC-163":"Kateryna Yaremenko","REC-46":"Anastasiia Melnyk",
};
```

### Merge ALL_VACS (RECR/SRCR — авторитетне джерело, перекривають WP)

```javascript
// RECR і SRCR завжди мають пріоритет над WP.rec/WP.src (дані WP можуть бути застарілими)
// КРИТИЧНО: при WP override обов'язково зберігати r:v.r||null — WP не має поля r!
const ALL_VACS=OP.map(v=>{
  const wp=WP.find(w=>w.key===v.key);
  const rec=RECR[v.key]||null;
  const src=SRCR[v.key]||(wp?.src)||v.re||null;
  if(wp) return{...wp, rec, src, r:v.r||null};  // r ЗАВЖДИ з OP!
  return{key:v.key,s:v.s,st:v.st,pr:v.pr,
    sn:SN[v.key]||null, rec, src,
    sd:SD[v.key]||null,
    h:v.h,t:v.t,sb:v.sb,r:v.r,cr:v.cr};
});
```

---

## Динамічний тиждень (Пн–Нд)

```javascript
const _d=new Date(),_dy=_d.getDay()||7;
const _m=new Date(_d);_m.setDate(_d.getDate()-_dy+1);
const _s=new Date(_m);_s.setDate(_m.getDate()+6);
const _fmt=d=>`${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`;
const WS=_fmt(_m), WE=_fmt(_s);  // НЕ хардкодити дати!
```

---

## KPI Section

4 картки в одному рядку `display:flex;align-items:stretch;gap:12px`:
- **Active Vacancies** (blue) — `OP.length`
- **Plan** (blue) — `OP.filter(v=>v.st==='Plan').length`
- **In Progress** (orange) — `OP.filter(v=>v.st==='In progress').length`
- **Hires Needed** (orange) — `OP.reduce((s,v)=>s+v.h,0)`

```javascript
function rKPI(){
  document.getElementById('kn-av').textContent=OP.length;
  document.getElementById('kn-hn').textContent=OP.reduce((s,v)=>s+v.h,0);
  document.getElementById('kn-plan').textContent=OP.filter(v=>v.st==='Plan').length;
  document.getElementById('kn-ip').textContent=OP.filter(v=>v.st==='In progress').length;
}
```

**ПРАВИЛА KPI:**
- ✅ Всі 4 картки в одному рядку, `align-items:stretch` для рівної висоти
- ✅ Кожна картка: `flex:1;justify-content:center`
- ❌ НЕ використовувати `id="kpi-row"` і старий 7-карточний grid — видалено!
- ❌ НЕ додавати стрілки між картками — вже видалено, не повертати!

---

## Charts Section

Два бар-графіки в grid 1fr 1fr (`class="charts-row"`), розміщені до Section 1.
**Порядок: Opened This Week (ліво), Hires This Week (право).**

### HTML структура card
```html
<div class="chart-card">
  <div class="chart-hdr" style="justify-content:space-between;align-items:center">
    <span class="chart-title">Opened This Week</span>
    <span style="font-size:26px;font-weight:700;color:var(--blue);line-height:1" id="opened-total">—</span>
  </div>
  <!-- Period picker (same style as S1/S2) -->
  <div style="display:flex;align-items:center;gap:8px;margin-bottom:10px;flex-wrap:wrap">
    <span style="font-size:12px;color:var(--text2);font-weight:500">Period:</span>
    <input type="date" id="opened-from" style="...">
    <span style="color:var(--slate);font-size:13px">—</span>
    <input type="date" id="opened-to" style="...">
    <button onclick="rChartOpened(document.getElementById('opened-from').value,
                                   document.getElementById('opened-to').value)"
            class="upd-btn" style="padding:5px 14px;font-size:12px">Apply</button>
  </div>
  <div style="position:relative;height:180px"><canvas id="chart-opened"></canvas></div>
</div>
```

### Helper функції
```javascript
let hiresFrom=WS, hiresTo=WE, openedFrom=WS, openedTo=WE;
let _chHires=null, _chOpened=null;

function _dateRange(from,to){
  const arr=[],d=new Date(from+'T00:00:00'),e=new Date(to+'T00:00:00');
  while(d<=e){arr.push(_fmt(d));d.setDate(d.getDate()+1);}
  return arr;
}
function _dLabel(d){
  const dt=new Date(d+'T00:00:00');
  const dy=['Sun','Mon','Tue','Wed','Thu','Fri','Sat'][dt.getDay()];
  return `${String(dt.getMonth()+1).padStart(2,'0')}/${String(dt.getDate()).padStart(2,'0')} ${dy}`;
}
function _cumul(arr){return arr.map((_,i)=>arr.slice(0,i+1).reduce((a,b)=>a+b,0));}
function _lineDs(data,color){return{type:'line',data,borderColor:color,borderWidth:2,
  borderDash:[5,3],pointBackgroundColor:color,pointRadius:3,pointHoverRadius:5,
  fill:false,tension:0.3,order:1};}
```

### Shared bar-label plugin (пропускати line datasets!)
```javascript
const _chartPlugin=[{
  id:'barLabels',
  afterDatasetsDraw(chart){
    const {ctx:c,data}=chart;
    chart.data.datasets.forEach((ds,di)=>{
      if(ds.type==='line')return;  // КРИТИЧНО: пропускати line datasets!
      const meta=chart.getDatasetMeta(di);
      meta.data.forEach((bar,i)=>{
        const v=data.datasets[di].data[i];
        if(!v)return;
        const props=bar.getProps(['x','y','base'],true);
        const barH=props.base-props.y;
        c.save(); c.font='bold 11px Inter,sans-serif'; c.textAlign='center';
        if(barH>22){
          c.fillStyle='rgba(255,255,255,0.92)'; c.textBaseline='middle';
          c.fillText(v,props.x,props.y+barH/2);
        } else {
          c.fillStyle=ds.borderColor||'#374151'; c.textBaseline='bottom';
          c.fillText(v,props.x,props.y-3);
        }
        c.restore();
      });
    });
  }
}];
```

### rChartHires — бар + кумулятивна лінія
```javascript
function rChartHires(from,to){
  if(from!==undefined)hiresFrom=from;
  if(to!==undefined)hiresTo=to;
  document.getElementById('hires-from').value=hiresFrom;
  document.getElementById('hires-to').value=hiresTo;
  const dates=_dateRange(hiresFrom,hiresTo);
  const counts=dates.map(d=>HW.filter(v=>v.fcd===d).length);
  const total=counts.reduce((a,b)=>a+b,0);
  document.getElementById('hires-total').textContent=total;
  if(_chHires){_chHires.destroy();_chHires=null;}
  _chHires=new Chart(document.getElementById('chart-hires').getContext('2d'),{
    type:'bar',
    data:{labels:dates.map(_dLabel),datasets:[
      {type:'bar',data:counts,backgroundColor:'#4ade80',hoverBackgroundColor:'#22c55e',
       borderColor:'#4ade80',borderWidth:0,borderRadius:7,borderSkipped:false,order:2},
      _lineDs(_cumul(counts),'#16a34a')
    ]},
    options:{responsive:true,maintainAspectRatio:false,animation:{duration:400},barPercentage:0.7,
      plugins:{legend:{display:false},datalabels:false,
        tooltip:{backgroundColor:'#1e293b',titleColor:'#f8fafc',bodyColor:'#94a3b8',
          borderColor:'#334155',borderWidth:1,padding:{x:14,y:10},cornerRadius:10,
          callbacks:{label:ctx=>ctx.dataset.type==='line'
            ?`  Cumul: ${ctx.parsed.y}`
            :`  ${ctx.parsed.y} hire${ctx.parsed.y!==1?'s':''}`}}},
      scales:{
        y:{beginAtZero:true,border:{display:false,dash:[3,3]},grid:{color:'#f1f5f9',lineWidth:1},
           ticks:{font:{family:'Inter',size:11},color:'#94a3b8',precision:0}},
        x:{grid:{display:false},border:{display:false},
           ticks:{font:{family:'Inter',size:10,weight:'500'},color:'#64748b',maxRotation:30}}
      }},plugins:_chartPlugin});
}
```

### rChartOpened — аналогічно, але по SD і синій колір
```javascript
// Дані: Object.values(SD).filter(Boolean) — start dates всіх активних OP
// backgroundColor:'#60a5fa', cumul line color:'#2563eb'
// id: chart-opened, hires-total → opened-total, hires-from/to → opened-from/to
```

**ПРАВИЛА Charts:**
- ✅ Period picker — той самий стиль що S1/S2 (date inputs + Apply)
- ✅ Default: `hiresFrom=WS, hiresTo=WE` (поточний Пн–Нд), встановлювати через `document.getElementById('...').value=hiresFrom`
- ✅ X-axis: один стовпець на день у діапазоні (не фіксований Mon–Sun!)
- ✅ Кумулятивна лінія: `_lineDs(_cumul(counts), color)` як другий dataset
- ✅ `_chartPlugin` — обов'язково `if(ds.type==='line')return` щоб не малювати labels на лінії
- ✅ Total number `id="hires-total"` / `id="opened-total"` — оновлювати з `counts.reduce((a,b)=>a+b,0)`
- ✅ Порядок карток: Opened зліва, Hires справа
- ❌ НЕ використовувати dropdown з hardcoded тижнями — видалено!

---

## Section 1: Відкриті вакансії поточного тижня

### Фільтр
```javascript
// ТІЛЬКИ по Start date, НЕ по created! Виключати Hired.
let items=ALL_VACS.filter(v=>v.sd&&v.sd>=s1From&&v.sd<=s1To&&v.st!=='Hired');
```

### Subtasks — завжди видимі (без expand/collapse)
```javascript
// Subtask з sd:null — показувати завжди. Виключати Hired.
const subs=ST.filter(s=>
  s.pk===v.key && s.st!=='Hired' && (!s.sd||(s.sd>=s1From&&s.sd<=s1To))
);
```

### Sub-task рядки — ВСІ поля заповнені, успадковувати від батька

```javascript
const subRows=subs.map(s=>{
  const ssdHtml=s.sd?`<span style="font-size:11px;color:var(--text2)">${s.sd}</span>`:'<span class="dash-val">—</span>';
  const sdt=[s.t||v.t, s.sb||v.sb].filter(Boolean).join(' / ');
  const sPr=s.pr||v.pr;
  const sSn=s.sn||v.sn;
  const sSnHtml=sSn?`<span style="font-size:11px;font-weight:500;color:${snColor[sSn]||'#475569'}">${sSn}</span>`:'<span class="dash-val">—</span>';
  const sHires=s.h!=null?s.h:1;
  return`<tr style="background:#f5f8ff">
    <td style="padding-left:18px;font-size:12px">↳ ${jl(s.key)}</td>
    <td style="font-size:11px">${s.s}</td>
    <td>${sb2(s.st)}</td>
    <td>${pb(sPr)}</td>
    <td>${sSnHtml}</td>
    <td style="font-size:11px">${fv(s.rec)}</td>
    <td style="font-size:11px">${fv(s.src)}</td>
    <td>${ssdHtml}</td>
    <td style="font-size:11px">${fv(sdt)}</td>
    <td style="text-align:center"><b style="color:#0f172a">${sHires}</b></td>
  </tr>`;
}).join('');
```

**ПРАВИЛА для subtask рядків у Section 1:**
- Priority: `s.pr || v.pr` (власний або від батька)
- Seniority: `s.sn || v.sn` (власний або від батька)
- Dept/Team: `[s.t||v.t, s.sb||v.sb].filter(Boolean).join(' / ')`
- Hires: `s.h != null ? s.h : 1`
- Recruiter/Sourcer: власні поля `s.rec`, `s.src`
- ❌ НЕ використовувати `color:#64748b` на назві вакансії в subtask рядках

---

## Section 2: Hired вакансії

### Заголовок
```html
<h2>Hired вакансії поточного тижня &nbsp;
  <span style="color:#94a3b8;font-weight:400">
    (фільтр по Factual close date + transition to Hired status)
  </span>
</h2>
```

### Фільтр — два джерела (union)

> **ВАЖЛИВО (2026-04-28):** Кожен Hired item тепер має ДВА можливих "close date":
> - `v.fcd` — поле **Factual close date** (`customfield_22878`), заповнене вручну рекрутером
> - `v.hd` — дата **transition to Hired** з Jira **changelog** (`POST /rest/api/3/issue/{key}/changelog`)
>
> Часто рекрутери забувають заповнити `fcd`, але транзишн в Jira завжди є. Тому **усі фільтри і обчислення повинні використовувати helper `closeDate(v) = v.fcd || v.hd || null`** замість `v.fcd`.
>
> Helper визначений у HTML одразу після `_fmt`:
> ```javascript
> const closeDate = v => v.fcd || v.hd || null;
> ```

```javascript
// Source 1: HW filtered by closeDate (fcd OR hd transition date)
const inRange=d=>d&&d>=s2From&&d<=s2To;
const hwItems=HW.filter(v=>inRange(v.fcd)||inRange(v.hd));
const hwKeys=new Set(hwItems.map(v=>v.key));

// Source 2: ALL_VACS items з st='Hired' і sd в діапазоні (не в HW)
const avHired=ALL_VACS.filter(v=>v.st==='Hired'&&v.sd&&v.sd>=s2From&&v.sd<=s2To&&!hwKeys.has(v.key))
  .map(v=>({...v,fcd:v.sd,type:'position'}));

// Source 3: ST items з st='Hired' і sd в діапазоні (не в HW)
const usedKeys=new Set([...hwKeys,...avHired.map(v=>v.key)]);
const stHired=ST.filter(v=>v.st==='Hired'&&v.sd&&v.sd>=s2From&&v.sd<=s2To&&!usedKeys.has(v.key))
  .map(v=>{
    const par=ALL_VACS.find(p=>p.key===v.pk);
    return{key:v.key,s:v.s,type:'subtask',pk:v.pk,
      pr:par?.pr||null,sn:par?.sn||SN[v.pk]||null,
      rec:v.rec,src:v.src,fcd:v.sd,
      h:1,t:par?.t||null,sb:par?.sb||null,st:v.st};
  });

let items=[...hwItems,...avHired,...stHired];
```

### КРИТИЧНО: hires count — sub-task = 1 особа, НЕ v.h

**Дані Jira: sub-task у HW успадковує `parent.h`** (наприклад REC-314 sub з parent REC-163 має h=11 — це значення parent's expected total hires). Це нормально для Jira-моделі, але для S2 hires count це баг — ми хочемо рахувати реальних людей найнятих в період.

**Семантика**:
- 1 hired sub-task = 1 особа (h=1, незалежно від parent.h)
- 1 hired position (parent сам Hired без subs) = parent.h (рідкісний випадок)

```javascript
// ✅ ПРАВИЛЬНО — sub-task завжди 1, position використовує v.h
const hiresTotal2=items.reduce((s,v)=>s+(v.type==='subtask'?1:(v.h||1)),0);

// ❌ НЕПРАВИЛЬНО — дає inflated count (REC-314 рахується як 11 hires замість 1)
// const hiresTotal2=items.reduce((s,v)=>s+(v.h||1),0);
```

**Реальний приклад**: 6 sub-tasks хайрено цього тижня (REC-314, 313, 251, 214, 180, 179), кожний з h=11/3/5/3/3 успадкованим від parent.
- Стара формула: `11+11+3+5+3+3 = 36` ❌
- Нова формула: `1+1+1+1+1+1 = 6` ✓

**Те саме у render**: HIRES колонка sub-task рядка має показувати `1`, а не `${v.h}`:

```javascript
// ✅ Sub-task row HIRES cell
rows2+=`<tr><td>↳ ${jl(v.key)}</td>...<td><b>1</b></td></tr>`;

// ❌ НЕ показувати v.h для subs:
// rows2+=`<tr><td>↳ ${jl(v.key)}</td>...<td><b>${v.h}</b></td></tr>`;
```

Parent placeholder row (сірий, для context) — там `${parent.h}` коректно (показує parent's expected total).

### Групування subtasks з батьківським контекстом

```javascript
// Окремо positions і subtasks; subtasks групуємо по pk
const positions=items.filter(v=>v.type!=='subtask');
const subtasks=items.filter(v=>v.type==='subtask');
const byParent={};
subtasks.forEach(v=>{if(!byParent[v.pk])byParent[v.pk]=[];byParent[v.pk].push(v);});

// Для кожної групи subtasks — сірий рядок батька (якщо батько НЕ Hired)
Object.entries(byParent).forEach(([pk,subs])=>{
  subs.sort((a,b)=>b.fcd.localeCompare(a.fcd));
  const parent=ALL_VACS.find(v=>v.key===pk);
  const pHired=parent&&parent.st==='Hired';
  if(parent&&!pHired){
    // Fallback рекрутера/сорсера з першого subtask якщо батько не має
    const pRec=parent.rec||subs[0]?.rec||null;
    const pSrc=parent.src||subs[0]?.src||null;
    // Сірий рядок батька
    rows2+=`<tr style="background:#f8fafc;color:#94a3b8">...</tr>`;
  }
  // Subtask рядки (НЕ сірі, без color:#64748b на назві!)
  subs.forEach(v=>{
    rows2+=`<tr style="background:#f5f8ff">
      <td style="padding-left:18px;font-size:12px">↳ ${jl(v.key)}</td>
      <td style="max-width:210px;font-size:11px">${v.s}</td>  // БЕЗ color:#64748b!
      ...
    </tr>`;
  });
});
```

**ПРАВИЛА сірого кольору:**
- ✅ Тільки батьківський контекст-рядок у Section 2 коли батько НЕ Hired: `style="background:#f8fafc;color:#94a3b8"`
- ❌ НЕ сірити subtask рядки (ні фон, ні текст назви вакансії)
- Subtask рядки: `style="background:#f5f8ff"` — блакитний фон, нормальний текст

---

## Factual Close Date (fcd)

Витягується через `expand=changelog` у `getJiraIssue`:

```javascript
// Шукати transition до статусу "Hired" в changelog
const hiringEntry = issue.changelog.histories
  .filter(h => h.items.some(i => i.field==='status' && i.toString==='Hired'))
  .sort((a,b) => new Date(b.created)-new Date(a.created))[0];
const fcd = hiringEntry ? hiringEntry.created.split('T')[0] : null;
```

---

## Helper функції

```javascript
const J='https://newsiteam.atlassian.net/browse/';
function jl(k){return `<a class="jl" href="${J}${k}" target="_blank">${k}</a>`;}
function fv(v){return v&&v!=='-'?v:`<span class="dash-val">—</span>`;}
// TODAY = local midnight today (NEVER hardcoded — auto-update from system clock)
const TODAY=(()=>{const t=new Date();return new Date(t.getFullYear(),t.getMonth(),t.getDate());})();
// dag = calendar-day diff. Date string ('YYYY-MM-DD') парситься як LOCAL date,
// інакше new Date(string) інтерпретує як UTC midnight, що дає off-by-one в +X TZ.
function dag(d){
  if(!d) return null;
  const parts=String(d).split('-').map(Number);
  const sd=new Date(parts[0],parts[1]-1,parts[2]);
  return Math.floor((TODAY-sd)/86400000);
}

const pOrd={High:0,Medium:1,Low:2};
function pb(p){const m={High:'ph',Medium:'pm',Low:'pl'};return p?`<span class="bp ${m[p]||'pl'}">${p}</span>`:'<span class="dash-val">—</span>';}
function sb2(s){const m={'In progress':'sip','Plan':'spl','Hired':'shi'};return `<span class="bp ${m[s]||'spl'}">${s}</span>`;}
const snColor={Junior:'#7c3aed',Middle:'#1d4ed8',Senior:'#0369a1',Lead:'#065f46',Expert:'#92400e',Intern:'#6b7280'};
```

---

## Sortable columns

```javascript
let s1SortCol=null, s1SortDir=1;
function s1sort(col){
  if(s1SortCol===col)s1SortDir*=-1; else{s1SortCol=col;s1SortDir=1;}
  r1();
}
// В th: onclick="s1sort('pr')"
// Arrow: on?(s1SortDir===1?'▴':'▾'):'⇅'
// Колір стрілки: on?'#3b6ef5':'#c8d2e0'
```

---

## CSS компоненти

```css
/* Compact table */
.tbl-compact th { padding: 6px 9px; font-size: 10px; }
.tbl-compact td { padding: 5px 9px; line-height: 1.35; }

/* Sub-task рядки в Section 1 (відкриті вакансії) */
tr[style*="background:#f5f8ff"] td { border-bottom: 1px solid #e8edf8; }

/* Badge */
.bp { display:inline-flex; align-items:center; padding:2px 8px; border-radius:4px; font-size:11px; font-weight:500; }
.sip { background:#eff6ff; color:#1d4ed8; }
.spl { background:#f8fafc; color:#475569; border:1px solid #e2e8f0; }
.shi { background:#f0fdf4; color:#16a34a; }
.ph  { background:#fef2f2; color:#dc2626; }
.pm  { background:#fffbeb; color:#d97706; }
.pl  { background:#f8fafc; color:#64748b; }
```

---

## Колонки Section 1

| ID | Label | Примітки |
|----|-------|----------|
| key | Key | clickable Jira link, `↳` prefix для subtasks |
| s | Vacancy | max-width:210px |
| st | Status | subtask успадковує власний |
| pr | Priority | `s.pr\|\|v.pr` для subtasks |
| sn | Seniority | `s.sn\|\|v.sn` для subtasks, snColor badge |
| rec | Recruiter | font-size:11px |
| src | Sourcer | font-size:11px |
| sd | Start date | font-size:11px |
| dt | Dept / Team | `[s.t\|\|v.t, s.sb\|\|v.sb].filter(Boolean).join(' / ')` |
| h | Hires | `s.h!=null?s.h:1` для subtasks |

---

## Структура HTML файлу

```
<head>
  Inter font (Google Fonts)
  Chart.js 4.4.0 CDN
  CSS: variables (--blue, --border, --text2, --bg, --card), components
</head>
<body>
  <header>  назва, дата, посилання на Jira проект

  <!-- KPI — 4 cards в одному flex рядку (align-items:stretch;gap:12px) -->
  <div style="display:flex;align-items:stretch;gap:12px;margin-bottom:28px">
    kpi-card blue: Active Vacancies (#kn-av)
    kpi-card blue: Plan (#kn-plan)
    kpi-card orange: In Progress (#kn-ip)
    kpi-card orange: Hires Needed (#kn-hn)
  </div>

  <!-- Charts row: Opened This Week (ліво) + Hires This Week (право) -->
  <div class="charts-row">  grid 1fr 1fr, gap:20px
    chart-card: Opened This Week
      total number top-right (#opened-total)
      Period picker: from/to date + Apply (default WS/WE)
      canvas#chart-opened (height:180px, bars + cumulative dashed line)
    chart-card: Hires This Week
      total number top-right (#hires-total)
      Period picker: from/to date + Apply (default WS/WE)
      canvas#chart-hires (height:180px, bars + cumulative dashed line)
  </div>

  <section#s1>  Відкриті вакансії поточного тижня (фільтр по Start date, без Hired)
    badge: N вакансій · M hires  (id="b1")
    Period picker: from/to date inputs + Apply button
    sortable table, subtasks завжди видимі (без expand/collapse)
  <section#s2>  Hired вакансії (фільтр: fcd + transition to Hired)
    badge: N закрито  (id="b2")
    Period picker: from/to date inputs + Apply button
    sortable table, subtasks з сірим батьківським рядком якщо батько не Hired
  <section#s3>  Open Vacancies per Department — DUAL: 'In progress only' + 'Plan only' (#c3 + #c3p)
    Кожна секція self-contained зі своїм підрахунком (parent+matching subs only)
    Колонки: Department | Seniority | Teams | <Status> | Vacancies | Hires (БЕЗ Distribution!)
    Expandable: vacancy rows + sub-task rows; subs відфільтровані по статусу секції
  <section#s4>  Roles by Days Open (Hiring Focus) — активні позиції, фільтр по Start date, default 30+ днів
  <section#s5>  Вакансії In Progress по рекрутерах
  <script>
    const TODAY, WS, WE
    const SD, SN, RECR, SRCR  (lookup таблиці)
    const OP, WP, HW, ST, ALL_VACS
    helper functions: dag, pb, sb2, jl, fv, snColor
    chart helpers: _dateRange, _dLabel, _cumul, _lineDs, _chartPlugin
    render functions: rKPI, rChartHires, rChartOpened, r1, r2, r3, r4, r5
    s1sort, s2sort, s3Sort
    module-level state: _s3SortCol, _s3SortDir, _s3deptVacs, hiresFrom, hiresTo, openedFrom, openedTo
    init: rKPI(); rChartHires(); rChartOpened(); r1(); r2(); r3(); r4(); r5();
</body>
```

---

## Section 3: Open Vacancies per Department — DUAL (IP + Plan)

**Розділена на 2 паралельні секції з ідентичною структурою**, кожна self-contained зі своїм фільтром і підрахунком:

### HTML — дві section-и поряд

```html
<!-- IP-only -->
<section>
  <div class="section-header">
    <h2>Open Vacancies per Department <span class="status-tag" style="color:#3b6ef5;background:#eff6ff">In progress only</span></h2>
    <span class="sec-badge" id="b3"></span>
  </div>
  <div id="c3"></div>
</section>

<!-- Plan-only mirror -->
<section>
  <div class="section-header">
    <h2>Open Vacancies per Department <span class="status-tag" style="color:#475569;background:#f1f5f9">Plan only</span></h2>
    <span class="sec-badge" id="b3p"></span>
  </div>
  <div id="c3p"></div>
</section>
```

### Колонки — 6 шт у ОБОХ секціях (БЕЗ Distribution — вона видалена!)
- Department | Seniority | Teams | **\<Status\>** | Vacancies | Hires
- В IP section колонка статусу = "In Progress"
- В Plan section колонка статусу = "Plan"

### Sort state — окремий для кожної секції
```javascript
let _s3SortCol='h', _s3SortDir=-1, _s3deptVacs={};       // IP section
let _s3pSortCol='h', _s3pSortDir=-1, _s3pdeptVacs={};    // Plan section
function s3Sort(col){...; r3();}
function s3pSort(col){...; r3plan();}
```

### r3() — IP-only render
```javascript
function r3(){
  // Filter: parent is In progress OR has any active sub-task in In progress
  const _activeVacs=ALL_VACS.filter(v=>vacInStatus(v,'In progress'));
  const _activeST=ST.filter(s=>s.st!=='Hired');

  // Hires: count ONLY units matching 'In progress' (parent if IP + IP subs)
  const _vacHires=v=>{
    const subs=_activeST.filter(x=>x.pk===v.key);
    if(subs.length>0){
      const subsIp=subs.filter(x=>x.st==='In progress').length;
      const parentIp=v.st==='In progress'?1:0;
      return subsIp+parentIp;
    }
    return v.st==='In progress'?v.h:0;
  };

  const totalH=_activeVacs.reduce((s,v)=>s+_vacHires(v),0);
  // badge: `${_activeVacs.length} vacancies · ${totalH} hires`

  // Per-dept: only IP-matching count
  const entries=Object.entries(depts).map(([dept,vacs])=>({
    dept, vacs,
    ip:vacs.filter(v=>vacInStatus(v,'In progress')).length,
    h:vacs.reduce((s,v)=>s+_vacHires(v),0)
  }));

  // Expanded sub-task rows: ONLY In progress subs
  const subs3=ST.filter(s=>s.pk===v.key&&s.st==='In progress');
  // Vacancy row HIRES column: ${_vacHires(v)} (NOT v.h!)
}
```

### r3plan() — Plan-only mirror render
Симетрична до r3(), але з Plan фільтром:
```javascript
function r3plan(){
  const _planVacs=ALL_VACS.filter(v=>vacInStatus(v,'Plan'));
  const _activeST=ST.filter(s=>s.st!=='Hired');
  const _vacHires=v=>{
    const subs=_activeST.filter(x=>x.pk===v.key);
    if(subs.length>0){
      const subsPl=subs.filter(x=>x.st==='Plan').length;
      const parentPl=v.st==='Plan'?1:0;
      return subsPl+parentPl;
    }
    return v.st==='Plan'?v.h:0;
  };
  // Subs filter: ST.filter(s=>s.pk===v.key&&s.st==='Plan')
  // Status column: parent.st='Plan' shows badge, else "via sub" hint
}
```

### Sum-check
- IP section + Plan section = total Hires Needed
- Приклад: REC-228 (parent IP, sub REC-229 Plan) → 1 hire в IP + 1 hire в Plan = 2 total
- Бейдж IP: `41 vacancies · 77 hires` + Бейдж Plan: `1 vacancy · 1 hire` = 78 (= KPI Hires Needed)

### КРИТИЧНО — НЕ робити:
- ❌ НЕ показувати Plan subs в IP section (відфільтровувати через `s.st==='In progress'`)
- ❌ НЕ використовувати `${v.h}` в expanded vacancy row HIRES — використовувати `${_vacHires(v)}` для status-correct count
- ❌ НЕ повертати Distribution колонку (видалена за рішенням користувача)
- ❌ НЕ об'єднувати IP+Plan в одній секції з обома колонками (роздільність=ясність)

### Old single-section rendering reference (legacy, до 2026-05)

Раніше була одна секція з колонками Department | Seniority | Teams | In Progress | Plan | Vacancies | Hires | Distribution. Зараз заміна на dual sections.

### Таблиця — 8 колонок і sortable headers
```javascript
// Колонки: Department | Seniority | Teams | In Progress | Plan | Vacancies | Hires | Distribution
// Seniority — окремий стовпець (НЕ inline badge у назві), колір snColor[v.sn], НЕ сортується
// Teams — v.sb (subteam, другий рівень customfield_23547), НЕ сортується
// Dept rows: 2 порожні <td></td> для Seniority і Teams
// Vacancy rows: snHtml для Seniority, v.sb для Teams
const arw=(c)=>{
  const on=_s3SortCol===c||(_s3SortCol==='h'&&c==='dist');
  return on?(_s3SortDir===1?'▴':'▾'):'⇅';
};
const arwC=(c)=>{
  const on=_s3SortCol===c||(_s3SortCol==='h'&&c==='dist');
  return on?'#3b6ef5':'#c8d2e0';
};

// thead
`<th onclick="s3Sort('dept')" style="cursor:pointer;text-align:left">
  DEPARTMENT <span style="color:${arwC('dept')};font-size:9px">${arw('dept')}</span>
</th>
<th style="text-align:center">SENIORITY</th>   <!-- НЕ сортується -->
<th style="text-align:center">TEAMS</th>        <!-- v.sb; НЕ сортується -->
<th onclick="s3Sort('ip')" style="cursor:pointer;text-align:center">
  IN PROGRESS <span style="color:${arwC('ip')};font-size:9px">${arw('ip')}</span>
</th>
<th onclick="s3Sort('pl')" style="cursor:pointer;text-align:center">
  PLAN <span style="color:${arwC('pl')};font-size:9px">${arw('pl')}</span>
</th>
<th onclick="s3Sort('vac')" style="cursor:pointer;text-align:center">
  VACANCIES <span style="color:${arwC('vac')};font-size:9px">${arw('vac')}</span>
</th>
<th onclick="s3Sort('h')" style="cursor:pointer;text-align:center">
  HIRES <span style="color:${arwC('h')};font-size:9px">${arw('h')}</span>
</th>
<th onclick="s3Sort('dist')" style="cursor:pointer;text-align:left">
  DISTRIBUTION <span style="color:${arwC('dist')};font-size:9px">${arw('dist')}</span>
</th>`
```

### Department row (expandable) — 8 cols, Seniority і Teams — порожні
```javascript
const did=e.dept.replace(/\s+/g,'_');  // safe ID
const dh=e.h, pct=Math.round(dh/maxH*100);
tbody+=`<tr onclick="togDept3('${did}')" style="cursor:pointer">
  <td style="padding:10px 16px;font-size:13px;font-weight:600;color:#1e293b">
    <span id="arr3-${did}" style="color:#94a3b8;font-size:10px;margin-right:8px">+</span>
    ${e.dept}
  </td>
  <td></td>  <!-- Seniority — порожня для dept row -->
  <td></td>  <!-- Teams — порожня для dept row -->
  <td style="text-align:center;padding:10px;font-size:13px;font-weight:700;color:#3b6ef5">
    ${e.ip||'<span style="color:#94a3b8;font-weight:400">—</span>'}
  </td>
  <td style="text-align:center;padding:10px;font-size:13px;font-weight:700;color:#64748b">
    ${e.pl||'<span style="color:#94a3b8;font-weight:400">—</span>'}
  </td>
  <td style="text-align:center;padding:10px;font-size:13px;font-weight:600;color:#0f172a">
    ${e.vacs.length}
  </td>
  <td style="text-align:center;padding:10px;font-size:14px;font-weight:700;color:#0f172a">
    ${dh}
  </td>
  <td style="padding:10px 20px 10px 10px">
    <div style="background:#e2e8f0;border-radius:4px;height:8px;width:100%">
      <div style="background:#3b6ef5;border-radius:4px;height:8px;width:${pct}%"></div>
    </div>
  </td>
</tr>`;
```

### Expanded vacancy rows — 8 cols, Seniority і Teams заповнені
```javascript
// КРИТИЧНО: In progress badge → під IN PROGRESS колонкою; Plan badge → під PLAN колонкою
// _s3deptVacs[did] зберігати ДО forEach для togDept3
_s3deptVacs[did]=vacsSorted.map(v=>v.key);

vacsSorted.forEach(v=>{
  const vSn=v.sn?`<span style="font-size:11px;font-weight:700;color:${snColor[v.sn]}">${v.sn}</span>`:'<span style="color:#94a3b8">—</span>';
  const isIp=v.st==='In progress', isPl=v.st==='Plan';
  const subs3=ST.filter(s=>s.pk===v.key&&s.st!=='Hired');
  const togBtn3=subs3.length>0
    ?`<button id="s3tb-${v.key}" onclick="event.stopPropagation();togSubs3('${v.key}')"
        style="...">▶</button>`
    :'';
  tbody+=`<tr data-dept3="${did}" style="display:none;background:#f0f4ff;border-bottom:1px solid #e8eef8">
    <td style="padding:8px 16px 8px 36px;font-size:12px;white-space:nowrap">
      ${togBtn3}${jl(v.key)}<span style="color:#374151;font-weight:500;margin-left:8px;white-space:normal">${v.s}</span>
    </td>
    <td style="text-align:center;padding:8px 10px">${vSn}</td>
    <td style="text-align:center;padding:8px 10px;font-size:11px;color:#475569">${v.sb||'<span style="color:#94a3b8">—</span>'}</td>
    <td style="text-align:center;padding:8px 10px">${isIp?sb2(v.st):''}</td>
    <td style="text-align:center;padding:8px 10px">${isPl?sb2(v.st):''}</td>
    <td style="padding:8px 10px"></td>
    <td style="text-align:center;padding:8px 10px;font-size:12px;color:#64748b;font-weight:600">${v.h}</td>
    <td style="padding:8px 20px 8px 10px"></td>
  </tr>`;
  // Subtask rows — data-s3parent (НЕ data-dept3), hidden by default
  // Seniority: s.sn||v.sn; Teams: s.sb||v.sb
  subs3.forEach(s=>{
    const sSn=s.sn||v.sn;
    const sSnHtml=sSn?`<span style="font-size:11px;font-weight:700;color:${snColor[sSn]}">${sSn}</span>`:'<span style="color:#94a3b8">—</span>';
    tbody+=`<tr data-s3parent="${v.key}" style="display:none;background:#e8f0ff;border-bottom:1px solid #dde8f8">
      <td style="padding:6px 16px 6px 60px;font-size:11px;white-space:nowrap">
        ↳ ${jl(s.key)}<span style="color:#374151;font-weight:500;margin-left:8px;white-space:normal">${s.s}</span>
      </td>
      <td style="text-align:center;padding:6px 10px">${sSnHtml}</td>
      <td style="text-align:center;padding:6px 10px;font-size:11px;color:#475569">${s.sb||v.sb||'<span style="color:#94a3b8">—</span>'}</td>
      <td style="text-align:center;padding:6px 10px">${s.st==='In progress'?sb2(s.st):''}</td>
      <td style="text-align:center;padding:6px 10px">${s.st==='Plan'?sb2(s.st):''}</td>
      <td style="padding:6px 10px"></td>
      <td style="text-align:center;padding:6px 10px;font-size:11px;color:#64748b;font-weight:600">1</td>
      <td style="padding:6px 20px 6px 10px"></td>
    </tr>`;
  });
});
```

### Toggle функції
```javascript
// Dept toggle — при collapse також ховає відкриті subtask рядки
function togDept3(did){
  const rows=document.querySelectorAll(`[data-dept3="${did}"]`);
  const arr=document.getElementById('arr3-'+did);
  const hidden=rows[0]?.style.display==='none';
  rows.forEach(r=>r.style.display=hidden?'table-row':'none');
  if(arr)arr.textContent=hidden?'−':'+';
  // При collapse — ховаємо всі відкриті subtask рядки цього dept
  if(!hidden){
    (_s3deptVacs[did]||[]).forEach(key=>{
      document.querySelectorAll(`[data-s3parent="${key}"]`).forEach(r=>r.style.display='none');
      const btn=document.getElementById('s3tb-'+key);
      if(btn)btn.textContent='▶';
    });
  }
}

// Subtask toggle для окремої вакансії
function togSubs3(key){
  const rows=document.querySelectorAll(`[data-s3parent="${key}"]`);
  const btn=document.getElementById('s3tb-'+key);
  const hidden=rows[0]?.style.display==='none';
  rows.forEach(r=>r.style.display=hidden?'table-row':'none');
  if(btn)btn.textContent=hidden?'▼':'▶';
}
```

### Підсумковий рядок (8 cols — 2 порожні для Seniority і Teams)
```javascript
tfoot=`<tr style="background:#f8fafc;border-top:2px solid #e2e8f0;font-weight:700">
  <td style="padding:10px 16px;font-size:13px">Всього</td>
  <td></td>  <!-- Seniority -->
  <td></td>  <!-- Teams -->
  <td style="text-align:center;padding:10px;color:#3b6ef5">${entries.reduce((s,e)=>s+e.ip,0)}</td>
  <td style="text-align:center;padding:10px;color:#64748b">${entries.reduce((s,e)=>s+e.pl,0)}</td>
  <td style="text-align:center;padding:10px;color:#0f172a">${totalVacs}</td>
  <td style="text-align:center;padding:10px;color:#0f172a">${entries.reduce((s,e)=>s+e.h,0)}</td>
  <td style="padding:10px 20px 10px 10px"></td>
</tr>`;
```

**ПРАВИЛА Section 3:**
- ✅ Без tabs — один рядок на департамент, expandable по кліку
- ✅ `data-dept3="${did}"` атрибут на vacancy рядках (не CSS клас — уникаємо дефісів!)
- ✅ `did = e.dept.replace(/\s+/g,'_')` — safe ID без пробілів
- ✅ Seniority — окремий стовпець після Department; colored text `snColor[v.sn]`; dept і footer rows — порожні `<td></td>`; НЕ сортується
- ✅ Teams — окремий стовпець після Seniority; значення `v.sb` (subteam); subtask: `s.sb||v.sb`; dept і footer rows — порожні; НЕ сортується
- ✅ In progress badge → під IN PROGRESS колонкою (isIp); Plan badge → під PLAN колонкою (isPl)
- ✅ Subtask seniority: `s.sn||v.sn` (власний або від батька); Teams: `s.sb||v.sb`
- ✅ Distribution column сортує як Hires: `col==='dist'?'h':col` у s3Sort
- ✅ Sort arrows: `⇅` (неактивна), `▴`/`▾` (активна), колір `#3b6ef5` vs `#c8d2e0`
- ✅ `_s3SortCol`, `_s3SortDir`, `_s3deptVacs` — на модульному рівні (поза r3)
- ✅ dept default сортування: A→Z (dir=1); числові колонки: desc (dir=-1)
- ✅ `togDept3`, `togSubs3` визначати ДО r3 (або глобально)
- ✅ Subtask рядки: `data-s3parent="${v.key}"` (НЕ `data-dept3`!) + `display:none` за замовч.
- ✅ Toggle кнопка ▶/▼ тільки якщо `subs3.length > 0`; `event.stopPropagation()` щоб не розкривати dept
- ✅ `_s3deptVacs[did]` зберігає масив vacancy keys — для collapse subtasks при закритті dept
- ✅ При collapse dept (`togDept3`): ховати всі `data-s3parent` рядки і скидати ▶ кнопки
- ❌ НЕ використовувати `<div class="tab-bar" id="t3">` — видалено!
- ❌ НЕ додавати `v.t||'Інше'` fallback — вакансії без dept (`v.t === null`) пропускати повністю!

---

## Section 4: Roles by Days Open (Hiring Focus)

**ВАЖЛИВО**: секція перейменована з "30+ Day Open Roles" на "Roles by Days Open" (травень 2026). User-facing назва змінена, поведінка та сортування — без змін.

### Заголовок секції (HTML)
```html
<!-- Subtitle на другому рядку через <br>, щоб не переповнювався header -->
<h2>Roles by Days Open<br>
  <span style="color:#94a3b8;font-weight:400;font-size:11px">Hiring Focus · filter by Start date</span>
</h2>
```

### Фільтр inline в section-header (event.stopPropagation!)
```html
<!-- Фільтр в section-header, поряд з badge. stopPropagation — щоб не закривав секцію -->
<div onclick="event.stopPropagation()" style="display:flex;align-items:center;gap:6px;flex-shrink:0">
  <span style="font-size:11px;color:#94a3b8;white-space:nowrap">більше</span>
  <input type="number" id="di" value="30" min="1"
    style="width:46px;padding:3px 6px;border:1px solid #e2e8f0;border-radius:6px;font-size:12px;font-family:inherit;text-align:center;background:#fff">
  <span style="font-size:11px;color:#94a3b8">дн</span>
  <button onclick="r4()" style="padding:3px 10px;font-size:11px;background:#3b6ef5;color:#fff;border:none;border-radius:6px;cursor:pointer;font-family:inherit;font-weight:600">Apply</button>
</div>
<span class="sec-badge red" id="b4"></span>
```

### Badge CSS (великий, як S1/S2)
```css
#b4 { font-size: 13px; padding: 5px 16px; gap: 4px; display: inline-flex; align-items: center; }
#b4 .bnum { font-size: 17px; font-weight: 800; color: #b91c1c; line-height: 1; }
```

### Фільтр і render
```javascript
function r4(){
  const days=parseInt(document.getElementById('di').value)||30;  // default 30!
  let items=ALL_VACS.filter(v=>v.st==='In progress'&&v.sd)
    .map(v=>({...v,d:dag(v.sd)}))
    .filter(v=>v.d>=days);
  // Sort...
  document.getElementById('b4').innerHTML=
    `<span class="bnum">${items.length}</span> vacancies`;
  // ...
}
```

### Колонки Section 4
| ID | Label | Примітки |
|----|-------|----------|
| key | Key | toggle кнопка ▶ для вакансій з h≥2 |
| s | Vacancy | max-width:240px |
| pr | Priority | |
| sn | Seniority | |
| rec | Recruiter | |
| src | Sourcer | |
| sd | Start date | |
| dt | Dept / Team | |
| h | Hires | text-align:center |
| d | **Days** (НЕ "Днів відкрита"!) | text-align:center, числа БЕЗ суфіксу "д" |

### Days badge (числа без суфіксу!)
```javascript
// Без "д" — тільки число!
const badge=v.d>=45?`<span class="db45">${v.d}</span>`
           :v.d>=30?`<span class="db30">${v.d}</span>`
                   :`<span class="dbnorm">${v.d}</span>`;
```

```css
.db45 { background:#fef2f2; color:#991b1b; border-radius:5px; padding:2px 7px; font-size:11px; font-weight:700; border:1px solid #fecaca; }
.db30 { background:#fffbeb; color:#92400e; border-radius:5px; padding:2px 7px; font-size:11px; font-weight:700; border:1px solid #fde68a; }
.dbnorm { color:var(--text2); font-weight:600; font-size:13px; }
```

### Expandable subtasks (для h≥2)

За замовчуванням subtasks **скриті**. Toggle кнопка ▶/▼ в Key cell.

```javascript
// Toggle функція (визначити ДО r4!)
function togSubs4(key){
  const rows=document.querySelectorAll(`[data-s4parent="${key}"]`);
  const btn=document.getElementById('tgb4-'+key);
  const hidden=rows[0]?.style.display==='none';
  rows.forEach(r=>r.style.display=hidden?'table-row':'none');
  if(btn)btn.textContent=hidden?'▼':'▶';
}

// В rows4 map:
const subs=ST.filter(s=>s.pk===v.key&&s.st!=='Hired');
const hasToggle=v.h>=2&&subs.length>0;
const togBtn=hasToggle
  ?`<button id="tgb4-${v.key}" onclick="togSubs4('${v.key}')"
      style="background:none;border:1px solid #c8d2e0;border-radius:4px;cursor:pointer;font-size:9px;padding:1px 4px;color:#64748b;margin-right:4px;line-height:1">▶</button>`
  :'';

// Parent row:
const parentRow=`<tr>
  <td style="white-space:nowrap">${togBtn}${jl(v.key)}</td>
  ...
</tr>`;

// Sub-task rows (display:none за замовчуванням, data-s4parent для toggle):
const subRows=subs.map(s=>{
  const sdt=[s.t||v.t,s.sb||v.sb].filter(Boolean).join(' / ');
  const sPr=s.pr||v.pr;
  const sSn=s.sn||v.sn;
  const sSd=s.sd||v.sd;
  const sBadge=sSd?(()=>{const dd=dag(sSd);
    return dd>=45?`<span class="db45">${dd}</span>`
          :dd>=30?`<span class="db30">${dd}</span>`
                 :`<span class="dbnorm">${dd}</span>`;})():'<span class="dash-val">—</span>';
  return`<tr data-s4parent="${v.key}" style="display:none;background:#f5f8ff">
    <td style="padding-left:22px;font-size:12px;white-space:nowrap">↳ ${jl(s.key)}</td>
    <td style="font-size:11px">${s.s}</td>
    <td>${pb(sPr)}</td>
    <td>${sSnHtml}</td>
    <td style="font-size:11px">${fv(s.rec)}</td>
    <td style="font-size:11px">${fv(s.src)}</td>
    <td style="font-size:11px">${fv(sSd)}</td>
    <td style="font-size:11px">${fv(sdt)}</td>
    <td style="text-align:center"><b style="color:#0f172a">1</b></td>
    <td style="text-align:center">${sBadge}</td>
  </tr>`;
}).join('');
```

**ПРАВИЛА Section 4:**
- ✅ Default: 30 днів (не 21!)
- ✅ Фільтр по `v.sd` (Start date), НЕ по `v.cr` (created)
- ✅ Колонка "Days" (не "Днів відкрита"), числа без "д"
- ✅ Toggle subtasks (▶/▼) тільки для `h >= 2 && subs.length > 0`
- ✅ `data-s4parent` атрибут на subtask рядках (не CSS клас — уникаємо проблем з дефісами в ключах)
- ✅ Subtask успадковує: Priority, Seniority, Dept/Team від батька якщо власні null
- ✅ Subtask Days badge — рахувати від `s.sd || v.sd`
- ✅ Фільтр в section-header з `event.stopPropagation()`

---

## Section 5: Open Roles by Hiring Reason & Team

### Заголовок секції
```html
<h2>Open Roles by Hiring Reason &amp; Team</h2>
<span class="sec-badge orange" id="b5"></span>
```

### Badge — активні вакансії та hires
```javascript
// Підрахунок АКТИВНИХ hires: якщо є активні сабтаски → subs.length+1; інакше v.h
_s5activeSTs=ST.filter(s=>s.st!=='Hired');
const total=allIp.reduce((s,v)=>{
  const subs=_s5activeSTs.filter(x=>x.pk===v.key);
  return s+(subs.length>0?subs.length+1:v.h);
},0);
document.getElementById('b5').innerHTML=
  `<span class="bnum">${allIp.length}</span> vacancies &nbsp;·&nbsp; <span class="bnum">${total}</span> hires`;
```

### Badge CSS (великий, як S1/S2)
```css
#b5 { font-size: 13px; padding: 5px 16px; gap: 4px; display: inline-flex; align-items: center; }
#b5 .bnum { font-size: 17px; font-weight: 800; color: #b45309; line-height: 1; }
```

### Chart.js grouped bar chart

```javascript
let _s5chart=null, _s5ip=[], _s5allIp=[], _s5activeSTs=[];
function r5(){
  const allIp=_s5allIp=ALL_VACS.filter(v=>v.st==='In progress');
  _s5activeSTs=ST.filter(s=>s.st!=='Hired');

  // Departments — тільки ті що мають v.t (НЕ null); "Other" не додавати!
  const teamSet=new Set();
  allIp.forEach(v=>{if(v.t)teamSet.add(v.t);});
  const teams=[...teamSet].sort();

  // Причини
  const reasonCfg=[
    {key:'Extention',   label:'Extention',   bg:'#4ade80', hover:'#22c55e', border:'#16a34a'},
    {key:'Replacement', label:'Replacement', bg:'#f87171', hover:'#ef4444', border:'#dc2626'},
    {key:'Consultation',label:'Consultation',bg:'#60a5fa', hover:'#3b82f6', border:'#2563eb'},
    {key:'Не вказано',  label:'Other',       bg:'#94a3b8', hover:'#64748b', border:'#475569'},
  ];

  // Datasets рахують ВАКАНСІЇ (1 per parent position), НЕ hire slots!
  // _s5activeSTs використовується ТІЛЬКИ для popup expand — НЕ для підрахунку bars!
  _s5ip=allIp;
  const datasets=reasonCfg.map(rc=>{
    const data=teams.map(t=>allIp.filter(v=>(v.r||'Не вказано')===rc.key&&v.t===t).length);
    const hasData=data.some(d=>d>0);
    return hasData?{
      label:rc.label, data,
      backgroundColor:rc.bg, hoverBackgroundColor:rc.hover,
      borderColor:'transparent', borderWidth:0,
      borderRadius:7, borderSkipped:false,
    }:null;
  }).filter(Boolean);
```

### Chart options (візуальні покращення)
```javascript
options:{
  responsive:true, maintainAspectRatio:false,
  animation:{duration:500,easing:'easeOutQuart'},
  barPercentage:0.82, categoryPercentage:0.88,
  plugins:{
    legend:{
      position:'top', align:'center',  // 'center' — щоб всі items були видимі!
      labels:{font:{family:'Inter',size:12,weight:'500'}, padding:18,
              boxWidth:9, boxHeight:9, usePointStyle:true,
              pointStyle:'rectRounded', color:'#475569'}
    },
    tooltip:{
      backgroundColor:'#1e293b', titleColor:'#f8fafc', bodyColor:'#94a3b8',
      borderColor:'#334155', borderWidth:1, padding:{x:14,y:10}, cornerRadius:10,
      callbacks:{
        title:items=>`${items[0].label}`,
        label:item=>`  ${item.dataset.label}: ${item.raw}`,
        footer:()=>'Click to open →'
      },
      footerColor:'#60a5fa', footerFont:{size:10,style:'italic'}, footerMarginTop:6
    },
    datalabels:false
  },
  scales:{
    x:{grid:{display:false}, border:{display:false},
       ticks:{font:{family:'Inter',size:11,weight:'500'},color:'#64748b',maxRotation:25,minRotation:0}},
    y:{beginAtZero:true, border:{display:false,dash:[3,3]},
       grid:{color:'#f1f5f9',lineWidth:1},
       ticks:{font:{family:'Inter',size:11},color:'#94a3b8',stepSize:2,precision:0}}
  },
  interaction:{mode:'index',intersect:false},
  // onClick — 'nearest'+intersect:true щоб визначити ТОЧНИЙ bar (не тільки першй dataset)
  onClick(evt,elements,chart){
    const pts=chart.getElementsAtEventForMode(evt.native,'nearest',{intersect:true},true);
    if(!pts.length)return;
    const el=pts[0];
    const dept=chart.data.labels[el.index];
    const ds=chart.data.datasets[el.datasetIndex];
    const reasonLabel=ds.label;
    const reasonKey=reasonLabel==='Other'?'Не вказано':reasonLabel;
    // Фільтр по v.t===dept (НЕ v.t||'Other') — без fallback!
    const vacs=_s5allIp.filter(v=>v.t===dept&&(v.r||'Не вказано')===reasonKey);
    if(vacs.length)showS5Popup(dept,reasonLabel,reasonKey,vacs);
  }
},
// Plugins масив:
plugins:[
  // 1. Роздільники між департаментами
  {id:'deptSeparators', afterDraw(chart){
    const {ctx:c,chartArea:{top,bottom},scales:{x}}=chart;
    if(!x.ticks||x.ticks.length<2)return;
    c.save(); c.strokeStyle='rgba(203,213,225,0.7)'; c.lineWidth=1; c.setLineDash([]);
    x.ticks.forEach((_,i)=>{
      if(i===0)return;
      const x0=x.getPixelForTick(i-1), x1=x.getPixelForTick(i);
      const mid=(x0+x1)/2;
      c.beginPath(); c.moveTo(mid,top); c.lineTo(mid,bottom+8); c.stroke();
    });
    c.restore();
  }},
  // 2. Data labels — білі всередині великих bars, кольорові над маленькими
  {id:'datalabelsInline', afterDatasetsDraw(chart){
    const {ctx:c}=chart;
    chart.data.datasets.forEach((ds,di)=>{
      const meta=chart.getDatasetMeta(di);
      if(meta.hidden)return;
      meta.data.forEach((bar,i)=>{
        const v=ds.data[i]; if(!v)return;
        const props=bar.getProps(['x','y','base'],true);
        const barH=props.base-props.y;
        c.save(); c.font='bold 11px Inter,sans-serif'; c.textAlign='center';
        if(barH>22){
          c.fillStyle='rgba(255,255,255,0.92)'; c.textBaseline='middle';
          c.fillText(v,props.x,props.y+barH/2);
        } else {
          c.fillStyle=ds.backgroundColor||'#374151'; c.textBaseline='bottom';
          c.fillText(v,props.x,props.y-3);
        }
        c.restore();
      });
    });
  }}
]
```

### Popup (modal) — при кліку на bar

```html
<!-- Overlay + Popup перед </script> або перед <script> -->
<div id="s5overlay" onclick="closeS5Popup()" style="display:none;position:fixed;inset:0;background:rgba(15,23,42,0.45);z-index:1000;backdrop-filter:blur(2px)"></div>
<div id="s5popup" style="display:none;position:fixed;top:50%;left:50%;transform:translate(-50%,-50%);z-index:1001;background:#fff;border-radius:16px;box-shadow:0 20px 60px rgba(0,0,0,0.18);min-width:700px;max-width:90vw;max-height:80vh;overflow:hidden;flex-direction:column">
  <div style="padding:20px 24px 14px;border-bottom:1px solid #f1f5f9;display:flex;justify-content:space-between;align-items:flex-start">
    <div>
      <div id="s5popup-title" style="font-size:18px;font-weight:700;color:#0f172a"></div>
      <div id="s5popup-sub" style="font-size:13px;color:#64748b;margin-top:2px"></div>
    </div>
    <button onclick="closeS5Popup()" style="...">✕</button>
  </div>
  <div style="overflow-y:auto;padding:14px 20px 20px">
    <table class="tbl-compact" style="width:100%">
      <thead><tr id="s5popup-thead"></tr></thead>
      <tbody id="s5popup-tbody"></tbody>
    </table>
  </div>
</div>
```

### Popup columns
```javascript
const _s5popupCols=[
  {id:'key',lbl:'Key'},{id:'s',lbl:'Vacancy'},{id:'st',lbl:'Status'},
  {id:'pr',lbl:'Priority'},{id:'sn',lbl:'Seniority'},
  {id:'rec',lbl:'Recruiter'},{id:'src',lbl:'Sourcer'},
  {id:'h',lbl:'Hires',c:1}
];
```

### Popup — active hires і Status column

```javascript
function showS5Popup(dept,reasonLabel,reasonKey,vacs){
  // Рахувати АКТИВНІ hires: якщо є активні сабтаски → subs.length+1 (включно з батьком)
  _s5popupVacs=vacs.map(v=>{
    const activeSubs=_s5activeSTs.filter(s=>s.pk===v.key);
    return{...v, h: activeSubs.length>0 ? activeSubs.length+1 : v.h};
  });
  _s5popupSort={col:'h',dir:-1};
  document.getElementById('s5popup-title').textContent=`${reasonLabel} — ${dept}`;
  document.getElementById('s5popup-sub').textContent=
    `${vacs.length} вакансій · ${_s5popupVacs.reduce((s,v)=>s+(v.h||1),0)} hires`;
  renderS5PopupHeaders();
  document.getElementById('s5popup-tbody').innerHTML=renderS5PopupRows();
  document.getElementById('s5overlay').style.display='block';
  document.getElementById('s5popup').style.display='flex';
}
```

### Popup rows — Status column + expandable subtasks

```javascript
function renderS5PopupRows(){
  const {col,dir}=_s5popupSort;
  const sorted=[..._s5popupVacs].sort((a,b)=>{
    let av=a[col]??'', bv=b[col]??'';
    if(col==='pr'){av=pOrd[a.pr]??9;bv=pOrd[b.pr]??9;}
    return(av>bv?1:av<bv?-1:0)*dir;
  });
  return sorted.map(v=>{
    const subs=_s5activeSTs.filter(s=>s.pk===v.key);
    const hasToggle=subs.length>0;
    const togBtn=hasToggle?`<button id="s5tb-${v.key}" onclick="togS5Subs('${v.key}')"
      style="background:none;border:1px solid #c8d2e0;border-radius:4px;cursor:pointer;
             font-size:9px;padding:1px 4px;color:#64748b;margin-right:4px;line-height:1">▶</button>`:'';
    const snHtml=v.sn?`<span ...>${v.sn}</span>`:'—';

    const parentRow=`<tr>
      <td style="white-space:nowrap">${togBtn}${jl(v.key)}</td>
      <td style="font-size:12px;max-width:220px">${v.s}</td>
      <td>${sb2(v.st)}</td>        <!-- STATUS column: sb2() badge -->
      <td>${pb(v.pr)}</td><td>${snHtml}</td>
      <td style="font-size:11px">${fv(v.rec)}</td>
      <td style="font-size:11px">${fv(v.src)}</td>
      <td style="text-align:center"><b>${v.h}</b></td>
    </tr>`;

    const subRows=subs.map(s=>{
      return`<tr data-s5parent="${v.key}" style="display:none;background:#f5f8ff">
        <td style="padding-left:22px;font-size:12px;white-space:nowrap">↳ ${jl(s.key)}</td>
        <td style="font-size:11px">${s.s}</td>
        <td>${sb2(s.st)}</td>       <!-- STATUS column для subtask -->
        <td>${pb(s.pr||v.pr)}</td><td>...</td>
        <td style="font-size:11px">${fv(s.rec)}</td>
        <td style="font-size:11px">${fv(s.src)}</td>
        <td style="text-align:center"><b>1</b></td>
      </tr>`;
    }).join('');
    return parentRow+subRows;
  }).join('');
}
```

### Subtask toggle в popup
```javascript
function togS5Subs(key){
  const rows=document.querySelectorAll(`[data-s5parent="${key}"]`);
  const btn=document.getElementById('s5tb-'+key);
  const hidden=rows[0]?.style.display==='none';
  rows.forEach(r=>r.style.display=hidden?'table-row':'none');
  if(btn)btn.textContent=hidden?'▼':'▶';
}
```

**ПРАВИЛА Section 5:**
- ✅ Графік рахує ВАКАНСІЇ (1 per parent), НЕ hire slots — `_s5ip=allIp`
- ✅ `_s5activeSTs` (ST де `st!=='Hired'`) — тільки для popup expand, НЕ для bars
- ✅ Badge і popup hires: активні (`subs.length+1` якщо є активні сабтаски, інакше `v.h`)
- ✅ "Other" dept НЕ додавати до `teamSet` — тільки `if(v.t) teamSet.add(v.t)`
- ✅ `onClick` — `getElementsAtEventForMode(...,'nearest',{intersect:true},true)` для точного визначення bar
- ✅ `legend.align:'center'` — щоб всі items були видимі (не `'end'`!)
- ✅ `r` поле в ALL_VACS merge: `if(wp) return{...wp,rec,src,r:v.r||null}` — WP не має `r`!
- ✅ Status column в popup — `sb2(v.st)` для batьківських, `sb2(s.st)` для subtask рядків
- ✅ Колонка Status: `{id:'st',lbl:'Status'}` між Vacancy та Priority

---

## Файл дашборду

`/Users/olenapizniak/claude reports/reports/REC_recruitment_dashboard.html`

Preview server: `sprint-report` (port 8765, `~/.claude/launch.json`)

---

## Типові помилки — НЕ робити!

1. ❌ Фільтрувати по `v.cr` (created) — тільки по `v.sd` (Start date)
2. ❌ Брати Recruiter тільки з WP — використовувати RECR lookup (він авторитетний і повний)
3. ❌ `so` в OP = Sourcer — НЕ правда! `so` = HiringMgr, `re` = Sourcer
4. ❌ Хардкодити WS/WE — завжди динамічний розрахунок Пн–Нд
5. ❌ Фільтрувати тільки WP (неповний список) — використовувати ALL_VACS
6. ❌ Ігнорувати subtasks з `sd:null` — їх треба показувати завжди
7. ❌ CSS клас `st-REC-286` — дефіс не валідний в CSS, треба `st-REC_286`
8. ❌ `customfield_11753` для Story Points — це для PLAT, не REC
9. ❌ Порожні комірки в subtask рядках — всі поля мають бути заповнені (успадковувати від батька)
10. ❌ Сірий `color:#64748b` на назві вакансії subtask — тільки батьківський контекст-рядок в Section 2 може бути сірим
11. ❌ Не перевіряти ST масив — він має містити ВСІ активні subtasks; при оновленні даних завжди перефетчувати через JQL `issuetype = "Vacancy sub-task" AND statusCategory != Done`
12. ❌ Рекрутер батьківської позиції в Section 2 може бути null — робити fallback: `pRec = parent.rec || subs[0]?.rec || null`
13. ❌ Section 4 default 21 днів — НЕ ВІРНО! Default = **30 днів**
14. ❌ Section 4 колонка "Днів відкрита" — тепер називається **"Days"**, числа БЕЗ суфіксу "д"
15. ❌ Toggle subtasks через CSS клас `.s4sub-REC-123` — дефіс ламає querySelector. Завжди `data-s4parent="REC-123"` атрибут
16. ❌ `togSubs4` визначати після `r4` — треба ДО, інакше onclick в HTML не знайде функцію при першому рендері
17. ❌ Фільтр Section 4 в section-body — він має бути в section-header (inline з badge). Обов'язково `event.stopPropagation()` на wrapper div
18. ❌ ALL_VACS merge без `r:v.r||null` при WP override — WP не має поля `r`, тому вакансії з причиною в OP потраплять в "Не вказано" bar на графіку S5
19. ❌ Section 5 графік рахує hire slots (через subtasks) замість вакансій — НЕ ВІРНО! `_s5ip=allIp` (parent In progress positions), `_s5activeSTs` тільки для popup expand
20. ❌ Section 5 badge hires = sum of `v.h` (planned) — треба АКТИВНІ: `subs.length>0 ? subs.length+1 : v.h`
21. ❌ `teamSet.add(v.t||'Other')` — не додавати "Other"! Тільки `if(v.t) teamSet.add(v.t)` і `v.t===dept` у фільтрах (без `||'Other'` fallback)
22. ❌ Section 5 onClick `elements[0]` завжди повертає перший dataset — використовувати `getElementsAtEventForMode(...,'nearest',{intersect:true},true)`
23. ❌ `legend.align:'end'` — останній item легенди обрізається. Завжди використовувати `align:'center'`
24. ❌ Popup popup hires: `v.h` (planned) для батьківської — показувати активні: `activeSubs.length+1` (батько + активні сабтаски)

---

## Процедура оновлення даних (при наступному використанні)

1. **OP** — JQL: `project = REC AND issuetype = "Open position" AND statusCategory != Done ORDER BY key DESC`
   - fields: `summary, status, priority, customfield_11223, customfield_22876, customfield_13935, customfield_23510, customfield_23509, customfield_23545`
   - Витягнути через Bash+python3 (результат > 100k символів)
   - Оновити: OP array, SD lookup, SN lookup, RECR lookup, SRCR lookup

2. **ST** — JQL: `project = REC AND issuetype = "Vacancy sub-task" AND statusCategory != Done ORDER BY key DESC`
   - fields: `summary, status, customfield_11223, customfield_13935, customfield_23510, parent`
   - Повністю замінити ST масив

3. **HW** — JQL: `project = REC AND status = Hired AND statusCategory = Done AND updated >= "WEEK_START"`
   - Для кожної задачі: `getJiraIssue` з `expand=changelog` для factual close date
   - Оновити HW масив

4. **TASKS** — JQL: `project = REC AND issuetype = Task AND statusCategory != Done ORDER BY created DESC`
   - fields: `summary, status, priority, assignee, customfield_11223`
   - `asgn` = `assignee.displayName`, `sd` = `customfield_11223`
   - Замінити масив `const TASKS=[...]` повністю

5. **WP** — опційно, якщо є нові позиції поточного тижня яких немає в RECR

## Актуальність даних

Дані OP, WP, ST, HW, SD, SN, RECR, SRCR актуальні на: **2026-04-24**.
ТАSKS актуальні на: **2026-04-25**.
При наступному використанні — перевіряти нові вакансії через JQL і оновлювати масиви.

---

## Workload Overview Tab (додано 2026-04-25)

### Структура двох-табова

Дашборд має дві вкладки:
- **Workload Overview** — перша, активна за замовчуванням
- **Dashboard** — друга, містить всі попередні секції (S1–S5)

```html
<!-- tab bar HTML (вгорі .container) -->
<div class="main-tab-bar">
  <div class="main-tab active" data-view="workload" onclick="switchView('workload')">📋 Workload Overview</div>
  <div class="main-tab" data-view="dashboard" onclick="switchView('dashboard')">📊 Dashboard</div>
</div>
<div id="view-workload">...</div>
<div id="view-dashboard" style="display:none">...весь старий контент...</div>
```

```javascript
let _dashInit=false;
function switchView(view){
  document.getElementById('view-workload').style.display=view==='workload'?'':'none';
  document.getElementById('view-dashboard').style.display=view==='dashboard'?'':'none';
  document.querySelectorAll('.main-tab').forEach(t=>t.classList.toggle('active',t.dataset.view===view));
  // Lazy chart init — Charts.js ламається якщо canvas в hidden div
  if(view==='dashboard'&&!_dashInit){_dashInit=true;rChartHires();rChartOpened();}
}
```

### Дані: TEAM_ALL, TASKS

```javascript
const TEAM_ALL=[
  'Alina Muravchyk','Anastasiia Hodyna','Anastasiia Melnyk','Anastasiia Prylutska',
  'Anastasiia Shapovalenko','Darina Lavrenko','Kateryna Yaremenko','Inna Patsora',
  'Nadiia Brusova','Mariia Salabai','Polina Serdiuk','Violetta Strelchenko',
  'Veronika Khovrina','Victoria Kotenko','Yaroslava Bondarchuk','Yelyzaveta Yakovlieva'
];

// Task issues (issuetype=Task, statusCategory != Done) — актуальні на 2026-04-25
// JQL: project = REC AND issuetype = Task AND statusCategory != Done ORDER BY created DESC
// fields: summary, status, priority, assignee, customfield_11223
const TASKS=[
  {key:"REC-276",s:"Допомога в редагуванні курсу LMS",st:"In progress",pr:"Medium",asgn:"Veronika Khovrina",sd:"2026-04-21"},
  {key:"REC-235",s:"Рісьорч ATS систем",st:"In progress",pr:"High",asgn:"Nadiia Brusova",sd:"2026-04-06"},
  {key:"REC-234",s:"Організація QA Hiring Event",st:"In progress",pr:"High",asgn:"Nadiia Brusova",sd:"2026-04-02"},
  {key:"REC-233",s:"Актуалізація шаблонів оферів",st:"In progress",pr:"Medium",asgn:"Nadiia Brusova",sd:null},
  {key:"REC-232",s:"Дослідження AI інструментів для сорсингу та ректурингу",st:"In progress",pr:"High",asgn:"Nadiia Brusova",sd:"2026-03-19"},
  {key:"REC-225",s:"Уніфікація назв позицій та команд в таблиці Recruitment Status",st:"In progress",pr:"Medium",asgn:"Nadiia Brusova",sd:null},
  {key:"REC-224",s:"Систематизація інформації про команди",st:"In progress",pr:"Medium",asgn:"Nadiia Brusova",sd:null},
  {key:"REC-223",s:"Організація виходів штатних співробітників",st:"In progress",pr:"Medium",asgn:"Nadiia Brusova",sd:null},
  {key:"REC-149",s:"TASK: Create Jira Project",st:"In progress",pr:"High",asgn:"Yaroslava Bondarchuk",sd:"2026-03-27"},
];
```

**TASKS особливості:**
- Визначається `assignee.displayName`, НЕ `customfield_13935` (Recruiter) — Tasks не мають recruiter поля
- `sd` = `customfield_11223` (Start date)
- В `rWorkload` для Task: `{...t, _role:'Task', h:0, sn:null, t:null, sb:null}`

### rWorkload() — основна функція

```javascript
function rWorkload(){
  const activeVacs=ALL_VACS.filter(v=>v.st!=='Hired');
  const activeST=ST.filter(s=>s.st!=='Hired');

  const members=TEAM_ALL.map(name=>{
    // recVacs: RECR lookup авторитетний; WP fallback для Plan-вакансій без RECR
    const recVacs=activeVacs.filter(v=>v.rec===name||(v.rec==null&&WP.find(w=>w.key===v.key)?.rec===name));
    const srcVacs=activeVacs.filter(v=>v.src===name&&v.rec!==name&&!recVacs.some(r=>r.key===v.key));
    const taskItems=TASKS.filter(t=>t.asgn===name).map(t=>({...t,_role:'Task',h:0,sn:null,t:null,sb:null}));
    const allVacs=[...recVacs.map(v=>({...v,_role:'Recruiter'})),...srcVacs.map(v=>({...v,_role:'Sourcer'}))];

    // Active hires: across ALL vacancies where person is assigned (rec + src roles)
    // NOTE: sourcer workload counts too — use allVacs, NOT recVacs
    const hiresTotal=allVacs.reduce((s,v)=>{
      const activeSubs=activeST.filter(x=>x.pk===v.key);
      return s+(activeSubs.length>0?activeSubs.length+1:v.h);
    },0);
    const highCount=recVacs.filter(v=>v.pr==='High').length;
    const seniorCount=recVacs.filter(v=>['Senior','Lead','Expert'].includes(v.sn)).length;
    const maxDays=recVacs.filter(v=>v.sd).reduce((m,v)=>Math.max(m,dag(v.sd)),0);
    return{name,recVacs,srcVacs,allVacs,taskItems,hires:hiresTotal,highCount,seniorCount,maxDays};
  });
  // ...
}
```

**Ключові правила rWorkload:**
- `hasVacs = m.allVacs.length + m.taskItems.length > 0` — треба враховувати tasks для expandability
- `if(!hasVacs) return;` — пропускати порожніх членів після фільтру, НЕ рендерити рядок
- `load = m.hires + m.taskItems.length` — workload bar і thresholds базуються на load, НЕ тільки hires
- `maxLoad = Math.max(...members.map(m=>m.hires+m.taskItems.length), 1)` — для масштабу бару
- Thresholds: `isOvld = load > 20`, `isWarn = !isOvld && load > 8`
- HIRES колонка відображає `m.hires` (active hires з allVacs = rec+src), НЕ tasks
- TASKS колонка відображає `m.taskItems.length`
- **totalHires у badge**: НЕ сумувати m.hires по членах (double-count). Рахувати унікально по ALL_VACS:
  ```javascript
  const _allActiveVacs=ALL_VACS.filter(v=>v.st!=='Hired');
  const _allActiveST=ST.filter(s=>s.st!=='Hired');
  const totalHires=_allActiveVacs.reduce((s,v)=>{
    const subs=_allActiveST.filter(x=>x.pk===v.key);
    return s+(subs.length>0?subs.length+1:v.h);
  },0);
  ```
- **members.sort() aE**: `const aE=!a.allVacs.length&&!a.taskItems.length` (НЕ `!a.recVacs.length`)
- **members.sort() explicit cases**: включати `hires` та `wl` явно, не тільки default

### КОНВЕНЦІЯ KPI cards (Open Vacancies tab)

**ПОТОЧНИЙ STATE: 3 картки** (раніше було 4, IN PROGRESS видалена бо дублювала Active):

```html
<div class="kpi-card blue"><div class="kpi-icon">⚡</div><div class="kpi-num" id="kn-av">—</div><div class="kpi-label">Active Vacancies</div></div>
<div class="kpi-card blue"><div class="kpi-icon">📌</div><div class="kpi-num" id="kn-plan">—</div><div class="kpi-label">Plan</div></div>
<div class="kpi-card orange"><div class="kpi-icon">🎯</div><div class="kpi-num" id="kn-hn">—</div><div class="kpi-label">Hires Needed</div></div>
```

**Семантика**:
- **Active Vacancies** = `OP.filter(v=>vacInStatus(v,'In progress')).length` — кількість позицій у статусі In Progress (parent або через sub).
- **Plan** = `OP.filter(v=>vacInStatus(v,'Plan')).length` — кількість позицій у Plan (parent або через sub).
- **Hires Needed** = total slots: parent + active subs для активних (IP+Plan) позицій. **НЕ просто сума `v.h`.**

```javascript
function rKPI(){
  document.getElementById('kn-av').textContent=OP.filter(v=>vacInStatus(v,'In progress')).length;
  document.getElementById('kn-plan').textContent=OP.filter(v=>vacInStatus(v,'Plan')).length;
  const _activeST=ST.filter(s=>s.st!=='Hired');
  const _activeOPs=OP.filter(v=>vacInStatus(v,'In progress')||vacInStatus(v,'Plan'));
  document.getElementById('kn-hn').textContent=_activeOPs.reduce((s,v)=>{
    const subs=_activeST.filter(x=>x.pk===v.key);
    return s+(subs.length>0?subs.length+1:v.h);
  },0);
}
```

### КОНВЕНЦІЯ КОНСИСТЕНТНОСТІ: всі counts по дашборду

Усі частини дашборду МАЮТЬ показувати однакові числа для активних вакансій:
- Workload-Active badge `41 vacancies · 78 hires · 8 tasks`
- KPI: `Active=41, Plan=1, Hires Needed=78`
- S5 'Open Vacancies per Department' badge: `41 vacancies · 78 hires`

**Спільні правила**:
1. **Vacancies count** — унікальні parent vacancies, не сума per-member (інакше rec+src дає double-count). Використовувати `_allActiveVacs.length` або `ALL_VACS.filter(v=>vacInStatus(v,'In progress')||vacInStatus(v,'Plan')).length`.
2. **Hires count** — сума slots: для кожної активної vacancy `subs.length+1` (якщо є subs) інакше `v.h`. Це формула в `rWorkload` totalHires; маємо її дублювати в `rKPI` і `r3` (S5 badge + per-dept).
3. **Виключати Canceled** — `vacInStatus(v,'In progress')||vacInStatus(v,'Plan')` фільтр (НЕ просто `ALL_VACS.length` без фільтра).

### КОНВЕНЦІЯ СТАТУС-ФІЛЬТРА: parent + sub-tasks

**КРИТИЧНО:** Vacancy може мати кілька статусів одночасно:
- Parent (з OP/WP) має статус `In progress` / `Plan` / `Canceled` / `Hired`
- Sub-tasks (з ST array) мають свої статуси, які можуть **відрізнятися** від parent

**Реальний приклад**: REC-228 parent='In progress', sub-task REC-229='Plan'. Jira board показує REC-229 в колонці **Plan**. Якщо фільтр вибирає Plan, користувач очікує побачити REC-228 (бо в неї є Plan sub).

**Глобальний хелпер** (визначений у script section, доступний всім):
```javascript
function vacInStatus(v, status){
  if(v.st===status) return true;
  return ST.some(s=>s.pk===v.key && s.st!=='Hired' && s.st===status);
}
```

**Де ОБОВ'ЯЗКОВО використовувати** (замість `v.st==='Plan'` / `v.st==='In progress'`):
1. **KPI cards** (`rKPI`):
   ```javascript
   document.getElementById('kn-plan').textContent=OP.filter(v=>vacInStatus(v,'Plan')).length;
   document.getElementById('kn-ip').textContent=OP.filter(v=>vacInStatus(v,'In progress')).length;
   ```
2. **S5 Open Vacancies per Department** (per-dept ip/pl counts і footer total):
   ```javascript
   ip:vacs.filter(v=>vacInStatus(v,'In progress')).length,
   pl:vacs.filter(v=>vacInStatus(v,'Plan')).length,
   ```
3. **rWorkload status filter** (через локальну `_vacMatchesSt`, бо там Set, але та сама логіка):
   ```javascript
   const _vacMatchesSt=v=>{
     if(_wlFilterSt.has(v.st)) return true;
     return activeST.some(s=>s.pk===v.key && _wlFilterSt.has(s.st));
   };
   const recVacs=activeVacs.filter(v=>(...) && _vacMatchesSt(v));
   const srcVacs=activeVacs.filter(v=>(...) && _vacMatchesSt(v));
   const _allActiveVacs=ALL_VACS.filter(v=>v.st!=='Hired' && _vacMatchesSt(v));  // for totalHires
   ```

   **КРИТИЧНО для hires count**: коли parent потрапляє у `allVacs` лише через sub (parent='In progress' пройшов Plan-фільтр через Plan sub), сумарний hires НЕ повинен включати parent+всі subs автоматично. Потрібно рахувати тільки юніти, що відповідають фільтру:

   ```javascript
   // Per-member m.hires
   const hiresTotal=allVacs.reduce((s,v)=>{
     const activeSubs=activeST.filter(x=>x.pk===v.key);
     if(activeSubs.length>0){
       const subsMatching=activeSubs.filter(x=>_wlFilterSt.has(x.st)).length;
       const parentMatching=_wlFilterSt.has(v.st)?1:0;
       return s+subsMatching+parentMatching;
     }
     return s+(_wlFilterSt.has(v.st)?v.h:0);
   },0);

   // Same logic for global totalHires (badge у section-header)
   const totalHires=_allActiveVacs.reduce((s,v)=>{
     const subs=_allActiveST.filter(x=>x.pk===v.key);
     if(subs.length>0){
       const subsMatching=subs.filter(x=>_wlFilterSt.has(x.st)).length;
       const parentMatching=_wlFilterSt.has(v.st)?1:0;
       return s+subsMatching+parentMatching;
     }
     return s+(_wlFilterSt.has(v.st)?v.h:0);
   },0);
   ```

   **Приклад REC-228** (parent='In progress' h=2, sub REC-229='Plan'):
   - Plan only filter → `0 (parent IP not in filter) + 1 (sub Plan in filter)` = **1 hire** ✓
   - In progress only → `1 (parent IP in filter) + 0 (sub Plan not in filter)` = **1 hire** ✓
   - Both checked → `1 + 1` = **2 hires** ✓ (=sum of IP-only + Plan-only, без double-count)

   ❌ **Стара (помилкова) формула** — `subs.length+1` — давала 2 hires незалежно від фільтра, що було inflated.

4. **Tasks status filter** (TASKS не мають sub, тільки прямий статус):
   ```javascript
   const taskItems=...TASKS.filter(t=>t.asgn===name && _wlFilterSt.has(t.st))...;
   ```

**Де НЕ застосовувати**:
- Per-vacancy expanded row у S5 (parent row): IP/PL колонки показують саме parent's own status (sub-tasks мають свої окремі рядки) — там треба `v.st==='In progress'` як було.
- r5 (30+ Day Open Roles): міряє lifecycle parent vacancy, sub-tasks не мають окремої дати.
- Sub-task row rendering: у sub-row завжди показуємо її власний `s.st`.

**Чому це важливо**: без цього хелпера, parent з Plan sub-task пропадає з Plan KPI/фільтра і не видно у Jira-flow контексті.

### КОНВЕНЦІЯ TODAY + dag(): динамічно і timezone-safe

**КРИТИЧНО:** не хардкодити `TODAY=new Date('2026-XX-XX')` — застаріватиме і даватиме неправильні Days Open (включно з від'ємними).

**Правильна реалізація** (на самому початку script section, після `const J=...`):

```javascript
// TODAY = today at local midnight (auto-refresh on every page load)
const TODAY=(()=>{const t=new Date();return new Date(t.getFullYear(),t.getMonth(),t.getDate());})();

// Calendar-day diff: TODAY (local) − дата 'YYYY-MM-DD' (parsed as LOCAL).
function dag(d){
  if(!d) return null;
  const parts=String(d).split('-').map(Number);
  const sd=new Date(parts[0],parts[1]-1,parts[2]);
  return Math.floor((TODAY-sd)/86400000);
}
```

**Чому local parsing**: `new Date('2026-04-30')` інтерпретує як **UTC midnight**, а TODAY — як **local midnight**. Для користувача в UTC+3 (Kyiv) це дає разрив у ~3 год → `Math.floor` округлює донизу → off-by-one день.

**Реальний баг**: REC-40 sd=2026-04-30, today=2026-05-05. До фікса показувало `-6` днів (бо TODAY був хардкодом '2026-04-24'); після фікса dynamicTODAY+local parsing → правильно `5` днів.

**Anti-patterns** (НЕ робити):
```javascript
❌ const TODAY=new Date('2026-04-24');                     // хардкод — застаріє
❌ function dag(d){return Math.floor((TODAY-new Date(d))/(864e5));}  // UTC vs local TZ offset
❌ Math.round(...)                                          // round дає неправильні значення на pivot
```

**Усі місця, де dag() використовується**: Workload-Active (DAYS OPEN колонка, maxDays для сорту, vDays/sDays для expanded rows), r4 (30+ Day Open Roles), Hiring Focus row badges. Усі автоматично коректні після фікса.

### КОНВЕНЦІЯ ПОРЯДКУ В BADGE: vacancies → hires → tasks

**ЗАВЖДИ** в усіх sec-badge з 3 числами використовувати порядок: **vacancies · hires · tasks**.
Це стосується ВСІХ табів (Workload, Open Vacancies, Closed Vacancies) і всіх блоків.

```javascript
// ✅ ПРАВИЛЬНО
document.getElementById('bw').innerHTML=
  `<span class="bnum">${totalVacs}</span> vacancies &nbsp;·&nbsp; ` +
  `<span class="bnum">${totalHires}</span> hires &nbsp;·&nbsp; ` +
  `<span class="bnum">${totalTasks}</span> tasks`;

// ❌ НЕПРАВИЛЬНО — tasks не може йти між vacancies і hires
//   `${vacs} vacancies · ${tasks} tasks · ${hires} hires`
```

Якщо в badge тільки 2 значення — порядок: **vacancies · hires** (tasks опускається). Hires завжди стоїть зліва від tasks.

### AVG TTF / AVG TTH overview cards у Workload табі

Контейнер `#wl-tt-overview` (між Team Load KPI і Workload-Active секцією) рендерить дві картки:
- **AVG TTF** — Time to Fill, дні від відкриття до офер, по рекрутерах
- **AVG TTH** — Time to Hire, дні від першого контакту, по рекрутерах

Render-функція: `rWorkloadOverview()` (виводить горизонтальні bar-rows з ttfStats і tthStats).

**ПОТОЧНИЙ СТАН: cховано через `display:none`.** Користувач попросив тимчасово приховати ці картки бо вони "не дуже актуальні" (станом на 2026-05). Код залишений на місці.

**Як повернути назад**: у HTML на місці `<div id="wl-tt-overview" style="display:none;margin:16px 0"></div>` прибрати `display:none;`.

```html
<!-- сховано -->
<div id="wl-tt-overview" style="display:none;margin:16px 0"></div>

<!-- активно -->
<div id="wl-tt-overview" style="margin:16px 0"></div>
```

Render-функція (`rWorkloadOverview`) продовжує виконуватись і заповнювати DOM — це нормально, оскільки контейнер просто схований через CSS. Не видаляти render-функцію.

### Charts "Opened This Week" + "Hires This Week" (схована)

У табі **Open Vacancies**, одразу після KPI cards, дві cv-card картки поряд (через `<div class="cv-row">`):
- **Opened This Week** — `#chart-opened` + `#opened-total` + period filter (`opened-from`/`opened-to` + chips). Render: `rChartOpened(from,to)`. Дані: vacancies opened by Start date.
- **Hires This Week** — `#chart-hires` + `#hires-total` + period filter (`hires-from`/`hires-to` + chips). Render: `rChartHires(from,to)`. Дані: hires by Factual close date.

**ПОТОЧНИЙ СТАН: схована через `style="display:none"` на root `<div class="cv-row">`.** Користувач попросив тимчасово приховати (станом на 2026-05). Render-функції `rChartOpened`/`rChartHires` продовжують виконуватись.

**Як повернути назад**: прибрати `style="display:none"` з кореневої `<div class="cv-row">` що містить обидва графіки:

```html
<!-- сховано -->
<div class="cv-row" style="display:none">
  <div class="cv-card">... Opened This Week (chart-opened, opened-from/to) ...</div>
  <div class="cv-card">... Hires This Week (chart-hires, hires-from/to) ...</div>
</div>

<!-- активно -->
<div class="cv-row">
  <div class="cv-card">... Opened This Week ...</div>
  <div class="cv-card">... Hires This Week ...</div>
</div>
```

Render-функції не видаляються. Тільки inline-style на корневому div.

### Vacancy Dynamics — All Time / Period card (з period filter)

Друга з двох cv-card-ок у блоці Vacancy Dynamics (поряд з "Current vs Previous Week"). Має period filter на 5 режимів: All time / Month / Quarter / Year / Custom.

**HTML**:
```html
<div class="cv-card">
  <div class="cv-card-title">🌐 All Time / Period</div>
  <div class="cv-card-sub" id="cv-at-sub">Cumulative since project start</div>
  <div class="dp-chips">
    <button class="dp-chip cv-at-chip active" data-mode="all" onclick="cvSetAllTime('all')">All time</button>
    <button class="dp-chip cv-at-chip" data-mode="month" onclick="cvSetAllTime('month')">Month</button>
    <button class="dp-chip cv-at-chip" data-mode="quarter" onclick="cvSetAllTime('quarter')">Quarter</button>
    <button class="dp-chip cv-at-chip" data-mode="year" onclick="cvSetAllTime('year')">Year</button>
  </div>
  <input type="date" id="cv-at-from"> — <input type="date" id="cv-at-to">
  <button onclick="cvSetAllTime('custom')">Apply</button>
  <div id="cv-alltime-block"></div>  <!-- 2 columns: Open vs Hired -->
</div>
```

**State**: `let _cvAtMode='all', _cvAtFrom=null, _cvAtTo=null;`

**cvSetAllTime(mode)**: `all`/`month`/`quarter`/`year` → presets обчислюють from/to, `custom` → читає inputs. Updates active chip class, calls rCVDynamics().

**Render логіка в rCVDynamics()**:
- `mode='all'` → state-snapshot: `Currently Open` count vs `Hired (all time)` count, sub="Cumulative since project start"
- Інакше → flow-based в обраному періоді: `Opened` (cr||sd in range) vs `Hired` (hd||fcd in range), sub `${labelMap[mode]}: ${from} → ${to}`

**ВАЖЛИВО — НЕ показувати** "Hired ratio" + "Total tracked" stats line — користувач сказав видалити (травень 2026), бо ratio в period mode = частка hire-подій від усіх подій (некорисне insight).

```javascript
// ✅ Поточна структура — тільки 2 картки
document.getElementById('cv-alltime-block').innerHTML=`
  <div class="cv-cmpr-grid">
    <div class="cv-cmpr-side">${openedCount} ${openedLbl}</div>
    <div class="cv-cmpr-vs">vs</div>
    <div class="cv-cmpr-side">${hiredCount} ${hiredLbl}</div>
  </div>`;
// ❌ НЕ додавати: <div>Hired ratio: X% · Total tracked: N</div>
```

### Weekly trend chart (схований)

У табі **Closed Vacancies → Vacancy Dynamics** після пари cv-card блоків (Current vs Previous Week + All Time/Period) є cv-card з графіком "Weekly trend (last 12 weeks)" — bar chart `#cv-trend-chart` з кількістю opened та hired за останні 12 тижнів. Render у `rCVDynamics()` створює `_cvCharts.trend`.

**ПОТОЧНИЙ СТАН: схований через `style="display:none"` на root `<div class="cv-card">`.** Користувач попросив тимчасово приховати (станом на 2026-05). Render продовжує виконуватись (Chart.js малює canvas) — нормально, контейнер просто схований.

**Як повернути назад**: прибрати `style="display:none"` з кореневої `<div class="cv-card">`:

```html
<!-- сховано -->
<div class="cv-card" style="display:none;margin-top:0">
  <div class="cv-card-title">📈 Weekly trend (last 12 weeks)</div>
  <div class="cv-card-sub">Bars: opened ... and hired ... per week</div>
  <div class="cv-canvas-wrap" style="height:220px"><canvas id="cv-trend-chart"></canvas></div>
</div>

<!-- активно -->
<div class="cv-card" style="margin-top:0">
  <div class="cv-card-title">📈 Weekly trend (last 12 weeks)</div>
  ...
</div>
```

Render-функція `rCVDynamics()` НЕ видаляється (вона також рендерить All Time / Current vs Previous Week блоки).

### Avg TTF / Avg TTH by Department (Closed Vacancies tab)

Дві картки поряд у табі Closed Vacancies (під Vacancy Dynamics): horizontal bar charts з середнім часом по департаментах.

**Семантика метрик** (з полів CV array, заповнюється з Jira):
- **TTF** (Time to Fill) = `closeDate(v) − v.sd`, де:
  - `closeDate = v.fcd || v.hd` (Factual close date OR transition-to-Hired date)
  - `v.sd` = Start date вакансії (`customfield_11223`)
- **TTH** (Time to Hire) = `closeDate(v) − v.fcd_c`, де:
  - `v.fcd_c` = First contact date (`customfield_23407`)

**Render-функції** (`rCVTTF`, `rCVTTH`):
```javascript
function rCVTTF(){
  const byDept={};
  CV.filter(v=>v.t&&closeDate(v)&&v.sd).forEach(v=>{
    if(!byDept[v.t])byDept[v.t]=[];
    byDept[v.t].push(diffDays(closeDate(v),v.sd));
  });
  const entries=Object.entries(byDept).map(([d,arr])=>({d,avg:cvAvg(arr),n:arr.length}))
    .filter(e=>e.avg!=null).sort((a,b)=>b.avg-a.avg);
  // Overall avg = average of ALL individual TTFs (NOT average of dept averages)
  const overallAvg=Math.round(cvAvg(entries.flatMap(e=>byDept[e.d]))||0);
  document.getElementById('bcv-ttf').textContent=`Overall avg ${overallAvg}d · ${entries.length} depts`;
  // ... Chart.js horizontal bar with labels: "${days}d (${n})"
}

function rCVTTH(){
  // Same pattern, but filter requires fcd_c set; uses closeDate − fcd_c
  CV.filter(v=>v.t&&closeDate(v)&&v.fcd_c).forEach(v=>{...});
}
```

**Важливо**:
- TTF включає вакансії що мають `closeDate` AND `v.sd` — пропускає ті де відсутнє щось одне
- TTH включає вакансії з `fcd_c` заповненим — менше items (recruiters часто не заповнюють First contact date), тому badge показує `based on N hires`
- **Overall avg** обчислюється як середнє по ВСІХ окремих TTF днях (`flatMap`), НЕ як середнє по dept averages — інакше було б усереднення усереднень
- Сортування по `avg` desc — дашборд починається з найдовших, найшвидші внизу
- Sub-task TTF використовує parent's `sd` (sub успадковує) — це бажана поведінка, бо vacancy lifecycle починається з parent's open date

**Перевірка коректності** (на даних 2026-05):
| Dept | n | avg | Verified |
|------|---|-----|----------|
| Marketing | 17 | 37d | sum=628 / 17=36.9 ✓ |
| Content | 2 | 81d | (135+26)/2=80.5 ✓ |
| Overall TTF | 31 | 41d | sum=1264 / 31=40.77 ✓ |
| Overall TTH | 10 | 34d | sum=336 / 10=33.6 ✓ |

### Block 3: Closed Vacancies by Department (vertical bars per dept + click-to-popup)

**Поточний дизайн (травень 2026):** один вертикальний бар per department, sorted desc by hire count, цифри на барах, клік на бар → popup зі списком вакансій.

**HTML структура header**:
```html
<h2>Closed Vacancies by Department</h2>
<span class="sec-badge" id="bcv-cnt"></span>
<!-- Mode buttons (period presets) -->
<div class="cv-mode-bar" id="cv-cnt-mode">
  <button data-mode="all" class="active" onclick="cvSetMode('all')">All time</button>
  <button data-mode="month" onclick="cvSetMode('month')">Month</button>
  <button data-mode="quarter" onclick="cvSetMode('quarter')">Quarter</button>
  <button data-mode="year" onclick="cvSetMode('year')">Year</button>
</div>
<!-- Custom range -->
<input type="date" id="cv-cnt-from"> — <input type="date" id="cv-cnt-to">
<button onclick="rCVClosedCount()">Apply</button>
<button onclick="cvResetCntPeriod()">Reset</button>
<!-- Видалено: This week/Last week/This month/Last month chips (mode presets вище покривають) -->
```

**State**:
```javascript
let _cvCntMode='all';  // default — НЕ 'month'
let _cvCntFrom=null, _cvCntTo=null;
let _cvCntDeptVacs={};  // for popup lookup
```

**cvSetMode(m)**: для preset (all/month/quarter/year) обчислює `_cvCntFrom`/`_cvCntTo` від current date і заповнює inputs. Для 'custom' через Apply rCVClosedCount читає inputs.

**rCVClosedCount()**:
```javascript
function rCVClosedCount(){
  // detect custom mode if user changed inputs
  ...
  const items=CV.filter(v=>closeDate(v)&&v.t).filter(v=>cvInRange(closeDate(v),_cvCntFrom,_cvCntTo));
  const byDept={}; items.forEach(v=>{...});
  _cvCntDeptVacs=byDept;
  const entries=...sort((a,b)=>b.n-a.n);  // desc by count
  // Single dataset: vertical bars
  // onClick handler → showCVDeptPopup(dept, _cvCntDeptVacs[dept])
}
```

**Click handler** + popup: `showCVDeptPopup(dept, vacs)` — реюзить s5popup DOM (overlay + popup + table). Replaces table.innerHTML; **завжди залишає `id="s5popup-tbody"`** на новому tbody щоб інші popup-и працювали.

### Block 5: Hiring Sources (filter dropdowns + insights + click-to-popup)

**Поточний дизайн (травень 2026):**
- 3 insight-картки вгорі (light theme, white bg)
- Department + Seniority dropdowns (повний список) + Reset
- Single bar per source, sorted desc, colors з палітри
- Click → popup зі списком hires

**HTML header (без toggle By Dept/By Sn — видалено)**:
```html
<h2>Hiring Sources</h2>
<select id="cv-src-dept"><option value="">All</option>...</select>
<select id="cv-src-sn"><option value="">All</option>...</select>
<button onclick="...">Reset</button>
```

**HTML body**:
```html
<div style="font-size:13px;color:#0f172a;font-weight:600;margin-bottom:10px">Інсайти</div>
<div id="cv-src-insights" style="display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-bottom:18px"></div>
<div class="cv-canvas-wrap"><canvas id="cv-src-chart"></canvas></div>
```

**CSS .cv-insight-card** (light theme, **НЕ dark**):
```css
.cv-insight-card {
  background: var(--white); border: 1px solid var(--border);
  border-radius: var(--radius); padding: 18px 20px;
  box-shadow: var(--shadow-sm); min-height: 110px;
  display: flex; flex-direction: column; gap: 6px;
}
.cv-insight-lbl { font-size:12px; font-weight:600; color:#64748b; text-transform:uppercase; letter-spacing:.04em; }
.cv-insight-num { font-size:36px; font-weight:800; color:#0f172a; line-height:1; }
.cv-insight-num.txt { font-size:24px; color:#ec4899; }  /* для Top Source текст */
.cv-insight-sub { font-size:11px; color:#94a3b8; margin-top:auto; }
```

**Dropdowns populated FULL list** (не тільки existing):
```javascript
function _populateCVSrcDropdowns(){
  const allDepts=[...new Set([...CV,...ALL_VACS].map(v=>v.t).filter(Boolean))].sort();
  const allSns=['Intern','Junior','Middle','Senior','Lead','Expert'];
  // append options to selects (idempotent — only if length<=1)
}
```

**rCVSources()** logic:
- Filter items by selected dept + sn
- Build insights cards (Total / Sources / Top Source)
- Group items by source, sort desc, single dataset
- onClick handler → showCVSrcPopup(src, vacs, dept, sn)

**Insight cards** (3 шт):
- "Всього наймів" — count items in filter, sub-text = `dept · sn` або `усі команди`
- "Джерел" — unique sources count, sub-text = `унікальних`
- "Топ джерело" — top.name (24px, pink), sub-text = `${top.count} наймів` або `немає даних`

**showCVSrcPopup(src, vacs, dept, sn)**: title `Hiring Source — ${src}`, sub з активним фільтром, table same approach as CVDeptPopup.

**Anti-patterns** (НЕ робити):
- ❌ Stacked bars з груповим datasets — користувач хоче чисті bar per source
- ❌ Toggle By Dept/By Seniority — заміна на 2 dropdowns
- ❌ Dark cards — light theme з var(--white) як інші cv-cards
- ❌ Dropdowns з тільки existing data — повний список (всі depts, 6 seniority)

### Workload-Hired секція (схована)

Друга секція в `#view-workload`: повна таблиця рекрутерів з закритими (Hired) вакансіями та підрахунком TTF/TTH per recruiter. Контейнер: `#c-hired`. Render-функція: `rWorkloadHired()`. Має filter-controls: date period (`hwdf`/`hwdt`), preset chips (`This week / Last week / This month / Last month`), type filter (All/Vacancies/Tasks).

**ПОТОЧНИЙ СТАН: схована через `style="display:none"` на root `<div class="section">`.** Користувач попросив тимчасово приховати (станом на 2026-05). Render-функція `rWorkloadHired()` продовжує виконуватись (заповнює `#c-hired`) — це нормально, бо все під ним схована.

**Як повернути назад**: прибрати `style="display:none"` з кореневого `<div class="section">` секції Workload-Hired:

```html
<!-- сховано -->
<div class="section" style="display:none">
  <div class="section-header" ...>
    ... Workload - Hired ...

<!-- активно -->
<div class="section">
  <div class="section-header" ...>
    ... Workload - Hired ...
```

Render-функція `rWorkloadHired` не видаляється і не модифікується. Тільки inline-style на корневому div.

### Колонки таблиці Workload

| Колонка | Col key | Recruiter row | Vacancy/Task row | Subtask row |
|---------|---------|---------------|------------------|-------------|
| RECRUITER | `name` | avatar + name | issue key + summary | ↳ key + name |
| ROLE | `role` | — | REC/SRC/TASK badge | — |
| PRIORITY | `pr` | — | priority badge | priority badge |
| SENIORITY | `sn` | — | seniority text | seniority text |
| VACANCIES | `vac` | `allVacs.length` | status badge | status badge |
| TASKS | `tasks` | `taskItems.length` (teal) | — | — |
| HIRES | `hires` | `m.hires` | active hires | 1 |
| WORKLOAD | `wl` | workload bar | dept/team text | dept/team text |
| DAYS | `days` | — | days badge | days badge |

### Role badges

```javascript
const roleBadge=r=>r==='Recruiter'
  ?`<span style="font-size:10px;font-weight:600;color:#3b6ef5;background:#eff6ff;border-radius:4px;padding:2px 6px">REC</span>`
  :r==='Sourcer'
  ?`<span style="font-size:10px;font-weight:600;color:#8b5cf6;background:#f5f3ff;border-radius:4px;padding:2px 6px">SRC</span>`
  :r==='Task'
  ?`<span style="font-size:10px;font-weight:600;color:#0891b2;background:#ecfeff;border-radius:4px;padding:2px 6px">TASK</span>`
  :'<span class="dash-val">—</span>';
```

### Сортування і expand

```javascript
let _wlSortCol='hires',_wlSortDir=-1;
function wlSort(col){
  // Зберігаємо відкриті секції перед ре-рендером
  const openDids=[...new Set(
    Array.from(document.querySelectorAll('[data-wl]:not([data-wlsub])'))
      .filter(r=>r.style.display!=='none')
      .map(r=>r.dataset.wl)
  )];
  if(_wlSortCol===col)_wlSortDir*=-1;
  else{_wlSortCol=col;_wlSortDir=col==='name'?1:-1;}
  rWorkload();
  openDids.forEach(did=>togWL(did)); // відновити стан
}

function togWL(did){
  // Тільки vacancy рядки (не subtask!)
  const rows=document.querySelectorAll(`[data-wl="${did}"]:not([data-wlsub])`);
  const arr=document.getElementById('arr-'+did);
  const hidden=!rows[0]||rows[0].style.display==='none';
  rows.forEach(r=>r.style.display=hidden?'table-row':'none');
  if(!hidden){
    document.querySelectorAll(`[data-wl="${did}"][data-wlsub]`).forEach(r=>r.style.display='none');
  }
  if(arr)arr.textContent=hidden?'−':'+';
}

function togWLSubs(did,key){
  // IMPORTANT: uid includes did to avoid cross-recruiter collision on same vacancy key
  const uid=did+'-'+key;
  const rows=document.querySelectorAll(`[data-wlsub="${uid}"]`);
  const btn=document.getElementById('wlsb-'+uid);
  const hidden=!rows[0]||rows[0].style.display==='none';
  rows.forEach(r=>r.style.display=hidden?'table-row':'none');
  if(btn)btn.textContent=hidden?'−':'+';
}
```

### Фільтри (Status + Type)

```html
<!-- В section-header, після badge #bw -->
<div style="display:flex;align-items:center;gap:8px;margin-left:auto" onclick="event.stopPropagation()">
  <!-- Status: In progress / Plan -->
  <div style="...background:#f1f5f9;border-radius:8px;padding:4px 10px">
    <span>Status:</span>
    <label><input type="checkbox" id="wlf-ip" checked onchange="wlFilterSt()"> In progress</label>
    <label><input type="checkbox" id="wlf-pl" checked onchange="wlFilterSt()"> Plan</label>
  </div>
  <!-- Type: All / Vacancies / Tasks -->
  <div style="...background:#f1f5f9;border-radius:8px;overflow:hidden">
    <button onclick="wlFilterType('all')" id="wlft-all" style="background:#3b6ef5;color:#fff">All</button>
    <button onclick="wlFilterType('vac')" id="wlft-vac" style="background:transparent;color:#64748b">Vacancies</button>
    <button onclick="wlFilterType('task')" id="wlft-task" style="background:transparent;color:#64748b">Tasks</button>
  </div>
</div>
```

```javascript
let _wlFilterSt=new Set(['In progress','Plan']);
let _wlFilterType='all'; // 'all' | 'vac' | 'task'

function wlFilterSt(){
  _wlFilterSt=new Set();
  if(document.getElementById('wlf-ip').checked) _wlFilterSt.add('In progress');
  if(document.getElementById('wlf-pl').checked) _wlFilterSt.add('Plan');
  rWorkload();
}
function wlFilterType(t){
  _wlFilterType=t;
  ['all','vac','task'].forEach(k=>{
    const btn=document.getElementById('wlft-'+k);
    if(btn){btn.style.background=k===t?'#3b6ef5':'transparent';btn.style.color=k===t?'#fff':'#64748b';}
  });
  rWorkload();
}
```

**Фільтри у rWorkload:**
```javascript
// Status filter applied to recVacs/srcVacs:
const recVacs=activeVacs.filter(v=>(v.rec===name||...)&&_wlFilterSt.has(v.st));
const srcVacs=activeVacs.filter(v=>v.src===name&&...&&_wlFilterSt.has(v.st));
// Type filter:
const taskItems=_wlFilterType==='vac'?[]:TASKS.filter(t=>t.asgn===name).map(...);
const allVacs=_wlFilterType==='task'?[]:[...recVacs.map(...rec),...srcVacs.map(...src)];
// Empty members hidden:
if(!hasVacs) return; // skip row entirely
```

### Sticky header CSS

```css
/* overflow:clip не створює scroll container → sticky працює крізь нього */
#view-workload .section { overflow: clip; }
#c-workload .tbl-wrap { overflow: clip; }
#c-workload thead th {
  position: sticky;
  top: 64px; /* висота .header */
  z-index: 10;
  background: #f8fafc;
  box-shadow: 0 1px 0 #e2e8f0;
}
```
**УВАГА:** `overflow: hidden` на батьківських `.section` і `.tbl-wrap` ламає sticky. Замінювати на `overflow: clip`.

### Типові помилки Workload

- ❌ `overflow: hidden` на батьківських контейнерах — ламає `position: sticky` на thead. Замінити на `overflow: clip`
- ❌ `hasVacs = m.recVacs.length > 0` — не бачить людей без вакансій але з tasks. Треба `allVacs.length + taskItems.length > 0`
- ❌ Workload bar тільки по hires — tasks теж мають впливати: `load = hires + taskItems.length`
- ❌ Не включати Plan-вакансії без RECR запису — WP fallback: `v.rec==null && WP.find(w=>w.key===v.key)?.rec===name`
- ❌ `togWL` вибирає всі `[data-wl="${did}"]` включно з subtasks — ламає дефолтний прихований стан. Треба `:not([data-wlsub])`
- ❌ Не відновлювати стан після wlSort — користувач втрачає відкриті секції. Треба зберігати openDids і відновлювати через togWL
- ❌ hiresTotal тільки з recVacs — sourcer-only люди показують 0 hires. Рахувати з allVacs: `allVacs.reduce(...)`
- ❌ totalHires у badge як сума m.hires по всіх членах — подвійно рахує вакансії де є і REC і SRC. Треба унікальний підрахунок по ALL_VACS: `_allActiveVacs.reduce((s,v)=>s+(subs.length>0?subs.length+1:v.h),0)`
- ❌ `aE=!a.recVacs.length` у sort — sourcer-only завжди в кінці незалежно від сортування. Треба `aE=!a.allVacs.length&&!a.taskItems.length`
- ❌ Відсутні явні case для hires/wl у members.sort() — падають на default. Додати: `if(_wlSortCol==='hires') return (a.hires-b.hires)*_wlSortDir; if(_wlSortCol==='wl') return ((a.hires+a.taskItems.length)-(b.hires+b.taskItems.length))*_wlSortDir;`
- ❌ `data-wlsub="${v.key}"` та `id="wlsb-${v.key}"` не унікальні — якщо одна вакансія є у двох людей (REC + SRC), togWLSubs відкриває subtasks у першого знайденого. Треба `data-wlsub="${did}-${v.key}"` і `id="wlsb-${did}-${v.key}"`, `togWLSubs(did, key)`
- ❌ Subtask рядки без ROLE badge — треба `${roleBadge(v._role)}` (успадковує роль батьківської вакансії)
- ❌ Рядки з 0 вакансій і 0 tasks показуються після фільтрування — додати `if(!hasVacs) return;` в members.forEach перед побудовою row HTML

### Процедура оновлення TASKS

```
JQL: project = REC AND issuetype = Task AND statusCategory != Done ORDER BY created DESC
fields: summary, status, priority, assignee, customfield_11223
```
- `asgn` = `assignee.displayName` (не recruiter!)
- `sd` = `customfield_11223` (може бути null)
- Замінити масив `const TASKS=[...]` повністю

---

## Workload - Hired Tab (оновлено 2026-04-25)

### Структура сторінки Workload (актуальна)

Workload більше НЕ має окремого табу "Hired". Обидві секції — Active і Hired — знаходяться в одному `#view-workload`, прокручуються вертикально.

**Актуальна tab-bar (2 таби):**
```html
<div class="main-tab-bar">
  <div class="main-tab active" data-view="workload" onclick="switchView('workload')">👥 Workload</div>
  <div class="main-tab" data-view="dashboard" onclick="switchView('dashboard')">📊 Dashboard</div>
</div>
```

**`#view-workload` містить:**
```html
<div id="view-workload">
  <div id="wl-overview" style="margin-bottom:16px"></div>  <!-- Team Load block -->
  <div class="section"><!-- Active секція --></div>
  <div class="section"><!-- Hired секція --></div>
</div>
<div id="view-dashboard" style="display:none">...весь Dashboard контент...</div>
```

**`switchView` — НЕ містить view-hired (його більше немає):**
```javascript
function switchView(view){
  document.getElementById('view-workload').style.display=view==='workload'?'':'none';
  document.getElementById('view-dashboard').style.display=view==='dashboard'?'':'none';
  document.querySelectorAll('.main-tab').forEach(t=>t.classList.toggle('active',t.dataset.view===view));
  if(view==='dashboard'&&!_dashInit){_dashInit=true;rChartHires();rChartOpened();}
}
```

### Нові custom fields для HW

| Поле | Field ID | Примітки |
|------|----------|----------|
| Start date | `customfield_11223` | вже відоме |
| Factual close date | `customfield_22878` | дата прийняття оферу |
| First contact date | `customfield_23407` | дата першого контакту з кандидатом |

### HW масив — нова структура (з sd і fcd_c)

```javascript
// HW — hired вакансії
// Нові поля: sd (Start date = customfield_11223), fcd_c (First contact date = customfield_23407)
// fcd (Factual close date = customfield_22878 або з changelog transition to Hired)
const HW=[
  {key:"REC-218",...,fcd:"2026-04-09",sd:"2026-02-20",fcd_c:null,...},
  {key:"REC-219",...,fcd:"2026-04-22",sd:"2026-03-05",fcd_c:"2026-03-12",...},
  {key:"REC-241",...,fcd:"2026-04-21",sd:"2026-02-05",fcd_c:"2026-03-23",...},
  // ...
];
```

### Нові helper функції (після dag)

```javascript
// TTF = fcd - sd (дні від відкриття до офер)
// TTH = fcd - fcd_c (дні від першого контакту до офер)
function diffDays(d1,d2){if(!d1||!d2)return null;return Math.round((new Date(d1)-new Date(d2))/864e5);}
function ttBadge(d){return d==null?'<span class="dash-val">—</span>':`<span class="dbnorm">${d}d</span>`;}
```

### Колонки Workload - Hired (TTF + TTH замість DAYS)

**Заголовки:**
```javascript
// Замінити mkThH('days','DAYS') на:
${mkThH('ttf','TTF')} ${mkThH('tth','TTH')}
```

**Сортування (hwSort cases):**
```javascript
case 'ttf': sortedVacs.sort((a,b)=>{
  const da=diffDays(a.fcd,a.sd), db=diffDays(b.fcd,b.sd);
  return ((da??-1)-(db??-1))*hwSortDir; break;
});
case 'tth': sortedVacs.sort((a,b)=>{
  const da=diffDays(a.fcd,a.fcd_c), db=diffDays(b.fcd,b.fcd_c);
  return ((da??-1)-(db??-1))*hwSortDir; break;
});
```

**Parent vacancy row (TTF + TTH):**
```javascript
const vTTF=diffDays(v.fcd,v.sd);
const vTTH=diffDays(v.fcd,v.fcd_c);
// В <td>: ${ttBadge(vTTF)} та ${ttBadge(vTTH)}
```

**Subtask row (TTF + TTH, sd від батька якщо null):**
```javascript
const sTTF=diffDays(s.fcd,s.sd||v.sd);
const sTTH=diffDays(s.fcd,s.fcd_c);
// В <td>: ${ttBadge(sTTF)} та ${ttBadge(sTTH)}
```

**УВАГА:** Parent summary row (загальний рядок) має 10 колонок (TTF+TTH = 2 окремих `<td></td>`).

### Subtask expand fix (togHWSubs)

Subtask рядки відкриваються через `v._subs` масив у `_isSubParent` групах:

```javascript
// КРИТИЧНО: vSubs = v._subs, НЕ порожній масив!
const vSubs=v._isSubParent?(v._subs||[]):[];
const hasSubToggle=vSubs.length>0;
const subBtn=hasSubToggle
  ?`<button id="hwsb-${did}-${v.key}" onclick="event.stopPropagation();togHWSubs('${did}','${v.key}')"
      style="border:none;background:transparent;cursor:pointer;color:#10b981;font-size:14px;font-weight:700;padding:0 4px 0 0;line-height:1">+</button>`
  :'';
```

**sd для subParent з SD fallback:**
```javascript
// Якщо батьківська вакансія є в ALL_VACS (In progress/Plan) — брати звідти
// Якщо ні (вже Hired або не знайдено) — брати з глобального SD lookup
sd: avp?.sd || SD[pk] || null
```

### Period filter (фільтр по даті) для Hired секції

**HTML (в header Hired секції):**
```html
<input type="date" id="hwdf" style="..."> <span>—</span>
<input type="date" id="hwdt" style="...">
<button onclick="applyHWDateFilter()">Apply</button>
<button onclick="document.getElementById('hwdf').value='';document.getElementById('hwdt').value='';applyHWDateFilter()">Reset</button>
```

**JS:**
```javascript
let _hwDateFrom=null, _hwDateTo=null;
function applyHWDateFilter(){
  _hwDateFrom=document.getElementById('hwdf').value||null;
  _hwDateTo=document.getElementById('hwdt').value||null;
  rWorkloadHired();
  rWorkloadOverview();
}
```

**inRange фільтр у rWorkloadHired():**
```javascript
const inRange=v=>{
  if(!v.fcd) return !_hwDateFrom&&!_hwDateTo;
  if(_hwDateFrom&&v.fcd<_hwDateFrom) return false;
  if(_hwDateTo&&v.fcd>_hwDateTo) return false;
  return true;
};
const hiredPos=HW.filter(v=>v.type==='position'&&inRange(v));
const hiredSubs=HW.filter(v=>v.type==='subtask'&&inRange(v));
```

**Фільтр застосовується ДО групування** — правильно зменшує hire count батька якщо частина підзадач не в діапазоні.

### Active секція header (gradient style, як Hired)

```html
<div class="section-icon" style="background:linear-gradient(135deg,#3b6ef5,#6366f1);font-size:18px;display:inline-flex;align-items:center;justify-content:center;width:36px;height:36px;border-radius:10px">👥</div>
<span class="sec-badge" style="background:#eff6ff;color:#1d4ed8;font-weight:700;border-radius:20px;padding:4px 12px;font-size:12px" id="bw"></span>
```

### Team Load Overview block (rWorkloadOverview)

Розміщується в `#wl-overview` вгорі `#view-workload`. Оновлюється при зміні Period filter (Hired).

**4 метрики (картки):**
- **Active** — скільки членів команди мають `load > 0` (з усіх TEAM_ALL)
- **Overloaded** — `load > 20`
- **Warning** — `load > 8 && load <= 20`
- **On track** — `load > 0 && load <= 8`

де `load = hires + taskItems.length` (той самий принцип що в rWorkload).

```javascript
function rWorkloadOverview(){
  const allActive=ALL_VACS.filter(v=>v.st==='In progress'||v.st==='Plan');
  const activeST=ST.filter(s=>s.st!=='Hired');
  const mems=TEAM_ALL.map(name=>{
    const recVacs=allActive.filter(v=>v.rec===name);
    const srcVacs=allActive.filter(v=>v.src===name&&v.rec!==name);
    const allVacs=[...recVacs,...srcVacs];
    const h=allVacs.reduce((s,v)=>{
      const subs=activeST.filter(x=>x.pk===v.key);
      return s+(subs.length>0?subs.length+1:v.h);
    },0);
    const tk=TASKS.filter(t=>t.asgn===name);
    return{load:h+tk.length};
  });
  const activeM=mems.filter(m=>m.load>0).length;
  const overloaded=mems.filter(m=>m.load>20).length;
  const warning=mems.filter(m=>m.load>8&&m.load<=20).length;
  const ok=mems.filter(m=>m.load>0&&m.load<=8).length;

  const card=(val,lbl,col)=>`<div style="display:flex;flex-direction:column;align-items:center;justify-content:center;flex:1;gap:4px;padding:12px 0">
    <span style="font-size:36px;font-weight:800;color:${col};line-height:1">${val}</span>
    <span style="font-size:12px;color:#94a3b8;font-weight:500;text-transform:uppercase;letter-spacing:.05em">${lbl}</span>
  </div>`;

  document.getElementById('wl-overview').innerHTML=`
    <div style="background:#fff;border-radius:14px;border:1px solid #e8edf8;padding:16px 24px;box-shadow:0 1px 4px rgba(0,0,0,0.04)">
      <div style="font-size:11px;font-weight:700;color:#8b5cf6;text-transform:uppercase;letter-spacing:.08em;margin-bottom:12px">Team Load</div>
      <div style="display:flex;gap:12px;border-top:1px solid #f1f5f9;padding-top:12px">
        ${card(activeM+'/'+TEAM_ALL.length,'Active','#0f172a')}
        <div style="width:1px;background:#f1f5f9"></div>
        ${card(overloaded,'Overloaded','#ef4444')}
        <div style="width:1px;background:#f1f5f9"></div>
        ${card(warning,'Warning','#f59e0b')}
        <div style="width:1px;background:#f1f5f9"></div>
        ${card(ok,'On track','#10b981')}
      </div>
    </div>`;
}
```

**Init call (в кінці скрипту):**
```javascript
rKPI(); r1(); r2(); r3(); r3plan(); r4(); r5(); rWorkload(); rWorkloadHired(); rWorkloadOverview();
// r3() — IP-only Open Vacancies per Department (#c3)
// r3plan() — Plan-only mirror (#c3p) — обидві секції рендеряться разом
```

### Sticky header CSS (Hired секція)

```css
/* overflow:clip замість overflow:hidden — щоб sticky thead працював */
#view-workload .section { overflow: clip; }
/* Не додавати #view-hired .section — цього елементу більше немає! */
```

### Типові помилки Workload - Hired

- ❌ `vSubs=[]` hardcoded — підзадачі не розкриваються. Треба `const vSubs=v._isSubParent?(v._subs||[]):[]`
- ❌ `sd` для subParent тільки з ALL_VACS — батьківська вакансія може вже бути Hired і її немає в ALL_VACS (тільки In progress/Plan). Fallback: `sd: avp?.sd || SD[pk] || null`
- ❌ Видаляти `#view-hired .section { overflow: clip; }` і `#c-hired` правила — `#view-hired` більше не існує, але `#c-hired` id може ще бути в HTML якщо не перейменований. Видаляти тільки ті що точно orphan.
- ❌ `customfield_22878` і `customfield_23407` ще не в JQL по замовчуванню — при оновленні HW треба явно додавати ці поля до fields списку
- ❌ Окремий tab "Workload - Hired" — видалено. Тепер 3 таби: Workload / Open Vacancies / Closed Vacancies
- ❌ Старий ендпоінт `/rest/api/3/search` повертає 410 — мігрувати на `/rest/api/3/search/jql` (POST + nextPageToken pagination)
- ❌ Фільтр Hired-by-week ТІЛЬКИ через `v.fcd` пропускає випадки коли поле не заповнили в Jira — обовʼязково додавати `v.hd` (transition date з changelog) як fallback. Усе через helper `closeDate(v)`

---

## Auto-update архітектура (з 2026-04-28)

Дашборд тепер **автоматично оновлюється щогодини** через GitHub Actions cron job.

### Структура

```
claude-reports/
├── reports/
│   ├── REC_recruitment_dashboard.html  ← маркери AUTO_DATA_*, AUTO_CV_*, AUTO_DATE_* + password overlay
│   └── README.md                        ← інструкції по setup
├── scripts/
│   └── update_rec_dashboard.py         ← Python скрипт-оновлювач
├── .github/workflows/
│   └── update-rec-dashboard.yml        ← hourly cron + manual dispatch
└── .gitignore
```

### Маркери в HTML (Python script замінює тільки контент між ними)

```javascript
// <<<AUTO_DATA_START>>> — managed by scripts/update_rec_dashboard.py
const SD={...}; const SN={...}; const OP=[...]; const HW=[...];
const WP=[...]; const ST=[...]; const RECR={...}; const SRCR={...};
const TASKS=[...];
// <<<AUTO_DATA_END>>>

// <<<AUTO_CV_START>>>
const CV=[...];
// <<<AUTO_CV_END>>>
```

```html
<!--<<<AUTO_DATE_START>>>-->Дані: 28 квітня 2026, оновлено 13:08 (Kyiv)<!--<<<AUTO_DATE_END>>>-->
```

### Скрипт `update_rec_dashboard.py`

- **Auth:** HTTP Basic — `JIRA_EMAIL` + `JIRA_API_TOKEN` (як GitHub Secrets)
- **Endpoint:** `POST /rest/api/3/search/jql` (новий, старий `/search` повертає 410!)
- **Пагінація:** `nextPageToken` (НЕ `startAt`)
- **Changelog:** для кожного Hired item окремий call `GET /rest/api/3/issue/{key}/changelog` → шукати `items[].field='status'` де `toString='Hired'` → брати `created[:10]` як `hd`
- **JS literal serializer:** `js_value()` робить unquoted keys для valid identifiers, double-quoted strings, `null`/`true`/`false`. Це важливо для збереження формату existing data arrays.
- **Заміна:** `replace_marker_block(text, start_re, end_re, new_inner)` — через regex з groups, зберігає markers, замінює inner.

### Workflow (`.github/workflows/update-rec-dashboard.yml`)

```yaml
on:
  schedule:
    - cron: '7 * * * *'   # щогодини о :07 UTC
  workflow_dispatch: {}
permissions:
  contents: write
```

Кроки: checkout → setup-python@v5 → run script → `git diff` reports/REC_*.html → якщо є зміни: commit з ботського name + push.

### Password overlay (для GitHub Pages public access)

```javascript
(function(){
  if(sessionStorage.getItem('rec_auth')==='1') return;
  // overlay HTML with input + button
  // password === 'RECrec1' → sessionStorage.setItem('rec_auth','1') + remove overlay
})();
```

URL: `https://olenapizniak.github.io/claude-reports/reports/REC_recruitment_dashboard.html`

### Типові помилки auto-update

- ❌ Використовувати legacy `/rest/api/3/search?startAt=...` — повертає 410. Тільки `/rest/api/3/search/jql` POST з `nextPageToken`
- ❌ Не додавати `hd` поле в HW і CV → блок Vacancy Dynamics, Avg TTF/TTH, Closed Count покажуть 0 коли `fcd` не заповнено в Jira
- ❌ Маркери не парні (зник `<<<AUTO_DATA_END>>>`) → скрипт впаде з `Marker pair not found in HTML`
- ❌ Забути `permissions: contents: write` у workflow → push fail
- ❌ Запускати workflow без `JIRA_EMAIL`/`JIRA_API_TOKEN` секретів → exit code 1, повідомлення `JIRA_EMAIL and JIRA_API_TOKEN env vars are required`
- ❌ `switchView` з `view-hired` рядком — цей елемент не існує, викличе помилку JS


## Jira Automation Rules: live `Number of hires` decrement (з 2026-05-08)

У проекті REC налаштовані 3 правила Jira Automation, що тримають поле `Number of hires` (customfield_23545) синхронізованим з реальним станом hire-процесу:

### Rule 1: sub-task → Hired декрементує parent
```
Trigger: Work item transitioned → Hired
Condition: Work item type = Vacancy sub-task
Branch: Parent
Action: Edit work item
  Number of hires = {{#=}}{{issue."Number of hires"}} - 1{{/}}
```

### Rule 2: parent → Hired декрементує власне поле (тільки якщо є sub-tasks)
```
Trigger: Work item transitioned → Hired
Condition 1: Work item type = Open position
Condition 2: {{issue."Number of hires"}} > 0
Condition 3: Related work items (Sub-tasks) → Are present
Action: Edit work item
  Number of hires = {{#=}}{{issue."Number of hires"}} - 1{{/}}
```
**Важливо**: Condition 3 (`Are present`) виключає solo вакансії — для solo parent при закритті h залишається на оригінальному значенні (типово 1), щоб не зіпсувати аналітику.

### Rule 3: parent's `Number of hires` змінився → синкає у всі sub-tasks
```
Trigger: Field value changed (Number of hires)
Condition: Work item type = Open position
Branch: Sub-tasks
Action: Edit work item
  Number of hires = {{triggerIssue."Number of hires"}}
Rule details: ✅ "Allow other rule actions to trigger this rule" — ОБОВ'ЯЗКОВО включити!
```
Без галочки "Allow other rule actions" Rule 3 не спрацює коли Rule 1/2 змінюють поле.

### Семантика поля `h` (Number of hires) після цих правил

| Стан вакансії | Значення `h` | Приклад |
|----------------|---------------|---------|
| Активна, sub-task'и не закриті | total expected hires | h=3, 2 subs активні + parent |
| Активна, частина subs закрита | remaining hires | h=2 (1 sub був закритий) |
| Hired (parent + всі subs) | 0 (multi) або original (solo) | h=0 для multi, h=1 для solo |

### КРИТИЧНО: КОНВЕНЦІЯ FORMULA для підрахунку hires

Через нову автоматизацію `v.h` тепер відображає **remaining hires**, не **total expected**. Тому ВСІ формули підрахунку hires у дашборді мають використовувати **уніфіковану формулу**:

```javascript
// Уніфікована формула hires per vacancy (active phase)
const _activeST = ST.filter(s => s.st !== 'Hired');
const _hires = v => {
  const subs = _activeST.filter(x => x.pk === v.key);
  return subs.length > 0 ? subs.length + 1 : v.h;
};
```

**Чому**: `subs.length+1` для multi-vacancies НЕ залежить від `v.h` — рахує реальні active units (живі subs + parent). Це робить формулу стійкою до:
- Legacy даних, де `v.h` не оновлювалось (час до автоматизації)
- Ручних правок поля
- Race conditions у Jira automation

Для solo (без subs) використовуємо `v.h` — для них Rule 1/2 не декрементують.

### Місця де ця формула застосована (✅ всі узгоджені після 2026-05-08)

- `rKPI()` → KPI HIRES NEEDED (line ~1532)
- `rWorkload()` → Workload-Active hires column + per-recruiter (line ~2744)
- `rWorkloadOverview()` → totalHires + per-member load (line ~3046, 3051) — ✅ виправлено 2026-05-08
- `r3()` / `r3plan()` → Open Vacancies per Department (lines ~1756, 1884) — використовує count за статусом
- `rWorkloadHired()` → `v.type==='subtask'?1:(v.h||1)` — спеціальна формула для closed (sub=1, parent=h з fallback)

### Анти-приклад (НЕ робити)

```javascript
// ❌ НЕ використовуй v.h напряму для multi-vacancies
const totalHires = allActive.reduce((s, v) => s + v.h, 0);
// Це дасть НЕТОЧНУ цифру якщо v.h "відстає" від реального remaining
// (legacy data, manual edits, race conditions)
```

### Тестування при змінах формули

Якщо змінюєш формулу підрахунку hires — обов'язково перевір на REC-249 (h=3, 3 active subs):
- Очікувано: hires = 4 (parent + 3 subs)
- Якщо повертає 3 — формула використовує `v.h` напряму (BUG)
- Якщо повертає 4 — формула uses `subs.length+1` (правильно)

---

## Tab "Plan Vacancies" + новий KPI layout (додано 2026-05-22)

### Що змінилось

1. **Новий таб `📌 Plan Vacancies`** у головній панелі між Workload і Open Vacancies. Plan-related контент (KPI Plan + секція "Plan Vacancies per Department") винесений сюди з табу Open Vacancies.
2. **KPI cards у кожному з табів Plan/Open** перероблені на 4 картки з розділенням Open Position vs Recruitment Assignment:
   - 📂 **Vacancies** — count OP parents
   - 🎯 **Hires needed** — sum OP slots (parents + sub-tasks)
   - 📋 **Recruitment Assignments** — count RA parents
   - 🎓 **Specialists needed** — sum RA slots (parents + sub-tasks)
3. **Active Vacancies KPI прибрано** з Open Vacancies tab — замість нього показуються 4 нові картки.
4. **Vacancy Dynamics block** (Closed Vacancies tab) переписаний з "Open vs Hired" на "Hired Breakdown by issue type" — обидва sub-card-и (Current vs Previous Week, All Time / Period) показують ті ж 4 категорії з фільтром Hired.
5. **Картки Vacancy Dynamics клікабельні** → відкривають popup із списком вакансій за цією цифрою.

### HTML структура — main-tab-bar (3 → 4 табів)

```html
<div class="main-tab-bar">
  <div class="main-tab active" data-view="workload" onclick="switchView('workload')">👥 Workload</div>
  <div class="main-tab" data-view="plan" onclick="switchView('plan')">📌 Plan Vacancies</div>
  <div class="main-tab" data-view="dashboard" onclick="switchView('dashboard')">📂 Open Vacancies</div>
  <div class="main-tab" data-view="closed" onclick="switchView('closed')">✅ Closed Vacancies</div>
</div>
```

`switchView()` оновлено — додано `view-plan` блок (hide/show аналогічно іншим).

### HTML — KPI cards Plan tab (4 картки)

```html
<div id="view-plan" style="display:none">
  <div style="display:flex;align-items:stretch;gap:12px;margin-bottom:28px">
    <div class="kpi-card blue" style="flex:1;justify-content:center">
      <div class="kpi-icon">📂</div>
      <div class="kpi-num" id="kn-plan-op">—</div>
      <div class="kpi-label">Vacancies</div>
    </div>
    <div class="kpi-card blue" style="flex:1;justify-content:center">
      <div class="kpi-icon">🎯</div>
      <div class="kpi-num" id="kn-plan-hires">—</div>
      <div class="kpi-label">Hires needed</div>
    </div>
    <div class="kpi-card blue" style="flex:1;justify-content:center">
      <div class="kpi-icon">📋</div>
      <div class="kpi-num" id="kn-plan-ra">—</div>
      <div class="kpi-label">Recruitment Assignments</div>
    </div>
    <div class="kpi-card blue" style="flex:1;justify-content:center">
      <div class="kpi-icon">🎓</div>
      <div class="kpi-num" id="kn-plan-spec">—</div>
      <div class="kpi-label">Specialists needed</div>
    </div>
  </div>
  <!-- Plan Vacancies per Department section (переміщена з view-dashboard) -->
  <div class="section">
    <div class="section-header" onclick="tog(this)">
      <div class="section-icon">📌</div>
      <h2>Plan Vacancies per Department</h2>
      <span class="sec-badge" id="b3p"></span>
      <div class="toggle-btn">−</div>
    </div>
    <div id="c3p" style="padding:0 4px 8px"></div>
  </div>
</div>
```

KPI cards у Open Vacancies tab (view-dashboard) мають таку саму структуру з IDs `kn-op`, `kn-hn`, `kn-ra`, `kn-spec` (orange + blue alternating).

### JS — універсальні helpers для OP/RA класифікації

```javascript
// Class helpers — read `kind` field (set by Python script), fallback to `type`.
function _isOPParent(v){ if(v.kind) return v.kind==='op'; return v.type!=='subtask'; }
function _isOPany(v){ if(v.kind) return v.kind==='op'||v.kind==='op_sub'; return true; }
function _isRAParent(v){ return v.kind==='ra'; }
function _isRAany(v){ return v.kind==='ra' || v.kind==='ra_sub'; }

// vacInStatus — для OP (parent.st OR active sub-task.st matches)
function vacInStatus(v, status){
  if(v.st===status) return true;
  return ST.some(s=>s.pk===v.key && s.st!=='Hired' && s.st===status);
}
// raInStatus — для RA (parent.st OR active RAS sub-task.st matches)
function raInStatus(v, status){
  if(v.st===status) return true;
  return RAS.some(s=>s.pk===v.key && s.st!=='Hired' && s.st===status);
}
// slotsInStatus — універсальна формула: parent (1 якщо матчить) + active subs які матчать
function slotsInStatus(v, subs, status){
  const matchingSubs=subs.filter(x=>x.st===status);
  const parentMatch=v.st===status?1:0;
  if(subs.length>0) return matchingSubs.length+parentMatch;
  return v.st===status?(v.h||1):0;
}
```

### JS — rKPI() рендерить 8 значень

```javascript
function rKPI(){
  const _activeST=ST.filter(s=>s.st!=='Hired');
  const _activeRAS=RAS.filter(s=>s.st!=='Hired');

  // ── Open Vacancies tab (In progress) ─────────────────
  const _activeOPs=OP.filter(v=>vacInStatus(v,'In progress'));
  document.getElementById('kn-op').textContent=_activeOPs.length;
  document.getElementById('kn-hn').textContent=_activeOPs.reduce((s,v)=>{
    const subs=_activeST.filter(x=>x.pk===v.key);
    return s+slotsInStatus(v,subs,'In progress');
  },0);
  const _activeRAs=RA.filter(v=>raInStatus(v,'In progress'));
  document.getElementById('kn-ra').textContent=_activeRAs.length;
  document.getElementById('kn-spec').textContent=_activeRAs.reduce((s,v)=>{
    const subs=_activeRAS.filter(x=>x.pk===v.key);
    return s+slotsInStatus(v,subs,'In progress');
  },0);

  // ── Plan Vacancies tab ──────────────────────────────
  const _planOPs=OP.filter(v=>vacInStatus(v,'Plan'));
  document.getElementById('kn-plan-op').textContent=_planOPs.length;
  document.getElementById('kn-plan-hires').textContent=_planOPs.reduce((s,v)=>{
    const subs=_activeST.filter(x=>x.pk===v.key);
    return s+slotsInStatus(v,subs,'Plan');
  },0);
  const _planRAs=RA.filter(v=>raInStatus(v,'Plan'));
  document.getElementById('kn-plan-ra').textContent=_planRAs.length;
  document.getElementById('kn-plan-spec').textContent=_planRAs.reduce((s,v)=>{
    const subs=_activeRAS.filter(x=>x.pk===v.key);
    return s+slotsInStatus(v,subs,'Plan');
  },0);
}
```

### Vacancy Dynamics block (Closed Vacancies tab) — Hired Breakdown

**Header** перейменовано:
```html
<h2>Vacancy Dynamics: Hired Breakdown<br>
  <span style="color:#94a3b8;font-weight:400;font-size:11px">by issue type · Open Position vs Recruitment Assignment</span>
</h2>
<!-- badge bcv1 ВИДАЛЕНО -->
```

Два sub-cards (`cv-week-block`, `cv-alltime-block`) показують 4 Hired стати кожен.

**Логіка `rCVDynamics()`** використовує buckets:

```javascript
let _vdThis={}, _vdAt={}, _vdAtLabel='', _vdWeekLabel='';

function rCVDynamics(){
  const wThis=cvWeekRange(0), wPrev=cvWeekRange(1);
  const hiredItemsInWeek=w=>{
    // ... dedup hw + ALL_VACS hired + ST hired in week
    // Кожен елемент має v.kind (fallback 'op'/'op_sub' для legacy)
  };
  const hThisArr=hiredItemsInWeek(wThis), hPrevArr=hiredItemsInWeek(wPrev);
  const slotsOf=v=>(v.type==='subtask'?1:(v.h||1));

  const bucketize=arr=>({
    opParents:arr.filter(_isOPParent),
    opAll:arr.filter(_isOPany),
    raParents:arr.filter(_isRAParent),
    raAll:arr.filter(_isRAany),
  });
  const statsFromBucket=b=>({
    opCount:b.opParents.length,
    opSlots:b.opAll.reduce((s,v)=>s+slotsOf(v),0),
    raCount:b.raParents.length,
    raSlots:b.raAll.reduce((s,v)=>s+slotsOf(v),0),
  });
  _vdThis=bucketize(hThisArr);
  const tw=statsFromBucket(_vdThis), pw=statsFromBucket(bucketize(hPrevArr));

  // Render 4 stat-cards у cv-stat-grid (4 columns)
  // Кожна card має onclick="openVDPopup('this','opCount')" і т.д.

  // All Time / Period — _vdAt=bucketize(cvScope); cvScope=CV (all) або CV.filter(period)
}
```

### Popup — клік на картці Vacancy Dynamics

**Реюз HTML-елементу `s5popup` / `s5overlay`** (вже існує в дашборді). Розширено до `min(1320px, 96vw)`, `max-height:85vh`, `min-width:1180px` для таблиці.

**Окремий sort state + render** (не міксувати з S5):

```javascript
let _vdPopupItems=[], _vdPopupSort={col:'h',dir:-1}, _vdPopupCols=[];

const _vdColsOP=[
  {id:'key',lbl:'Key'},{id:'s',lbl:'Vacancy'},
  {id:'pr',lbl:'Priority'},{id:'sn',lbl:'Seniority'},
  {id:'rec',lbl:'Recruiter'},{id:'src',lbl:'Sourcer'},
  {id:'fcd',lbl:'Factual close date'},{id:'hd',lbl:'Hired transition date'}
];
const _vdColsRA=[ // БЕЗ Seniority
  {id:'key',lbl:'Key'},{id:'s',lbl:'Recruitment Assignment'},
  {id:'pr',lbl:'Priority'},
  {id:'rec',lbl:'Recruiter'},{id:'src',lbl:'Sourcer'},
  {id:'fcd',lbl:'Factual close date'},{id:'hd',lbl:'Hired transition date'}
];

function openVDPopup(period, popKey){
  // period: 'this' | 'at'. popKey: 'opCount' | 'opSlots' | 'raCount' | 'raSlots'
  const bucket = period==='this' ? _vdThis : _vdAt;
  const periodLbl = period==='this' ? `This week (${_vdWeekLabel})` : _vdAtLabel;
  let items, title, kind;
  if(popKey==='opCount'){ items=bucket.opParents; title='Vacancies'; kind='op'; }
  else if(popKey==='opSlots'){ items=bucket.opAll; title='Hires needed'; kind='op'; }
  else if(popKey==='raCount'){ items=bucket.raParents; title='Recruitment Assignments'; kind='ra'; }
  else { items=bucket.raAll; title='Specialists needed'; kind='ra'; }
  _vdPopupItems=items.slice();
  _vdPopupCols=kind==='ra'?_vdColsRA:_vdColsOP;
  // Render popup
}
```

**КРИТИЧНО — popup НЕ має колонки Status і Hires:**
- Status — всі items в Hired, неінформативно
- Hires — для subtasks завжди 1, для parents теж 1 (бо в popup ми вже розбили по slot-ам), неінформативно

**Колонка Factual close date** (`fcd`) — з custom field `customfield_22878` (заповнюється рукою в Jira; часто null).
**Колонка Hired transition date** (`hd`) — з Jira changelog (автоматично, через `fetch_hired_transition_date()` у Python скрипті).

### Python script — нові поля у HW і CV

```python
F = {
    # ... existing fields ...
    'num_specialists': 'customfield_25663',  # RA: Number of specialists needed
    'end_date':       'customfield_11232',  # End date (OP + RA)
}

# Map issuetype → dashboard kind (для розрізнення OP vs RA у Vacancy Dynamics)
_KIND = {
    'Open position': 'op',
    'Vacancy sub-task': 'op_sub',
    'Recruitment Assignment': 'ra',
    'Recruitment Assignment sub-task': 'ra_sub',
}

# HW і CV — для кожного hired item додати:
issuetype = (fld.get('issuetype') or {}).get('name')
kind = _KIND.get(issuetype, 'op')
typ = 'subtask' if kind in ('op_sub', 'ra_sub') else 'position'
h_field = F['num_specialists'] if kind in ('ra', 'ra_sub') else F['num_hires']

item = {
    # ... existing fields ...
    'kind': kind,           # 'op' | 'op_sub' | 'ra' | 'ra_sub'
    'ed': fld.get(F['end_date']),    # End date
    'pr': (fld.get('priority') or {}).get('name'),  # Priority (раніше тільки в HW)
    'h': fld.get(h_field) or 1,      # use num_specialists для RA
}
```

**ВАЖЛИВО:** до додавання `kind` поля Python script ставив `type='position'` для ВСЬОГО окрім Vacancy sub-task. Це означало що RA hired items (REC-201, REC-359 і т.д.) рахувались як OP. Після цього оновлення `kind` field розрізняє їх.

Для legacy даних (без `kind`) — fallback у JS helpers:
- `_isOPParent`: повертає true якщо `type!=='subtask'` (тобто рахується як OP parent)
- `_isOPany`: повертає true завжди (всі legacy = OP)
- `_isRAParent` / `_isRAany`: повертають false без `kind` (тому RA items до оновлення невидимі — ОК, бо їх все одно немає)

### UI tweaks

**Чіпси All time / Month / Quarter / Year + Custom date range — в одному рядку:**

```html
<div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap;font-size:12px">
  <div class="dp-chips" style="display:flex;gap:4px;flex-shrink:0">
    <button class="dp-chip cv-at-chip active" data-mode="all">All time</button>
    <!-- ... -->
  </div>
  <span style="color:#cbd5e1;margin:0 2px">·</span>
  <!-- Custom + dates + Apply ГРУПУЮТЬСЯ разом (nowrap) -->
  <div style="display:flex;align-items:center;gap:6px;flex-shrink:0;flex-wrap:nowrap">
    <span style="color:#64748b;font-weight:600">Custom:</span>
    <input type="date" id="cv-at-from" class="cv-input">
    <span style="color:#94a3b8">—</span>
    <input type="date" id="cv-at-to" class="cv-input">
    <button onclick="cvSetAllTime('custom')" style="...flex-shrink:0">Apply</button>
  </div>
</div>
```

Apply кнопка ніколи не відрізняється від date inputs (через внутрішній `flex-wrap:nowrap`), а вся група рветься цілою.

### Конвенції цього блоку

1. **"Vacancies" / "Recruitment Assignments" count = ТІЛЬКИ parents.** Sub-tasks не рахуються як окремі вакансії.
2. **"Hires needed" / "Specialists needed" = всі слоти.** Parent (якщо матчить статус) + sub-tasks які матчать статус. Subtask = завжди 1 слот.
3. **`kind` field має пріоритет над `type`.** Перевіряти `v.kind` ПЕРШИМ, `v.type` тільки як legacy fallback.
4. **Popup для Hired подій НЕ показує Status і Hires колонки.** Ці колонки в цьому контексті завжди однакові і неінформативні.

### Файли, які змінювались

- `reports/REC_recruitment_dashboard.html` — HTML structure (4-tab nav, 4-card KPIs, Vacancy Dynamics rewrite, popup, helpers)
- `scripts/update_rec_dashboard.py` — додано `num_specialists`, `end_date`, `_KIND`, поля `kind`/`ed`/`pr` у HW/CV

---

## Closed Vacancies tab refactor — clickable popups + type toggles (додано 2026-05-22)

Великий пакет змін до Closed Vacancies табу, який зробив його повністю консистентним з Plan/Open Vacancies через `kind` field + єдину canonical date logic (`closeDate`).

### Generic VD popup — реюз для ВСІХ блоків з list-of-hired-items

Створено універсальну функцію `_showVDPopupGeneric(items, title, subtitle, kind)` яка реюзає `s5popup` HTML-елемент. Усі popup-вікна на Closed Vacancies tab тепер викликають її замість кастомного HTML.

```javascript
const _vdColsOP=[
  {id:'key',lbl:'Key'},{id:'s',lbl:'Vacancy'},
  {id:'pr',lbl:'Priority'},{id:'sn',lbl:'Seniority'},
  {id:'rec',lbl:'Recruiter'},{id:'src',lbl:'Sourcer'},
  {id:'sd',lbl:'Start date'},{id:'fcd',lbl:'Factual close date'},{id:'hd',lbl:'Hired transition date'}
];
const _vdColsRA=[ // БЕЗ Seniority — у RA немає такого поля
  {id:'key',lbl:'Key'},{id:'s',lbl:'Recruitment Assignment'},
  {id:'pr',lbl:'Priority'},
  {id:'rec',lbl:'Recruiter'},{id:'src',lbl:'Sourcer'},
  {id:'sd',lbl:'Start date'},{id:'fcd',lbl:'Factual close date'},{id:'hd',lbl:'Hired transition date'}
];

function _showVDPopupGeneric(items, title, subtitle, kind){
  _vdPopupItems=items.slice();
  _vdPopupCols=kind==='ra'?_vdColsRA:_vdColsOP;
  _vdPopupSort={col:'fcd',dir:-1}; // default sort by Factual close date desc
  document.getElementById('s5popup-title').textContent=title;
  document.getElementById('s5popup-sub').textContent=subtitle;
  _renderVDPopupHeaders();
  document.getElementById('s5popup-tbody').innerHTML=_renderVDPopupRows();
  document.getElementById('s5overlay').style.display='block';
  document.getElementById('s5popup').style.display='flex';
}
```

**Розмір popup** збільшено до `min(1320px, 96vw)`, `max-height:85vh`, `min-width:1180px` для таблиці — щоб всі 9 (OP) / 8 (RA) колонок вміщались без обрізки `HIRED TRANSITION DATE`.

**КРИТИЧНО — popup НЕ має колонок Status і Hires:**
- Status — всі items в Hired, неінформативно
- Hires — для subtasks завжди 1, неінформативно

**Колонки в порядку часової логіки** (зліва направо): Start date → Factual close date → Hired transition date — щоб TTF/TTH можна було порахувати очима.

### HW enrichment lookup — для legacy CV items без kind/pr

CV-items зі старих auto-update runs можуть не мати `kind`, `pr`, `sn` полів. HW завжди їх містить (після оновлення Python script). Тому додано lookup, що збагачує CV items відсутніми полями з HW.

```javascript
const _HW_BY_KEY={};
HW.forEach(h=>{_HW_BY_KEY[h.key]=h;});
function _enrichFromHW(v){
  const hw=_HW_BY_KEY[v.key];
  if(!hw) return v;
  return {...v, pr:v.pr??hw.pr, kind:v.kind??hw.kind, sn:v.sn??hw.sn};
}
```

`_enrichFromHW` викликається у `bucketize` (Vacancy Dynamics) і в `_cvByType` (TTF/TTH/Closed/Sources) — щоб popup і фільтри коректно працювали для всіх items.

### Type toggle filter — окремий стан для кожного блоку

Усі блоки на Closed Vacancies tab отримали toggle filter Vacancies / Rec Assign. **Кожен блок має ОКРЕМИЙ стан** — користувач може бачити, наприклад, TTF Vacancies + TTH Rec Assign + Closed Vacancies by Dept = Rec Assign одночасно.

```javascript
let _cvVfFilterTTF='vac', _cvVfFilterTTH='vac';  // TTF + TTH (незалежно)
let _cvCntFilter='vac';                            // Closed Vacancies by Dept
let _cvSrcFilter='vac';                            // Hiring Sources

function _cvByType(mode){
  const pred=mode==='ra'?_isRAany:_isOPany;
  return CV.map(_enrichFromHW).filter(pred);
}
```

**Setter pattern** (приклад для одного блоку):
```javascript
function setCvCntFilter(mode){
  _cvCntFilter=mode;
  const isVac=mode==='vac';
  const a=document.getElementById('cvcnt-vac'), b=document.getElementById('cvcnt-ra');
  if(a){a.style.background=isVac?'#f59e0b':'transparent';a.style.color=isVac?'#fff':'#64748b';}
  if(b){b.style.background=!isVac?'#f59e0b':'transparent';b.style.color=!isVac?'#fff':'#64748b';}
  rCVClosedCount();
}
```

**Кольори active button узгоджуються з accent-кольором блоку:**
| Блок | Active color | ID-prefix кнопок |
|------|--------------|-------------------|
| TTF  | `#3b6ef5` (blue) | `cvvf-vac` / `cvvf-ra` |
| TTH  | `#10b981` (green) | `cvvf2-vac` / `cvvf2-ra` |
| Closed Vacancies by Dept | `#f59e0b` (orange) | `cvcnt-vac` / `cvcnt-ra` |
| Hiring Sources | `#ec4899` (pink) | `cvsrc-vac` / `cvsrc-ra` |

**Toggle стиль** — однаковий для всіх (раніше у Closed Vacancies був ярчий, потім зменшений):
```html
<div onclick="event.stopPropagation()" style="display:flex;align-items:center;background:#f1f5f9;border-radius:8px;overflow:hidden;font-size:12px">
  <button onclick="setCvXxxFilter('vac')" id="cvxxx-vac" style="padding:5px 12px;border:none;cursor:pointer;font-size:12px;font-weight:600;background:#ACCENT;color:#fff">📂 Vacancies</button>
  <button onclick="setCvXxxFilter('ra')" id="cvxxx-ra" style="padding:5px 12px;border:none;cursor:pointer;font-size:12px;font-weight:600;background:transparent;color:#64748b">📋 Rec Assign</button>
</div>
```

### Clickable bars/cards → popup

Усі charts на Closed Vacancies tab клікабельні — click на bar/card відкриває popup з deviceData:

| Блок | Click target | Popup опеншер | Дані для popup |
|------|--------------|---------------|----------------|
| Vacancy Dynamics (4 cards) | KPI card | `openVDPopup('this'\|'at', popKey)` | `_vdThis` / `_vdAt` bucket |
| Avg TTF chart | bar (dept) | `openCVMetricPopup('ttf', dept)` | `_cvByType` + dept + sd |
| Avg TTH chart | bar (dept) | `openCVMetricPopup('tth', dept)` | `_cvByType` + dept + fcd_c |
| Closed Vacancies by Dept | bar (dept) | `showCVDeptPopup(dept, vacs)` → `_showVDPopupGeneric` | `_cvCntDeptVacs[dept]` (filtered by type+period) |
| Hiring Sources | bar (source) | `showCVSrcPopup(src, vacs, dept, sn)` → `_showVDPopupGeneric` | `_cvSrcVacsBySrc[src]` (filtered by type+dept+sn) |

**Chart.js onClick + onHover pattern:**
```javascript
options:{
  onClick:(evt,els)=>{
    if(els.length) openCVMetricPopup('ttf', labels[els[0].index]);
  },
  onHover:(evt,els)=>{evt.native.target.style.cursor=els.length?'pointer':'default';},
  plugins:{
    tooltip:{callbacks:{label:ctx=>`Avg: ${ctx.parsed.x}d · Hires: ${e.n} · click to see list`}}
  }
}
```

### КОНВЕНЦІЯ: closeDate(v) = v.fcd || v.hd ВСЮДИ

КРИТИЧНО: усі фільтри та агрегації по даті закриття використовують canonical helper `closeDate(v) = v.fcd || v.hd || null`. Це означає:
- **fcd має пріоритет** — це бізнес-правда (recruiter manually entered)
- **hd як fallback** — коли recruiter не заповнив fcd, беремо дату транзиту в статус Hired з changelog
- **Single date per item** — запобігає double-counting (item з fcd у тижні A і hd у тижні B рахується ОДИН раз)

Усі місця застосування:

| Місце | Лінія | Helper |
|---|---|---|
| Hired This Week badge + table (r2) | 1658 | `inRange(closeDate(v))` |
| Workload Hired (rWorkloadHired) | 2903–2910 | `closeDate(v)` |
| Workload TT Overview (rWorkloadOverview) | 3110–3120 | `closeDate(v)` |
| Vacancy Dynamics — Current/Prev Week | 3411 | `inR(closeDate(v))` |
| Vacancy Dynamics — All Time/Period | 3488 | `inAtRange(closeDate(v))` |
| Avg TTF/TTH popup | 3604 | `closeDate(v)` |
| Avg TTF chart (rCVTTF) | 3644 | `closeDate(v)` |
| Avg TTH chart (rCVTTH) | 3710 | `closeDate(v)` |
| Closed Vacancies by Dept (rCVClosedCount) | 3815 | `cvInRange(closeDate(v),...)` |
| Charts Hires Week (rChartHires) | 2512 | `closeDate(v)` |

**Місця з прямим `v.fcd` або `v.hd`** — тільки для DISPLAY (НЕ фільтр):
- Колонка "Close date" у Hired This Week table → `fcdCell(v.fcd)` — показує саме fcd
- Колонки popup `Factual close date` і `Hired transition date` → показують окремо обидва поля
- Workload Active `closeDate(v)||v.sd` → fallback на start date для active vacancies (інша семантика)

**Тест-case REC-359** (RA sub-task hired): fcd="2026-05-08", hd="2026-05-15". У будь-якому періоді закриття рахується **за датою 05-08**. Якщо діапазон 05-11..05-17 — REC-359 НЕ потрапляє в жоден блок (consistent).

### Hired This Week table — нова структура колонок

Колонки тепер:
- Key
- **Type** (нова) — `<span>Vacancy</span>` (blue) або `<span>Rec Assign</span>` (purple), визначається через `_isRAany(v)`
- Vacancy (summary)
- Status
- Priority
- Seniority
- Recruiter
- Sourcer
- **Close date** — з `v.fcd` (НЕ closeDate, тільки фактичне поле, як попросив user)
- Dept / Team

**Прибрана колонка** `Hires` — суб-таски завжди 1, неінформативно.

**Sort buttons виправлено** — раніше `s2SortCol` оновлювався, але `positions.sort()` був hardcoded на priority. Тепер є generic comparator:

```javascript
const _s2cmp=(a,b,col)=>{
  if(col==='pr')   return (pOrd[a.pr]??9)-(pOrd[b.pr]??9);
  if(col==='type') return (_isRAany(a)?1:0)-(_isRAany(b)?1:0);
  if(col==='dt')   { const av=[a.t,a.sb].filter(Boolean).join(' / '), bv=[b.t,b.sb].filter(Boolean).join(' / '); return av<bv?-1:av>bv?1:0; }
  const av=a[col]??'', bv=b[col]??'';
  return av<bv?-1:av>bv?1:0;
};
```

**Badge "Hired This Week"** оновлено — показує 4 стати замість "N hires":
```
📂 N Vacancies · 🎯 N Hires needed · 📋 N Recruitment Assignments · 🎓 N Specialists needed
```

**Grey parent context row** тепер шукає parent в `ALL_VACS` АБО `RA` (з міткою `kind:'ra'`) — щоб RA sub-tasks показувались разом з parent context.

### Vacancy Dynamics block — фінальна структура (без Open side, без bcv1 badge)

- Header перейменовано: `Vacancy Dynamics: Hired Breakdown` + sub `by issue type · Open Position vs Recruitment Assignment`
- **Badge `bcv1` ВИДАЛЕНО** — раніше показував "N hired this week · M all time", тепер зайвий
- Trend chart code теж видалено (раніше викликав `openInWeek` яку я видалила при rewrite → ламав cascade)
- Inline `All time / Month / Quarter / Year` chips + Custom range + Apply в один рядок (`flex-wrap:nowrap` для Custom-групи щоб Apply не відривався)

### Hiring Sources — Seniority hide для RA

RA items не мають Seniority field. Тому при перемиканні на `Rec Assign`:
```javascript
const snLbl=document.getElementById('cv-src-sn-lbl');
const snSel=document.getElementById('cv-src-sn');
if(snLbl) snLbl.style.display=isVac?'':'none';
if(snSel){
  snSel.style.display=isVac?'':'none';
  if(!isVac) snSel.value=''; // reset stale OP-only seniority
}
```

Також у `rCVSources` для RA-режиму пропускається requirement `v.sn` (інакше всі RA items відсіялись би через null sn):
```javascript
const baseItems=typeScope.filter(v=>v.cs&&v.t&&(_cvSrcFilter==='ra'||v.sn));
```

### Файли, які змінювались у цій сесії

- `reports/REC_recruitment_dashboard.html` — popup стандартизація, type toggles у всі CV-блоки, closeDate всюди, Hired This Week table refactor, Vacancy Dynamics остаточна форма



