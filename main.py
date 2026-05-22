"""Google Drive PARA Organizer — entry point and Claude Code tool definitions.

Three public functions are exposed as tools for Claude Code:
    - get_drive_analysis()       : scan Drive and return enriched file data with PARA signals
    - preview_para_plan()        : format a proposed PARA plan for user review
    - execute_para_organization(): execute an approved plan on Google Drive

Module-level initialization runs once on import so the tools are immediately
usable when Claude Code loads this file.
"""

import sys
from collections import Counter

from src.google_drive_auth import GoogleDriveAuth
from src.file_organizer import GoogleDriveOrganizer
from src.para_analyzer import extract_para_signals, format_proposal_report

# ---------------------------------------------------------------------------
# Module-level initialization — runs once when main.py is imported
# ---------------------------------------------------------------------------

try:
    _auth = GoogleDriveAuth()
    _service = _auth.authenticate()
    _organizer = GoogleDriveOrganizer(_service)
except FileNotFoundError as exc:
    raise RuntimeError(
        f"Google Drive PARA Organizer failed to initialize: {exc}\n"
        "Fix the credentials issue above, then re-run."
    ) from exc


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _build_stats(enriched_files: list[dict]) -> dict:
    """Build aggregate statistics from enriched file list."""
    activity_counts = Counter(f.get("activity_level", "unknown") for f in enriched_files)
    mime_counts = Counter(f.get("mime_type_category", "Other") for f in enriched_files)
    suggested_counts = Counter(
        f.get("para_signals", {}).get("suggested_category", "Resources")
        for f in enriched_files
    )

    return {
        "total_files": len(enriched_files),
        "by_activity": dict(activity_counts),
        "by_type": dict(mime_counts),
        "suggested_para_distribution": dict(suggested_counts),
    }


# ---------------------------------------------------------------------------
# Tool 1 — Scan and analyse
# ---------------------------------------------------------------------------

def get_drive_analysis(recursive: bool = True, folder_id: str = "root") -> dict:
    """
    Scan Google Drive and return all files with PARA analysis signals.

    Returns dict with:
    - "files": list of enriched file dicts with para_signals
    - "stats": aggregate statistics
    - "files_index": dict mapping file_id -> file dict (for use with preview_para_plan)

    Call this first before proposing a PARA organization plan.
    """
    files = _organizer.get_all_files_recursive(
        folder_id=folder_id,
        max_depth=10 if recursive else 1,
    )

    # Enrich each file
    enriched = [_organizer.get_file_metadata_enriched(f) for f in files]

    # Add folder paths
    for f in enriched:
        f["folder_path"] = _organizer.get_folder_path(f)

    # Add PARA signals (returns None; mutates each file dict in place)
    extract_para_signals(enriched)

    # Build files_index for use with preview_para_plan
    files_index = {f["id"]: f for f in enriched}

    # Build stats
    stats = _build_stats(enriched)

    return {
        "files": enriched,
        "stats": stats,
        "files_index": files_index,
    }


# ---------------------------------------------------------------------------
# Tool 2 — Preview plan
# ---------------------------------------------------------------------------

def preview_para_plan(plan: dict, files_index: dict) -> str:
    """
    Format a proposed PARA organization plan for user review.

    Args:
        plan: dict mapping PARA categories to subfolders to file IDs, e.g.:
              {"Projects": {"Website": ["id1", "id2"]}, "Areas": {...}, ...}
        files_index: the "files_index" value returned by get_drive_analysis()

    Returns formatted string showing the proposed folder structure.
    Display this to the user and wait for their approval before executing.
    """
    return format_proposal_report(plan, files_index)


# ---------------------------------------------------------------------------
# Tool 3 — Execute plan
# ---------------------------------------------------------------------------

def execute_para_organization(plan: dict) -> dict:
    """
    Execute an approved PARA organization plan on Google Drive.

    ONLY call this after the user has reviewed and approved the plan from preview_para_plan().

    Args:
        plan: dict mapping PARA categories to subfolders to file IDs, e.g.:
              {"Projects": {"Website": ["id1", "id2"]}, "Areas": {...}, ...}

    Returns:
        {"folders_created": int, "files_moved": int, "errors": list[str]}
    """
    folders_created = 0
    files_moved = 0
    errors = []

    # Create PARA root folder (or use existing)
    try:
        para_root_id = _organizer.create_folder("PARA", "root")
    except Exception as exc:
        return {"folders_created": 0, "files_moved": 0, "errors": [f"Failed to create PARA root folder: {exc}"]}

    for category, subfolders in plan.items():
        try:
            category_id = _organizer.create_folder(category, para_root_id)
            folders_created += 1
        except Exception as exc:
            errors.append(f"Failed to create category folder '{category}': {exc}")
            continue

        for subfolder_name, file_ids in subfolders.items():
            try:
                subfolder_id = _organizer.create_folder(subfolder_name, category_id)
                folders_created += 1
            except Exception as exc:
                errors.append(f"Failed to create subfolder '{category}/{subfolder_name}': {exc}")
                continue

            for file_id in file_ids:
                file_name = file_id
                try:
                    file_meta = _service.files().get(
                        fileId=file_id, fields="name,parents"
                    ).execute()
                    file_name = file_meta.get("name", file_id)
                    old_parent = file_meta.get("parents", ["root"])[0]
                    success = _organizer.move_file(file_id, subfolder_id, old_parent)
                    if success:
                        files_moved += 1
                    else:
                        errors.append(f"Failed to move '{file_name}' ({file_id})")
                except Exception as exc:
                    errors.append(f"Error processing '{file_name}' ({file_id}): {exc}")

    return {
        "folders_created": folders_created,
        "files_moved": files_moved,
        "errors": errors,
    }


# ---------------------------------------------------------------------------
# Direct execution
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        files = _organizer.get_all_files_recursive(folder_id="root", max_depth=1)
        print(f"Connection OK — found {len(files)} files at root level")
    else:
        print("Google Drive PARA Organizer ready.")
        print("Use Claude Code in this directory and ask it to organize your Drive with PARA.")
        input("Press Ctrl+C to stop.")
