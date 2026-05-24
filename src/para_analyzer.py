"""PARA signal extraction and proposal report formatting."""

import re
from collections import Counter
from datetime import datetime

PARA_CATEGORIES = ["Projects", "Areas", "Resources", "Archives"]

_RESOURCE_TYPES = {"Document", "Spreadsheet", "Presentation", "PDF", "Form"}
_DOCUMENT_TYPES = _RESOURCE_TYPES - {"PDF", "Form"}

_REPORT_PREVIEW_LIMIT = 3

# ---------------------------------------------------------------------------
# Name-based token sets
# ---------------------------------------------------------------------------

_ARCHIVE_NAME_TOKENS = frozenset({
    "old", "archive", "archived", "backup", "bak", "deprecated",
    "legacy", "obsolete", "outdated", "retired", "completed",
    "done", "finished", "closed", "expired",
})
_PROJECT_NAME_TOKENS = frozenset({
    "draft", "wip", "todo", "proposal", "pitch", "plan", "launch",
    "campaign", "sprint", "milestone", "deliverable", "briefing",
})
_AREA_NAME_TOKENS = frozenset({
    "health", "finance", "finances", "budget", "family", "home",
    "career", "fitness", "habit", "journal", "routine",
})
_RESOURCE_NAME_TOKENS = frozenset({
    "template", "templates", "reference", "guide", "tutorial",
    "cheatsheet", "notes", "note", "checklist", "framework",
    "sop", "readme", "instructions", "recipe", "course", "reading", "research",
})

# Matches 4-digit years at least 2 years before the year this module was loaded
_YEAR_RE = re.compile(r"^\d{4}$")
_CURRENT_YEAR = datetime.now().year


def _is_old_year(token: str) -> bool:
    if not _YEAR_RE.match(token):
        return False
    year = int(token)
    return 1900 <= year <= _CURRENT_YEAR - 2


# ---------------------------------------------------------------------------
# Age / activity helpers
# ---------------------------------------------------------------------------

def _resolve_age_category(file_age_days: int) -> str:
    if file_age_days < 90:
        return "recent"
    if file_age_days < 365:
        return "moderate"
    if file_age_days < 730:
        return "old"
    return "very_old"


def _resolve_activity_signal(activity_level: str, mime_type_category: str) -> tuple[str, str]:
    """Return (suggested_category, signal_token) from time + type alone."""
    if activity_level == "inactive":
        return "Archives", "activity:inactive"
    if activity_level == "active":
        if mime_type_category in _DOCUMENT_TYPES:
            return "Projects", "activity:active+doc"
        return "Areas", "activity:active+other"
    if activity_level == "moderate":
        if mime_type_category in _RESOURCE_TYPES:
            return "Resources", "activity:moderate+resource_type"
        return "Areas", "activity:moderate+other"
    if activity_level == "unknown":
        return "Resources", "activity:unknown"
    return "Archives", "activity:fallback"


# ---------------------------------------------------------------------------
# Filename classifier (Improvement 2)
# ---------------------------------------------------------------------------

def _classify_from_name(name_keywords: list[str]) -> tuple[str | None, str | None]:
    """Return (category, signal_token) from filename tokens, or (None, None)."""
    for token in name_keywords:
        if token in _ARCHIVE_NAME_TOKENS:
            return "Archives", f"name_token:{token}"
        if _is_old_year(token):
            return "Archives", f"name_year:{token}"
    for token in name_keywords:
        if token in _PROJECT_NAME_TOKENS:
            return "Projects", f"name_token:{token}"
    for token in name_keywords:
        if token in _AREA_NAME_TOKENS:
            return "Areas", f"name_token:{token}"
    for token in name_keywords:
        if token in _RESOURCE_NAME_TOKENS:
            return "Resources", f"name_token:{token}"
    return None, None


# ---------------------------------------------------------------------------
# Folder context classifier (Improvement 3)
# ---------------------------------------------------------------------------

_FOLDER_PATH_SPLIT_RE = re.compile(r"[/\-_ ]+")

# Top-level PARA folder names take immediate precedence
_TOP_PARA_FOLDERS = {
    "projects": "Projects",
    "project": "Projects",
    "areas": "Areas",
    "area": "Areas",
    "resources": "Resources",
    "resource": "Resources",
    "archives": "Archives",
    "archive": "Archives",
}


def _classify_from_folder_path(folder_path: str) -> tuple[str | None, str | None]:
    """Return (category, signal_token) from the file's Drive folder chain, or (None, None)."""
    if not folder_path:
        return None, None

    # Top-level folder is the strongest signal
    top_folder = folder_path.split("/")[0].lower().strip()
    if top_folder in _TOP_PARA_FOLDERS:
        cat = _TOP_PARA_FOLDERS[top_folder]
        return cat, f"folder:{cat}"

    # Tokenise the full path
    tokens = [t for t in _FOLDER_PATH_SPLIT_RE.split(folder_path.lower()) if len(t) > 2]

    for token in tokens:
        if token in _ARCHIVE_NAME_TOKENS:
            return "Archives", f"folder_token:{token}"
        if _is_old_year(token):
            return "Archives", f"folder_year:{token}"
    for token in tokens:
        if token in _AREA_NAME_TOKENS:
            return "Areas", f"folder_token:{token}"
    for token in tokens:
        if token in _RESOURCE_NAME_TOKENS:
            return "Resources", f"folder_token:{token}"

    return None, None


# ---------------------------------------------------------------------------
# Anti-hoarding flag (Improvement 4)
# ---------------------------------------------------------------------------

_BINARY_MIME_TYPES = {"Image", "Video", "Audio", "Other"}
_LARGE_SIZE_CATEGORIES = {"large", "huge"}


def _flag_anti_hoarding(activity_level: str, size_category: str, mime_type_category: str) -> bool:
    return (
        activity_level == "inactive"
        and size_category in _LARGE_SIZE_CATEGORIES
        and mime_type_category in _BINARY_MIME_TYPES
    )


# ---------------------------------------------------------------------------
# Confidence scoring (Improvement 1)
# ---------------------------------------------------------------------------

def _score_confidence(signals_fired: list[str]) -> str:
    if len(signals_fired) >= 3:
        return "high"
    if len(signals_fired) == 2:
        return "medium"
    return "low"


# ---------------------------------------------------------------------------
# Main extraction entry point
# ---------------------------------------------------------------------------

def extract_para_signals(files: list[dict]) -> None:
    """Add a ``para_signals`` key to each enriched file dict in-place.

    Reads these keys from each file dict (all produced by file_organizer.py):
        activity_level, mime_type_category, file_age_days,
        name_keywords, folder_path, size_category

    Produces para_signals with:
        age_category, suggested_category, confidence, signals_fired,
        anti_hoarding_flag
    """
    for file in files:
        file_age_days: int = file.get("file_age_days", 0) or 0
        activity_level: str = file.get("activity_level", "unknown")
        mime_type_category: str = file.get("mime_type_category", "Other")
        name_keywords: list[str] = file.get("name_keywords", [])
        folder_path: str = file.get("folder_path", "")
        size_category: str = file.get("size_category", "unknown")

        signals_fired: list[str] = []

        # --- Name signal (highest intent signal after archive activity) ---
        name_category, name_signal = _classify_from_name(name_keywords)
        if name_signal:
            signals_fired.append(name_signal)

        # --- Folder context signal ---
        folder_category, folder_signal = _classify_from_folder_path(folder_path)
        if folder_signal:
            signals_fired.append(folder_signal)

        # --- Activity + type signal (always fires) ---
        activity_category, activity_signal = _resolve_activity_signal(activity_level, mime_type_category)
        signals_fired.append(activity_signal)

        # --- Determine final category (priority: name > folder > activity) ---
        # Exception: if activity says Archives, that always wins (inactive = done)
        if activity_level == "inactive":
            suggested_category = "Archives"
        elif name_category is not None:
            suggested_category = name_category
        elif folder_category is not None:
            suggested_category = folder_category
        else:
            suggested_category = activity_category

        # --- Anti-hoarding flag ---
        anti_hoarding = _flag_anti_hoarding(activity_level, size_category, mime_type_category)
        if anti_hoarding:
            signals_fired.append("anti_hoarding:large_inactive")

        # --- Confidence ---
        # Anti-hoarding always forces high (very clear signal)
        if anti_hoarding:
            confidence = "high"
        # All three independent signal sources agree → high
        elif name_category and folder_category and name_category == folder_category == activity_category:
            confidence = "high"
        else:
            confidence = _score_confidence(signals_fired)

        file["para_signals"] = {
            "age_category": _resolve_age_category(file_age_days),
            "suggested_category": suggested_category,
            "confidence": confidence,
            "signals_fired": signals_fired,
            "anti_hoarding_flag": anti_hoarding,
        }


# ---------------------------------------------------------------------------
# Cluster hint post-processing (Improvement 5)
# ---------------------------------------------------------------------------

def apply_cluster_hints(files: list[dict]) -> None:
    """Post-processing pass: low-confidence files inherit their folder's majority category."""
    folder_to_files: dict[str, list[dict]] = {}
    for f in files:
        path = f.get("folder_path", "")
        if path:
            folder_to_files.setdefault(path, []).append(f)

    for path, folder_files in folder_to_files.items():
        if len(folder_files) < 3:
            continue

        category_votes = Counter(
            f["para_signals"]["suggested_category"] for f in folder_files
        )
        majority_category, majority_count = category_votes.most_common(1)[0]

        if majority_count / len(folder_files) <= 0.5:
            continue

        for f in folder_files:
            signals = f["para_signals"]
            if (
                signals["confidence"] == "low"
                and signals["suggested_category"] != majority_category
            ):
                signals["suggested_category"] = majority_category
                signals["signals_fired"].append(f"cluster:majority({majority_category})")
                signals["confidence"] = "medium"


# ---------------------------------------------------------------------------
# Proposal report formatting
# ---------------------------------------------------------------------------

def format_proposal_report(plan: dict, files_index: dict) -> str:
    """Format a human-readable PARA organisation proposal report.

    Args:
        plan: Mapping of PARA category -> subfolder name -> list of file IDs.
        files_index: Mapping of file_id -> enriched file dict.

    Returns:
        Formatted report string ready to print to the terminal.
    """
    lines: list[str] = []

    lines.append("PROPOSED P.A.R.A. ORGANIZATION PLAN")
    lines.append("=====================================")

    total_files = sum(
        len(file_ids)
        for category in PARA_CATEGORIES
        for file_ids in plan.get(category, {}).values()
    )
    lines.append(f"Total files to move: {total_files}")
    lines.append("")

    for category in PARA_CATEGORIES:
        subfolders: dict = plan.get(category, {})
        category_total = sum(len(ids) for ids in subfolders.values())

        if category_total == 0:
            continue

        lines.append(f"\U0001f4c1 {category}/ ({category_total} files)")

        for subfolder_name, file_ids in subfolders.items():
            subfolder_total = len(file_ids)
            lines.append(f"   └─ {subfolder_name} ({subfolder_total} files)")

            shown = file_ids[:_REPORT_PREVIEW_LIMIT]
            for fid in shown:
                file_dict = files_index.get(fid)
                name = file_dict.get("name", "[unknown]") if file_dict else "[unknown]"
                c = file_dict.get("para_signals", {}).get("confidence", "") if file_dict else ""
                lines.append(f"      • {name}{f' [{c}]' if c else ''}")

            remaining = subfolder_total - len(shown)
            if remaining > 0:
                lines.append(f"      ... and {remaining} more")

        lines.append("")

    # Anti-hoarding section
    anti_hoarding_files = [
        f for f in files_index.values()
        if f.get("para_signals", {}).get("anti_hoarding_flag", False)
    ]
    if anti_hoarding_files:
        lines.append("⚠️  Large inactive files (digital hoarding candidates):")
        for f in anti_hoarding_files[:10]:
            size = f.get("size_category", "?")
            lines.append(f"   • {f.get('name', '[unknown]')} ({size})")
        if len(anti_hoarding_files) > 10:
            lines.append(f"   ... and {len(anti_hoarding_files) - 10} more")
        lines.append("")

    lines.append("=====================================")
    lines.append("Review the plan above. Reply 'yes' to execute or describe changes you want.")

    return "\n".join(lines)
