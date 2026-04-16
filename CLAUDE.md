# Project: Jira Reports for Creators Platform (PLAT)

## Контекст
Jira проєкт: **Creators Platform** (PLAT)
Board: https://newsiteam.atlassian.net/jira/software/c/projects/PLAT/boards/214
Cloud ID: `657e24cd-f643-4482-aba5-7e848607df28`

## Розробники
| Ім'я | Jira Account ID | Перший спринт |
|------|-----------------|---------------|
| Andrii Marusiak | `712020:bd62fda8-1ec1-4b0c-b5f7-2dedaed8e05c` | S22 |
| Yehor Kaliuzhnyi | `712020:8c65774d-e6bd-4da9-9940-be39f72bbf20` | S2 (дані з SP починаються з S5) |
| Oleksandr Menchynskyi | `712020:78328d5b-5094-4f6d-8241-ef34bd232852` | S16 |

## Jira Custom Fields
- **Story Points (ПРАВИЛЬНЕ ПОЛЕ)**: `customfield_10004` — це поле реально заповнене у задачах. Перевірено: S50 Andrii = 56 SP (збігається з eazyBI).
- **Story Points (старе/не використовувати)**: `customfield_11753` — дає занижені значення, часто null. НЕ ВИКОРИСТОВУВАТИ.
- **Sprint**: `customfield_10007`

## JQL для витягування даних
```
project = PLAT AND assignee = "{ACCOUNT_ID}" AND statusCategory = Done AND sprint in closedSprints() AND key > "PLAT-0" ORDER BY key ASC
```
- Поля: `["summary", "customfield_10004", "customfield_10007", "status"]`
- Пагінація: `key > "PLAT-XXXX"` (maxResults=100), повторювати поки результатів < 100
- Sprint: з масиву `customfield_10007` брати ОСТАННІЙ спринт зі `state: "closed"`

## Артефакти

### 1. PLAT_story_points_report.html
**Інтерактивний HTML-звіт** — лінійний графік "Resolved SP by Dev Team / All sprints"
- Dropdown для вибору розробника (Andrii / Yehor / Oleksandr)
- Chart.js + chartjs-plugin-datalabels
- **Кожна точка на графіку клікабельна** — веде на Jira JQL з усіма задачами за спринт
- **Sprint Notes секція** — редаговані коментарі під кожним спринтом
- Дані: story points (`customfield_10004`) по закритих спринтах
- Дані актуальні станом на: **2026-04-11**

### 2. PLAT_story_points_per_sprint.md
**Markdown-звіт** з таблицями story points по спринтах (ЗАСТАРІЛИЙ — використовує customfield_11753).

## Зведені дані Story Points по спринтах (customfield_10004)

### Andrii Marusiak (всього: 1354 SP, 242 задачі, спринти S22–S50)
S22:14, S23:55, S24:67, S25:10, S26:70, S27:21, S28:120, S29:43, S30:87, S31:20, S32:38, S33:9, S34:50, S35:48, S36:53, S37:46, S38:25, S39:59, S40:96, S41:102, S42:37, S43:26, S44:22, S45:57, S46:6, S47:41, S48:56, S49:20, S50:56

### Yehor Kaliuzhnyi (всього: 1752 SP, 432 задачі, спринти S2–S50)
S2:5, S5:8, S6:23, S7:26, S8:2, S9:71, S10:27, S11:19, S12:32, S16:0, S17:18, S18:20, S19:22, S20:18, S21:41, S22:21, S23:72, S24:59, S25:30, S26:57, S27:55, S28:56, S29:51, S30:56, S31:42, S32:37, S33:16, S34:88, S35:39, S36:80, S37:94, S38:28, S39:31, S40:55, S41:33, S42:11, S43:21, S44:25, S45:37, S46:45, S47:87, S48:43, S49:44, S50:107

### Oleksandr Menchynskyi (всього: 1341 SP, 467 задач, спринти S16–S50)
S16:12, S17:6, S18:50, S19:22, S20:14, S21:31, S22:26, S23:63, S24:47, S25:13, S26:42, S27:35, S28:63, S29:19, S30:76, S31:23, S32:45, S33:60, S34:47, S35:21, S36:31, S37:52, S38:32, S39:50, S40:87, S41:42, S42:35, S43:37, S44:27, S45:48, S46:66, S47:43, S48:34, S49:0, S50:42

## Посилання на задачі по спринтах (для побудови JQL-лінків)
Повні списки issue keys зберігаються у HTML-файлі `PLAT_story_points_report.html` в об'єкті `rawData`.
Формат лінку: `https://newsiteam.atlassian.net/issues/?jql=key%20in%20(PLAT-XXX%2CPLAT-YYY%2C...)`
