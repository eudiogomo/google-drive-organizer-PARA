# Google Drive PARA Organizer — Claude Code Instructions

This file instructs Claude Code on how to organize Google Drive files using the PARA method.
Read every section before starting any organization task.

---

## 1. Setup (one-time)

Before using this project, complete the following steps once:

### 1.1 Create OAuth2 Credentials in Google Cloud Console

1. Go to [https://console.cloud.google.com](https://console.cloud.google.com) and create a new project (or select an existing one).
2. Navigate to **APIs & Services > Library** and enable the **Google Drive API**.
3. Navigate to **APIs & Services > Credentials** and click **Create Credentials > OAuth 2.0 Client ID**.
4. Choose **Desktop app** as the application type.
5. Go to **APIs & Services > OAuth consent screen** and add your Google account as a **Test user**.
6. Download the credentials JSON file.

### 1.2 Place Credentials at the Project Root

- Rename the downloaded file to `credentials.json`.
- Place it at the project root: `google-drive-organizer-PARA/credentials.json`.

### 1.3 Install Dependencies

```bash
pip install -r requirements.txt
```

### 1.4 Verify the Connection

```bash
python main.py test
```

This will open a browser window for OAuth2 authorization on the first run. After authorizing, a `token.json` file is saved locally. Subsequent runs use this token automatically.

---

## 2. How to Use

Follow these steps every time you want to organize your Drive:

1. **Start the server:** Open a terminal in the project root and run:
   ```bash
   python main.py
   ```
   Keep this terminal running while you work with Claude Code.

2. **Open Claude Code** in this same directory (`google-drive-organizer-PARA`).

3. **Ask Claude to organize your Drive**, for example:
   - "Organize my Google Drive using the PARA method."
   - "Analyze my Drive and suggest a PARA organization plan."

Claude Code will call the available tools, present a preview plan, and wait for your approval before making any changes.

---

## 3. The P.A.R.A. Method

PARA is a four-category system for organizing digital information. Each category has a distinct purpose.

### Projects

**Definition:** Work with a specific outcome and a clear end date.

- **Signs a file belongs here:**
  - Modified in the last 90 days (`activity_level == "active"`)
  - Clearly tied to a deliverable or milestone
  - Has a defined finish line

- **Examples of subcategory names:**
  `Website-Redesign`, `Book-Writing`, `Q4-Report`, `App-Launch`, `Marketing-Campaign`

- **Naming rule:** Use the project name, keep it short and specific.

---

### Areas

**Definition:** Ongoing responsibilities with no end date.

- **Signs a file belongs here:**
  - Regularly edited or referenced over a long period
  - Represents a continuous life or work domain
  - No clear "done" state

- **Examples of subcategory names:**
  `Health`, `Finance`, `Career`, `Home`, `Family`, `Learning`, `Personal-Development`

- **Naming rule:** Use the area or domain name.

---

### Resources

**Definition:** Reference material and topics of interest, consulted but not actively worked on.

- **Signs a file belongs here:**
  - Not actively edited (moderate or unknown activity)
  - Serves as reference, template, or documentation
  - Useful to keep but not tied to a current project or area

- **Examples of subcategory names:**
  `Templates`, `Research`, `Inspiration`, `Notes`, `Courses`, `Recipes`, `Reading-List`

- **Naming rule:** Use the topic or resource type.

---

### Archives

**Definition:** Inactive items from the other three categories — completed projects, outdated material, or anything no longer in use.

- **Signs a file belongs here:**
  - Not modified in over 1 year (`activity_level == "inactive"`)
  - Completed project deliverables
  - Outdated or superseded material

- **Examples of subcategory names:**
  `2023-Projects`, `Old-Work`, `Completed-Courses`, `2022-Finance`

- **Naming rule:** Use a year prefix or status prefix to indicate the archived period.

---

## 4. Classification Signals and Tie-breaking Rules

Each file has a `para_signals` dict with these fields:

| Field | Type | Description |
|---|---|---|
| `suggested_category` | string | The recommended PARA category after all signals are applied |
| `confidence` | `"high"` / `"medium"` / `"low"` | How certain the classification is |
| `signals_fired` | list of strings | Which signals contributed (e.g. `"activity:inactive"`, `"name_token:old"`, `"folder:Archives"`) |
| `anti_hoarding_flag` | bool | True when the file is a large, inactive binary — a strong delete/archive candidate |
| `age_category` | string | `recent` / `moderate` / `old` / `very_old` |

### Signal priority (the classifier applies these in order)

1. **`activity_level == "inactive"`** (not modified in >1 year) → **Archives** *(always wins — overrides all other signals)*
2. **Filename tokens** — file contains words like `old`, `backup`, `template`, `draft`, `budget`, etc. → category based on the token group (see table below)
3. **Folder context** — file lives inside a folder whose name matches a PARA category or domain keyword → inherit that category
4. **Activity + type fallback:**
   - `active` + document/spreadsheet/presentation → **Projects**
   - `active` + any other type → **Areas**
   - `moderate` + document/spreadsheet/presentation/PDF/form → **Resources**
   - `moderate` + any other type → **Areas**
   - `unknown` → **Resources**

### Filename token groups

| Token group | Examples | Category |
|---|---|---|
| Archive | `old`, `backup`, `deprecated`, `legacy`, `done`, `finished`, `retired`, year ≤ 2 years ago | Archives |
| Project | `draft`, `wip`, `proposal`, `launch`, `campaign`, `sprint`, `milestone` | Projects |
| Area | `health`, `finance`, `family`, `career`, `habit`, `journal` | Areas |
| Resource | `template`, `reference`, `guide`, `notes`, `checklist`, `tutorial`, `recipe`, `course` | Resources |

### How to use `confidence` when building the plan

- **`confidence == "high"`** — treat as settled; include in plan directly without review
- **`confidence == "medium"`** — review only if the assignment looks surprising
- **`confidence == "low"`** — surface these to the user; ask for guidance when ambiguous

### Anti-hoarding candidates

Files where `anti_hoarding_flag == True` are large inactive binaries (images, videos, audio over 10 MB not modified in over a year). The preview report shows these in a dedicated section. When presenting the plan, highlight these and suggest the user consider deleting them rather than just archiving.

---

## 5. Mandatory Workflow

Claude MUST follow this exact four-step workflow. Do not skip or reorder steps.

```
Step 1 — Analyze
  Call get_drive_analysis() and wait for results.
  Inspect the returned stats to understand the Drive's composition
  (total files, breakdown by PARA category, activity levels, file types).

Step 2 — Plan
  Using the returned files list and para_signals.suggested_category,
  build a plan dict that groups every file into PARA subcategories.

  Plan format:
  {
    "Projects": {
      "Subcategory-Name": ["file_id_1", "file_id_2"]
    },
    "Areas": {
      "Subcategory-Name": ["file_id_3"]
    },
    "Resources": {
      "Subcategory-Name": ["file_id_4", "file_id_5"]
    },
    "Archives": {
      "Subcategory-Name": ["file_id_6"]
    }
  }

  Rules for building the plan:
  - Use para_signals.suggested_category as the primary assignment for each file.
  - For high-confidence files, accept the suggested_category directly.
  - For low-confidence files, apply the tie-breaking rules in Section 4 and use
    para_signals.signals_fired to understand why the classifier chose what it chose.
  - Group related files into the same subcategory; use folder_path as a clustering hint.
  - Name subcategories in English using PascalCase or Kebab-Case.
  - Every file must appear in exactly one subcategory.
  - Subcategory names must be filesystem-safe (no special characters).
  - Check stats.by_confidence from Step 1 — report how many files are high/medium/low
    confidence before presenting the plan.
  - Highlight anti_hoarding_flag == True files: mention them to the user as candidates
    for deletion (they will still be moved to Archives in the plan).

Step 3 — Preview
  Call preview_para_plan(plan, files_index) with the plan dict and
  the files_index returned by get_drive_analysis().
  Display the formatted result to the user clearly.

  *** STOP HERE. ***
  Wait for the user's explicit approval ("yes", "go ahead", "execute", etc.)
  before proceeding to Step 4.
  Do NOT call execute_para_organization without approval.

Step 4 — Execute (only after explicit user approval)
  Call execute_para_organization(plan).
  Report the results to the user:
    - Number of folders created
    - Number of files moved
    - Any errors encountered
```

---

## 6. Subcategory Naming Guidelines

- **Language:** English only.
- **Case style:** PascalCase (`WebsiteRedesign`) or Kebab-Case (`Website-Redesign`). Be consistent within a session.
- **Allowed characters:** letters, digits, hyphens (`-`), and underscores (`_`). No spaces or special characters.
- **Length:** Descriptive but concise — 2 to 4 words maximum.

| Good examples       | Bad examples |
|---------------------|--------------|
| `Q4-Report`         | `misc`       |
| `Health`            | `other`      |
| `Marketing-Templates` | `stuff`   |
| `2023-Old-Projects` | `files`      |
| `WebsiteRedesign`   | `new folder` |

---

## 7. Important Notes

- **Files are MOVED, never deleted.** The original file is relocated inside a new folder structure; nothing is permanently removed.
- **Root folder:** The tool creates a `PARA/` folder at the root of your Google Drive. All four category folders (`Projects`, `Areas`, `Resources`, `Archives`) are created inside it.
- **Verify the connection at any time:**
  ```bash
  python main.py test
  ```
- **Authentication errors:** If you see an auth error or token expiry message, delete `token.json` from the project root and re-run `python main.py`. A new browser authorization window will appear.
- **Partial runs:** If execution is interrupted, re-run the full workflow from Step 1. Files already moved will not be moved again (they will no longer appear at their original location).
