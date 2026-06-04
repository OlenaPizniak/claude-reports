#!/usr/bin/env python3
"""
Auto-updater for REC Recruitment Dashboard.

Fetches fresh data from Jira (project REC) and rewrites the data blocks
in reports/REC_recruitment_dashboard.html between AUTO_*_START / END markers.

Required env vars:
  JIRA_EMAIL       — Atlassian account email
  JIRA_API_TOKEN   — Atlassian API token (https://id.atlassian.com/manage/api-tokens)

Usage:
  JIRA_EMAIL=... JIRA_API_TOKEN=... python3 scripts/update_rec_dashboard.py
"""

import os
import re
import sys
import json
import base64
from datetime import datetime, timezone, timedelta
from urllib.request import Request, urlopen
from urllib.parse import urlencode
from urllib.error import HTTPError

# ── Configuration ───────────────────────────────────────────
JIRA_HOST = "https://newsiteam.atlassian.net"
PROJECT = "REC"
HTML_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "reports", "REC_recruitment_dashboard.html"
)

# Custom field IDs (verified against Jira metadata)
F = {
    'start_date':     'customfield_11223',
    'recruiter':      'customfield_13935',
    'seniority':      'customfield_22876',
    'reason':         'customfield_22877',
    'fcd':            'customfield_22878',
    'fcd_contact':    'customfield_23407',
    'hiring_manager': 'customfield_23509',
    'sourcer':        'customfield_23510',
    'num_hires':      'customfield_23545',
    'team':           'customfield_23547',
    'cand_source':    'customfield_24344',
    'cand_source_other': 'customfield_25662',  # text field, filled when Candidate Source = Other
    'num_specialists': 'customfield_25663',  # Recruitment Assignment: Number of specialists needed
    'end_date':       'customfield_11232',  # End date (available on Open Position + RA)
    'employee_status': 'customfield_23581',  # Staff / Non-staff / Expert
}

RA_EXTRA_FIELDS = [
    'customfield_25664',  # cf_cooperation (Type of cooperation)
    'customfield_25665',  # cf_cooperation_other
    'customfield_25666',  # cf_core_req
    'customfield_25667',  # cf_nice_req
    'customfield_25668',  # cf_duration
    'customfield_25669',  # cf_legal
    'customfield_25670',  # cf_nda
    'customfield_25671',  # cf_marketing
    'customfield_25672',  # cf_budget
    'customfield_25673',  # cf_payment
    'customfield_25674',  # cf_stages
]
ALL_FIELDS = ['summary', 'status', 'priority', 'issuetype', 'created',
              'parent', 'assignee'] + list(F.values()) + RA_EXTRA_FIELDS

# Ukrainian month names for header date
UA_MONTHS = ['січня', 'лютого', 'березня', 'квітня', 'травня', 'червня',
             'липня', 'серпня', 'вересня', 'жовтня', 'листопада', 'грудня']


# ── Auth ────────────────────────────────────────────────────
def get_auth_header():
    email = os.environ.get('JIRA_EMAIL')
    token = os.environ.get('JIRA_API_TOKEN')
    if not email or not token:
        sys.exit("ERROR: JIRA_EMAIL and JIRA_API_TOKEN env vars are required")
    return 'Basic ' + base64.b64encode(f"{email}:{token}".encode()).decode()


HEADERS = {
    'Accept': 'application/json',
    'Content-Type': 'application/json',
}


# ── Jira API ────────────────────────────────────────────────
def jira_search(jql, fields, max_results=100):
    """Search issues via the /search/jql endpoint (POST + nextPageToken pagination).

    The legacy /search endpoint was removed in 2025; this uses the new
    enhanced search API: https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issue-search/#api-rest-api-3-search-jql-post
    """
    headers = dict(HEADERS)
    headers['Authorization'] = get_auth_header()
    url = f"{JIRA_HOST}/rest/api/3/search/jql"
    all_issues = []
    next_token = None
    while True:
        body = {
            'jql': jql,
            'fields': fields,
            'maxResults': max_results,
        }
        if next_token:
            body['nextPageToken'] = next_token
        req = Request(url, data=json.dumps(body).encode('utf-8'),
                      headers=headers, method='POST')
        try:
            with urlopen(req, timeout=60) as resp:
                data = json.loads(resp.read())
        except HTTPError as e:
            err = e.read().decode('utf-8', errors='replace')
            sys.exit(f"Jira API error {e.code}: {err[:500]}")
        issues = data.get('issues', [])
        all_issues.extend(issues)
        next_token = data.get('nextPageToken')
        is_last = data.get('isLast', not next_token)
        if is_last or not next_token:
            break
    return all_issues


def fetch_hired_transition_date(issue_key):
    """Return YYYY-MM-DD of the most recent transition INTO 'Hired' status.

    Pages through /rest/api/3/issue/{key}/changelog and inspects status
    history items. None if the issue never transitioned to Hired.
    """
    headers = dict(HEADERS)
    headers['Authorization'] = get_auth_header()
    base = f"{JIRA_HOST}/rest/api/3/issue/{issue_key}/changelog"
    latest_date = None
    start_at = 0
    while True:
        url = base + '?' + urlencode({'startAt': start_at, 'maxResults': 100})
        req = Request(url, headers=headers)
        try:
            with urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read())
        except HTTPError as e:
            # Don't fail the whole run for one issue's changelog
            print(f"  ⚠ changelog fetch failed for {issue_key}: HTTP {e.code}")
            return None
        for entry in data.get('values', []):
            for item in entry.get('items', []):
                if item.get('field') == 'status' and item.get('toString') == 'Hired':
                    d = (entry.get('created') or '')[:10]
                    if d and (latest_date is None or d > latest_date):
                        latest_date = d
        got = len(data.get('values', []))
        if got == 0 or data.get('isLast', True):
            break
        start_at += got
        if start_at >= data.get('total', start_at):
            break
    return latest_date


# ── Field extractors ────────────────────────────────────────
def get_user(field):
    if isinstance(field, list) and field:
        return field[0].get('displayName')
    if isinstance(field, dict):
        return field.get('displayName')
    return None


def get_option(field):
    if isinstance(field, list) and field:
        return field[0].get('value')
    if isinstance(field, dict):
        return field.get('value')
    return None


def get_team(field):
    if not field:
        return (None, None)
    return (field.get('value'), (field.get('child') or {}).get('value'))


def get_date(s):
    """Trim ISO datetime to YYYY-MM-DD, or pass through plain dates."""
    if not s:
        return None
    return s[:10] if len(s) >= 10 else s


# ── JS literal serializer ──────────────────────────────────
def js_value(v):
    if v is None:
        return 'null'
    if isinstance(v, bool):
        return 'true' if v else 'false'
    if isinstance(v, (int, float)):
        # Avoid 1.0 → output as integer when whole
        if isinstance(v, float) and v.is_integer():
            return str(int(v))
        return str(v)
    if isinstance(v, str):
        return '"' + v.replace('\\', '\\\\').replace('"', '\\"') \
                     .replace('\n', '\\n').replace('\r', '') + '"'
    if isinstance(v, list):
        return '[' + ','.join(js_value(x) for x in v) + ']'
    if isinstance(v, dict):
        parts = []
        for k, val in v.items():
            # Unquoted key if it's a valid identifier; else quoted
            if re.match(r'^[A-Za-z_$][A-Za-z0-9_$]*$', str(k)):
                parts.append(f'{k}:{js_value(val)}')
            else:
                parts.append(f'"{k}":{js_value(val)}')
        return '{' + ','.join(parts) + '}'
    return 'null'


def js_array_decl(name, items, indent='  '):
    """const NAME=[\n  {…},\n  {…},\n];"""
    if not items:
        return f'const {name}=[];'
    body = ',\n'.join(indent + js_value(it) for it in items)
    return f'const {name}=[\n{body},\n];'


def js_object_decl(name, mapping, indent='  '):
    """const NAME={\n  "KEY":"value",\n  …\n};"""
    if not mapping:
        return f'const {name}={{}};'
    parts = []
    for k, v in mapping.items():
        parts.append(f'{indent}"{k}":{js_value(v)}')
    body = ',\n'.join(parts)
    return f'const {name}={{\n{body}\n}};'


# ── Builders ────────────────────────────────────────────────
def build_data():
    """Fetch from Jira and build all data structures."""
    print("→ Fetching open positions...")
    open_pos = jira_search(
        f'project = {PROJECT} AND issuetype = "Open position" AND status != Hired ORDER BY key DESC',
        ALL_FIELDS,
    )
    print(f"  got {len(open_pos)} open positions")

    print("→ Fetching active sub-tasks...")
    sub_tasks = jira_search(
        f'project = {PROJECT} AND issuetype = "Vacancy sub-task" AND status != Hired ORDER BY key DESC',
        ALL_FIELDS,
    )
    print(f"  got {len(sub_tasks)} active sub-tasks")

    print("→ Fetching active tasks...")
    tasks = jira_search(
        f'project = {PROJECT} AND issuetype = Task AND statusCategory != Done ORDER BY key DESC',
        ALL_FIELDS,
    )
    print(f"  got {len(tasks)} active tasks")

    # ── Recruitment Assignment + RA sub-task (issuetypes 17332 / 17365) ──
    # Added 2026-05-19. New consultant-tracking paradigm parallel to Open position.
    # Not yet rendered on dashboard — data captured into RA / RAS arrays for future use.
    print("→ Fetching active recruitment assignments...")
    ra_active = jira_search(
        f'project = {PROJECT} AND issuetype = "Recruitment Assignment" AND status != Hired ORDER BY key DESC',
        ALL_FIELDS,
    )
    print(f"  got {len(ra_active)} active recruitment assignments")

    print("→ Fetching active RA sub-tasks...")
    ras_active = jira_search(
        f'project = {PROJECT} AND issuetype = "Recruitment Assignment sub-task" AND status != Hired ORDER BY key DESC',
        ALL_FIELDS,
    )
    print(f"  got {len(ras_active)} active RA sub-tasks")

    # Closed items = status in (Hired, Done). Done was added to RA workflow on 2026-05-28
    # for tasks completed without a specific hire (e.g. consulting calls). Tasks always
    # had Done as the natural completion state but were previously excluded.
    print("→ Fetching all closed items (Hired + Done, positions + sub-tasks + RA + RA-sub + Tasks)...")
    hired = jira_search(
        f'project = {PROJECT} AND status in (Hired, Done) ORDER BY key DESC',
        ALL_FIELDS,
    )
    print(f"  got {len(hired)} closed items (Hired+Done combined)")

    print("→ Fetching changelog for each closed item (transition-to-Hired date)...")
    hired_transition = {}
    for issue in hired:
        key = issue['key']
        # Only fetch transition for items currently Hired — Done items don't have hired-transition
        status_name = (issue.get('fields', {}).get('status') or {}).get('name')
        if status_name == 'Hired':
            hd = fetch_hired_transition_date(key)
            hired_transition[key] = hd
    have_hd = sum(1 for v in hired_transition.values() if v)
    print(f"  got transition date for {have_hd} Hired items")

    # Build lookups
    SD, SN, RECR, SRCR = {}, {}, {}, {}
    for issue in open_pos + sub_tasks + hired:
        key = issue['key']
        fld = issue['fields']
        sd = fld.get(F['start_date'])
        if sd:
            SD[key] = sd
        # Open positions also have null start date — preserve in HTML if old data had it
        if F['start_date'] in fld and sd is None and key not in SD:
            SD[key] = None
        sn = get_option(fld.get(F['seniority']))
        if sn:
            SN[key] = sn
        rec = get_user(fld.get(F['recruiter']))
        if rec:
            RECR[key] = rec
        src = get_user(fld.get(F['sourcer']))
        if src:
            SRCR[key] = src

    # OP — open positions (compact view)
    OP = []
    for issue in open_pos:
        fld = issue['fields']
        t, sb = get_team(fld.get(F['team']))
        OP.append({
            'key': issue['key'],
            's': fld.get('summary'),
            'st': (fld.get('status') or {}).get('name'),
            'pr': (fld.get('priority') or {}).get('name'),
            'so': fld.get(F['hiring_manager']),
            're': None,
            'h': fld.get(F['num_hires']),
            'r': get_option(fld.get(F['reason'])),
            'es': get_option(fld.get(F['employee_status'])),
            't': t,
            'sb': sb,
            'cr': get_date(fld.get('created')),
        })

    # WP — week positions (full open positions with rec/src embedded)
    WP = []
    for issue in open_pos:
        fld = issue['fields']
        t, sb = get_team(fld.get(F['team']))
        WP.append({
            'key': issue['key'],
            's': fld.get('summary'),
            'st': (fld.get('status') or {}).get('name'),
            'pr': (fld.get('priority') or {}).get('name'),
            'sn': get_option(fld.get(F['seniority'])),
            'rec': get_user(fld.get(F['recruiter'])),
            'src': get_user(fld.get(F['sourcer'])),
            'sd': fld.get(F['start_date']),
            'h': fld.get(F['num_hires']),
            'es': get_option(fld.get(F['employee_status'])),
            't': t,
            'sb': sb,
            'cr': get_date(fld.get('created')),
        })

    # ST — active sub-tasks
    ST = []
    for issue in sub_tasks:
        fld = issue['fields']
        parent = fld.get('parent')
        pk = parent.get('key') if parent else None
        ST.append({
            'key': issue['key'],
            'pk': pk,
            's': fld.get('summary'),
            'st': (fld.get('status') or {}).get('name'),
            'sd': fld.get(F['start_date']),
            'rec': get_user(fld.get(F['recruiter'])),
            'src': get_user(fld.get(F['sourcer'])),
        })

    # TASKS — active tasks
    TASKS = []
    for issue in tasks:
        fld = issue['fields']
        asgn_obj = fld.get('assignee')
        asgn = asgn_obj.get('displayName') if asgn_obj else None
        TASKS.append({
            'key': issue['key'],
            's': fld.get('summary'),
            'st': (fld.get('status') or {}).get('name'),
            'pr': (fld.get('priority') or {}).get('name'),
            'asgn': asgn,
            'sd': fld.get(F['start_date']),
        })

    # Map Jira issuetype name → dashboard kind (used to split OP vs RA in Vacancy Dynamics).
    # 'op'      = Open position
    # 'op_sub'  = Vacancy sub-task
    # 'ra'      = Recruitment Assignment
    # 'ra_sub'  = Recruitment Assignment sub-task
    # 'task'    = Task (only Done status from this fetch — active tasks come via tasks query)
    _KIND = {
        'Open position': 'op',
        'Vacancy sub-task': 'op_sub',
        'Recruitment Assignment': 'ra',
        'Recruitment Assignment sub-task': 'ra_sub',
        'Task': 'task',
    }

    # HW — Closed items (Hired + Done) compact format used by Workload Hired section
    HW = []
    for issue in hired:
        fld = issue['fields']
        issuetype = (fld.get('issuetype') or {}).get('name')
        kind = _KIND.get(issuetype, 'op')
        status_name = (fld.get('status') or {}).get('name')  # 'Hired' or 'Done'
        # Keep legacy `type` for backward-compat with existing HTML callers.
        typ = 'subtask' if kind in ('op_sub', 'ra_sub') else 'position'
        # For RA-specific items use customfield_25663 (Number of specialists needed) as hires count.
        h_field = F['num_specialists'] if kind in ('ra', 'ra_sub') else F['num_hires']
        parent = fld.get('parent')
        pk = parent.get('key') if parent else None
        t, sb = get_team(fld.get(F['team']))
        item = {
            'key': issue['key'],
            's': fld.get('summary'),
            'type': typ,
            'kind': kind,
            'st': status_name,  # 'Hired' or 'Done' — for status filter in dashboard
            'pr': (fld.get('priority') or {}).get('name'),
            'sn': get_option(fld.get(F['seniority'])),
            'rec': get_user(fld.get(F['recruiter'])),
            'src': get_user(fld.get(F['sourcer'])),
            'fcd': fld.get(F['fcd']),
            'hd': hired_transition.get(issue['key']),
            'sd': fld.get(F['start_date']),
            'ed': fld.get(F['end_date']),
            'fcd_c': fld.get(F['fcd_contact']),
            'h': fld.get(h_field) or 1,
            't': t,
            'sb': sb,
        }
        if pk:
            item['pk'] = pk
        HW.append(item)

    # CV — all closed items (Hired + Done) with full schema (Closed Vacancies tab)
    CV = []
    for issue in hired:
        fld = issue['fields']
        issuetype = (fld.get('issuetype') or {}).get('name')
        kind = _KIND.get(issuetype, 'op')
        status_name = (fld.get('status') or {}).get('name')
        typ = 'subtask' if kind in ('op_sub', 'ra_sub') else 'position'
        h_field = F['num_specialists'] if kind in ('ra', 'ra_sub') else F['num_hires']
        parent = fld.get('parent')
        pk = parent.get('key') if parent else None
        t, sb = get_team(fld.get(F['team']))
        CV.append({
            'key': issue['key'],
            'type': typ,
            'kind': kind,
            'st': status_name,  # 'Hired' or 'Done'
            's': fld.get('summary'),
            'sd': fld.get(F['start_date']),
            'ed': fld.get(F['end_date']),
            'cr': get_date(fld.get('created')),
            'fcd': fld.get(F['fcd']),
            'hd': hired_transition.get(issue['key']),
            'fcd_c': fld.get(F['fcd_contact']),
            'sn': get_option(fld.get(F['seniority'])),
            'rec': get_user(fld.get(F['recruiter'])),
            'src': get_user(fld.get(F['sourcer'])),
            'pr': (fld.get('priority') or {}).get('name'),
            'h': fld.get(h_field) or 1,
            't': t,
            'sb': sb,
            'cs': get_option(fld.get(F['cand_source'])),
            'cs_other': fld.get(F['cand_source_other']) or None,
            'pk': pk,
        })

    # ── RA — Recruitment Assignments (active, consultant track) ──
    # Schema is intentionally close to OP so future dashboard blocks can reuse helpers.
    # Extra RA-only fields stored as cf-prefixed keys (cf_cooperation, cf_budget, etc).
    RA = []
    for issue in ra_active:
        fld = issue['fields']
        t, sb = get_team(fld.get(F['team']))
        RA.append({
            'key': issue['key'],
            's': fld.get('summary'),
            'st': (fld.get('status') or {}).get('name'),
            'pr': (fld.get('priority') or {}).get('name'),
            'sn': get_option(fld.get(F['seniority'])),
            'rec': get_user(fld.get(F['recruiter'])),
            'src': get_user(fld.get(F['sourcer'])),
            'sd': fld.get(F['start_date']),
            'ed': fld.get('customfield_11232'),  # End date (RA-only)
            'fcd_c': fld.get(F['fcd_contact']),
            'h': fld.get('customfield_25663') or 1,  # Number of specialists needed
            't': t,
            'sb': sb,
            'cr': get_date(fld.get('created')),
            'cf_cooperation': get_option(fld.get('customfield_25664')),
            'cf_cooperation_other': fld.get('customfield_25665'),
            'cf_core_req': fld.get('customfield_25666'),
            'cf_nice_req': fld.get('customfield_25667'),
            'cf_duration': fld.get('customfield_25668'),
            'cf_legal': get_option(fld.get('customfield_25669')),
            'cf_nda': get_option(fld.get('customfield_25670')),
            'cf_marketing': get_option(fld.get('customfield_25671')),
            'cf_budget': fld.get('customfield_25672'),
            'cf_payment': get_option(fld.get('customfield_25673')),
            'cf_stages': fld.get('customfield_25674'),
        })

    # ── RAS — Recruitment Assignment sub-tasks (active) ──
    RAS = []
    for issue in ras_active:
        fld = issue['fields']
        parent = fld.get('parent')
        pk = parent.get('key') if parent else None
        t, sb = get_team(fld.get(F['team']))
        RAS.append({
            'key': issue['key'],
            'pk': pk,
            's': fld.get('summary'),
            'st': (fld.get('status') or {}).get('name'),
            'pr': (fld.get('priority') or {}).get('name'),
            'sn': get_option(fld.get(F['seniority'])),
            'rec': get_user(fld.get(F['recruiter'])),
            'src': get_user(fld.get(F['sourcer'])),
            'sd': fld.get(F['start_date']),
            't': t,
            'sb': sb,
            'cf_cooperation': get_option(fld.get('customfield_25664')),
        })

    return {
        'SD': SD, 'SN': SN, 'RECR': RECR, 'SRCR': SRCR,
        'OP': OP, 'WP': WP, 'ST': ST, 'TASKS': TASKS,
        'HW': HW, 'CV': CV,
        'RA': RA, 'RAS': RAS,
    }


# ── HTML rewriting ──────────────────────────────────────────
def replace_marker_block(text, start_re, end_re, new_inner):
    # Capture start marker (including trailing comment text) and end marker as groups
    pattern = re.compile('(' + start_re + ')' + r'.*?' + '(' + end_re + ')', re.DOTALL)
    if not pattern.search(text):
        sys.exit(f"Marker pair not found in HTML: {start_re} … {end_re}")
    return pattern.sub(lambda m: m.group(1) + '\n' + new_inner + '\n' + m.group(2),
                       text, count=1)


def rewrite_html(data):
    with open(HTML_PATH, 'r', encoding='utf-8') as f:
        html = f.read()

    # ── Block 1: main data (SD, SN, OP, HW, WP, ST, RECR, SRCR, TASKS) ──
    # Keep original headers + fresh data
    main_block = '\n'.join([
        '// Start dates from Jira (customfield_11223) for all Open Positions',
        js_object_decl('SD', data['SD']),
        '// Seniority from Jira (customfield_22876) for all Open Positions',
        js_object_decl('SN', data['SN']),
        js_array_decl('OP', data['OP']),
        '// Hired vacancies/sub-tasks (status=Hired) from Jira',
        js_array_decl('HW', data['HW']),
        '// Week positions with full fields (Recruiter=customfield_13935, Sourcer=customfield_23510, StartDate=customfield_11223)',
        js_array_decl('WP', data['WP']),
        '// Vacancy sub-tasks — full list, fresh from Jira (statusCategory != Done)',
        js_array_decl('ST', data['ST']),
        '// Recruiter lookup (customfield_13935) — fresh from Jira',
        js_object_decl('RECR', data['RECR']),
        '// Sourcer lookup (customfield_23510) — fresh from Jira',
        js_object_decl('SRCR', data['SRCR']),
        '',
        '// Task issues (issuetype=Task, not Done) — fresh from Jira',
        js_array_decl('TASKS', data['TASKS']),
    ])

    html = replace_marker_block(
        html,
        r'// <<<AUTO_DATA_START>>>[^\n]*',
        r'// <<<AUTO_DATA_END>>>',
        main_block,
    )

    # ── Block 2: CV ──
    cv_block = '\n'.join([
        '// All Hired vacancies (positions + sub-tasks) — from Jira',
        '// Fields: sd (Start date), fcd (Factual close date), fcd_c (First contact date),',
        '//         sn (Seniority), t (Department), sb (Sub-team), cs (Candidate Source)',
        js_array_decl('CV', data['CV']),
    ])

    html = replace_marker_block(
        html,
        r'// <<<AUTO_CV_START>>>[^\n]*',
        r'// <<<AUTO_CV_END>>>',
        cv_block,
    )

    # ── Block 4: RA (Recruitment Assignment + sub-tasks) ──
    # Added 2026-05-19. Not yet rendered on dashboard but data is captured for
    # future consultant-tracking blocks/tab. Markers are optional — if absent,
    # block is silently skipped (graceful degradation).
    ra_block = '\n'.join([
        '// Recruitment Assignments (issuetype=Recruitment Assignment, not Hired) — consultant track',
        '// Schema: see SKILL.md "Recruitment Assignment structure" section',
        js_array_decl('RA', data['RA']),
        '// Recruitment Assignment sub-tasks (issuetype=Recruitment Assignment sub-task, not Hired)',
        js_array_decl('RAS', data['RAS']),
    ])

    # Optional marker block — skip with warning if dashboard doesn't have markers yet.
    if re.search(r'// <<<AUTO_RA_START>>>', html):
        html = replace_marker_block(
            html,
            r'// <<<AUTO_RA_START>>>[^\n]*',
            r'// <<<AUTO_RA_END>>>',
            ra_block,
        )
    else:
        print(f"  (info: AUTO_RA markers not in HTML yet — RA/RAS arrays skipped, "
              f"{len(data['RA'])} RA + {len(data['RAS'])} RAS captured but not embedded)")

    # ── Block 3: header date ──
    now_kyiv = datetime.now(timezone(timedelta(hours=3)))  # Kyiv ≈ UTC+3
    date_str = f"Дані: {now_kyiv.day} {UA_MONTHS[now_kyiv.month - 1]} {now_kyiv.year}, оновлено {now_kyiv:%H:%M} (Kyiv)"

    html = re.sub(
        r'<!--<<<AUTO_DATE_START>>>-->.*?<!--<<<AUTO_DATE_END>>>-->',
        f'<!--<<<AUTO_DATE_START>>>-->{date_str}<!--<<<AUTO_DATE_END>>>-->',
        html,
        flags=re.DOTALL,
        count=1,
    )

    with open(HTML_PATH, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"✓ HTML rewritten: {HTML_PATH}")


# ── Main ────────────────────────────────────────────────────
def main():
    print(f"Updating REC dashboard from {JIRA_HOST}/projects/{PROJECT}")
    data = build_data()
    print(f"\nSummary:")
    print(f"  OP   (open positions):    {len(data['OP'])}")
    print(f"  WP   (week positions):    {len(data['WP'])}")
    print(f"  ST   (active sub-tasks):  {len(data['ST'])}")
    print(f"  TASKS (active tasks):     {len(data['TASKS'])}")
    print(f"  HW   (hired all-time):    {len(data['HW'])}")
    print(f"  CV   (closed vacancies):  {len(data['CV'])}")
    print(f"  SD   (start dates):       {len(data['SD'])}")
    print(f"  SN   (seniorities):       {len(data['SN'])}")
    print(f"  RECR (recruiters):        {len(data['RECR'])}")
    print(f"  SRCR (sourcers):          {len(data['SRCR'])}")
    rewrite_html(data)


if __name__ == '__main__':
    main()
