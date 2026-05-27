# 🗂️ Google Drive Organizer — P.A.R.A. Method with Claude Code

A system that uses Claude Code's intelligence to automatically organize your Google Drive files following **Tiago Forte's P.A.R.A. method**. Unlike traditional organizers, it proposes a complete plan for your approval before moving any file.

> Adapted from [tharlesamaro/google-drive-organizer](https://github.com/tharlesamaro/google-drive-organizer)

---

## 🎯 What is the P.A.R.A. Method?

P.A.R.A. is an organizational system created by Tiago Forte that divides everything into four categories:

| Category | What it is | Signals |
|----------|-----------|---------|
| **Projects** | Work with a specific outcome and deadline | Modified in the last 90 days, tied to a deliverable |
| **Areas** | Ongoing responsibilities with no defined end | Regularly edited, life domains (health, finances…) |
| **Resources** | Reference and consultation material | Rarely edited, serves as future reference |
| **Archives** | Inactive items from the other categories | Not modified in over 1 year |

### 📁 How the structure looks in Drive

```
📁 PARA/
├── 📁 Projects/
│   ├── 📁 Website-Redesign/
│   ├── 📁 Q4-Report/
│   └── 📁 App-Launch/
├── 📁 Areas/
│   ├── 📁 Finance/
│   ├── 📁 Health/
│   └── 📁 Career/
├── 📁 Resources/
│   ├── 📁 Templates/
│   ├── 📁 Research/
│   └── 📁 Courses/
└── 📁 Archives/
    ├── 📁 2023-Projects/
    └── 📁 Old-Work/
```

---

## ✨ What makes this project different

- 🧠 **Intelligent analysis**: Claude Code analyzes file metadata and usage patterns
- 👁️ **Review before execution**: Claude proposes the full plan and only executes after your approval
- 🏗️ **P.A.R.A. structure**: Organization based on a proven productivity methodology
- 🛡️ **100% safe**: Only moves files, never deletes

---

## ⚡ Getting Started

### 1. Clone the project

```bash
git clone https://github.com/your-username/google-drive-organizer-PARA.git
cd google-drive-organizer-PARA
pip install -r requirements.txt
```

### 2. Configure Google Drive credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or use an existing one)
3. Enable the **Google Drive API**
4. Create **OAuth 2.0** credentials for a Desktop application
5. Under **Test users**, add your Google account email
6. Download the JSON and rename it to `credentials.json`
7. Place the file in the project root folder

### 3. Test the connection

```bash
python main.py test
```

If you see `Connection OK — found N files at root level`, everything is working.

### 4. Run

```bash
python main.py
```

Then, in **Claude Code** (in the same directory), ask:

```
Organize my Google Drive using the P.A.R.A. method.
```

---

## 🔄 How the workflow works

```
1. ANALYZE   → Claude scans the entire Drive and analyzes the files
        ↓
2. PLAN      → Claude creates a P.A.R.A. plan based on each file's signals
        ↓
3. PREVIEW   → Claude displays the full plan for your review:
               📁 Projects/ (12 files)
                  └─ Website-Redesign (8 files)
                  └─ Q4-Report (4 files)
               📁 Areas/ (5 files)
                  └─ Finance (5 files)
               ...
        ↓
4. APPROVE   → You approve (or request adjustments)
        ↓
5. EXECUTE   → Claude moves all files into the P.A.R.A. structure
```

> **Important:** Claude never executes without your explicit approval in step 4.

---

## 🎮 Useful Claude Code prompts

```
# Full organization
Organize my Google Drive using the P.A.R.A. method.

# Analyze only, without organizing yet
Analyze my Drive and show me the file distribution by P.A.R.A. category.

# Test with a specific folder
Analyze only the "Documents" folder and suggest a P.A.R.A. organization.

# Adjust the plan
Move all files from "Finance" to Projects instead of Areas.
```

---

## 🔧 Technical details

### Tools exposed to Claude Code

```python
# Scans the Drive and returns files with P.A.R.A. signals
data = get_drive_analysis(recursive=True, folder_id="root")
# Returns: {"files": [...], "stats": {...}, "files_index": {...}}

# Formats the proposed plan for review
report = preview_para_plan(plan, files_index)

# Executes the approved plan
result = execute_para_organization(plan)
# Returns: {"folders_created": N, "files_moved": N, "errors": [...]}
```

### P.A.R.A. signals calculated per file

| Signal | Description |
|--------|-------------|
| `days_since_modified` | Days since last edit |
| `activity_level` | `active` / `moderate` / `inactive` |
| `mime_type_category` | Document / Spreadsheet / PDF / Image / … |
| `file_age_days` | Total age of the file |
| `name_keywords` | Keywords extracted from the filename |
| `suggested_category` | Automatic P.A.R.A. category suggestion |

---

## 🛡️ Security & Privacy

- 🔒 **Local credentials**: `credentials.json` and `token.json` stay only on your computer
- 🏠 **Data in Google**: Files remain in your Google Drive account
- 🚫 **Zero deletion**: The system only moves files
- 👁️ **Mandatory review**: You approve before any changes are made
- ↩️ **Reversible**: Changes can be manually undone in Google Drive

---

## 🔧 Troubleshooting

### Error 403: "The user does not have sufficient permissions"

1. In [Google Cloud Console](https://console.cloud.google.com/), go to **APIs & Services > Credentials**
2. Edit your OAuth 2.0 credentials
3. Under **Test users**, add your Google account email
4. Save the changes
5. Delete the `token.json` file (if it exists)
6. Run `python main.py test` again and complete the authorization

### "credentials.json not found"

- Make sure the file is in the project root folder (not in subfolders)
- The filename must be exactly `credentials.json`

### Claude Code cannot call the functions

- Check that `python main.py` is still running in the terminal
- Test with `python main.py test` before using Claude Code

### Authentication error after a long period of inactivity

- Delete the `token.json` file
- Run `python main.py` again to re-authenticate

---

## 📚 About the P.A.R.A. Method

P.A.R.A. was created by Tiago Forte and is described in detail in the book [*Building a Second Brain*](https://www.buildingasecondbrain.com/). The core idea is that any piece of information can be classified into just four categories, making organization simple and consistent over time.

---

**💡 The differentiator:** This project doesn't just organize — it organizes following a proven method, proposes the plan for you to review, and only executes with your approval.
