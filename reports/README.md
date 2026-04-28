# REC Recruitment Dashboard

Live, auto-updating dashboard for the **Recruitment** project (REC) on
[newsiteam.atlassian.net](https://newsiteam.atlassian.net/jira/software/projects/REC/boards/214).

**File:** [`REC_recruitment_dashboard.html`](./REC_recruitment_dashboard.html)
**Public URL** (after enabling GitHub Pages): `https://OlenaPizniak.github.io/claude-reports/reports/REC_recruitment_dashboard.html`
**Password:** `RECrec1` *(stored in `sessionStorage` after first login)*

## Tabs

| Tab | What's inside |
|-----|---------------|
| 👥 **Workload** | Active workload by recruiter/sourcer + Hired (with period filter & presets) |
| 📊 **Open Vacancies** | KPIs · Active vacancies this week · Per-department/team breakdowns · 30+ days at-risk roles · Reason-for-opening matrix |
| ✅ **Closed Vacancies** | Vacancy Dynamics (Open vs Hired) · Hired This Week · Avg TTF/TTH by department · Closed count (Month/Quarter/Year) · Hiring Sources by department/seniority |

All period filters have quick-pick chips: **This week / Last week / This month / Last month**.

## Auto-update from Jira

Every hour a GitHub Action runs [`scripts/update_rec_dashboard.py`](../scripts/update_rec_dashboard.py)
which fetches fresh data from Jira and rewrites the data blocks inside the HTML
between `// <<<AUTO_*_START>>>` / `// <<<AUTO_*_END>>>` markers, then commits & pushes.

### One-time setup (only once, by repo owner)

1. **Generate a Jira API token**
   - Go to <https://id.atlassian.com/manage-profile/security/api-tokens>
   - Click **Create API token** → name it `rec-dashboard-bot`
   - Copy the token value (it's shown only once)

2. **Add secrets in GitHub**
   - Open <https://github.com/OlenaPizniak/claude-reports/settings/secrets/actions>
   - Add two **repository secrets**:
     - `JIRA_EMAIL` — your Atlassian email
     - `JIRA_API_TOKEN` — the token from step 1

3. **GitHub Pages is already enabled** for this repo (from `OKR Dashboard`)
   - Public URL: `https://olenapizniak.github.io/claude-reports/reports/REC_recruitment_dashboard.html`
   - No action needed — it picks up the new file automatically after each push

4. **Trigger the first auto-update**
   - Open <https://github.com/OlenaPizniak/claude-reports/actions/workflows/update-rec-dashboard.yml>
   - Click **Run workflow** → **Run workflow** (manual run)
   - The workflow will fetch fresh data and push the updated HTML

### Schedule

Defined in [`.github/workflows/update-rec-dashboard.yml`](../.github/workflows/update-rec-dashboard.yml):

- Cron: `7 * * * *` — runs at HH:07 every hour, UTC
- Manual: `workflow_dispatch` enabled

To change frequency, edit the `cron:` line. Common patterns:
| Frequency | Cron expression |
|-----------|-----------------|
| Every 30 min | `*/30 * * * *` |
| Every 6 hours | `0 */6 * * *` |
| Daily at 8 AM Kyiv (06 UTC) | `0 6 * * *` |
| Weekdays 8–20 Kyiv every 30 min | `*/30 6-18 * * 1-5` |

### Run locally (testing)

```bash
export JIRA_EMAIL="your.email@betterme.world"
export JIRA_API_TOKEN="ATATT3xFfGF…"
python3 scripts/update_rec_dashboard.py
```

This rewrites `reports/REC_recruitment_dashboard.html` in place. Open it in a browser to verify.

## Data flow

```
Jira (newsiteam.atlassian.net)
  ↓ REST API (Basic Auth: email + token)
update_rec_dashboard.py
  ↓ rebuilds: SD, SN, OP, HW, WP, ST, RECR, SRCR, TASKS, CV
  ↓ replaces between marker comments
REC_recruitment_dashboard.html
  ↓ commit & push (only if data changed)
GitHub Pages
```

## Custom field reference

| JS short | Jira field | ID |
|----------|------------|-----|
| `sd` | Start date | `customfield_11223` |
| `rec` | Recruiter | `customfield_13935` |
| `sn` | Seniority | `customfield_22876` |
| `r` | Reason for opening | `customfield_22877` |
| `fcd` | Factual close date | `customfield_22878` |
| `fcd_c` | First contact date | `customfield_23407` |
| `so` | Hiring Manager | `customfield_23509` |
| `src` | Sourcer | `customfield_23510` |
| `h` | Number of hires | `customfield_23545` |
| `t` / `sb` | Team and subteams | `customfield_23547` (cascading) |
| `cs` | Candidate Source | `customfield_24344` |

## Troubleshooting

- **Workflow fails with 401**: token is invalid/expired — regenerate and update `JIRA_API_TOKEN` secret.
- **Workflow fails with 403**: account doesn't have permission for the REC project.
- **HTML breaks after update**: check the workflow run log; the marker block may have been corrupted. Restore from previous commit:
  ```bash
  git log --oneline -- reports/REC_recruitment_dashboard.html
  git checkout <good-sha> -- reports/REC_recruitment_dashboard.html
  ```
- **Need to pause auto-updates**: comment out the `schedule:` line in the workflow YAML.
