"""PARA signal extraction and proposal report formatting."""

PARA_CATEGORIES = ["Projects", "Areas", "Resources", "Archives"]

_DOCUMENT_TYPES = {"Document", "Spreadsheet", "Presentation"}
_RESOURCE_TYPES = {"Document", "Spreadsheet", "Presentation", "PDF", "Form"}


def _resolve_age_category(file_age_days: int) -> str:
    if file_age_days < 90:
        return "recent"
    if file_age_days < 365:
        return "moderate"
    if file_age_days < 730:
        return "old"
    return "very_old"


def _resolve_suggested_category(activity_level: str, mime_type_category: str) -> str:
    if activity_level == "inactive":
        return "Archives"
    if activity_level == "active":
        if mime_type_category in _DOCUMENT_TYPES:
            return "Projects"
        return "Areas"
    if activity_level == "moderate":
        if mime_type_category in _RESOURCE_TYPES:
            return "Resources"
        return "Areas"
    # "unknown" or anything else
    return "Archives"


def extract_para_signals(files: list[dict]) -> list[dict]:
    """Add a ``para_signals`` key to each enriched file dict in-place.

    Args:
        files: List of enriched file dicts from
            ``GoogleDriveOrganizer.get_file_metadata_enriched()``.

    Returns:
        The same list (mutated in place) with ``para_signals`` added to each
        dict.
    """
    for file in files:
        file_age_days: int = file.get("file_age_days", 0) or 0
        activity_level: str = file.get("activity_level", "unknown")
        mime_type_category: str = file.get("mime_type_category", "Other")

        file["para_signals"] = {
            "age_category": _resolve_age_category(file_age_days),
            "suggested_category": _resolve_suggested_category(
                activity_level, mime_type_category
            ),
        }

    return files


def format_proposal_report(plan: dict, files_index: dict) -> str:
    """Format a human-readable PARA organisation proposal report.

    Args:
        plan: Mapping of PARA category -> subfolder name -> list of file IDs.
            Example::

                {
                    "Projects": {"Website-Launch": ["id1", "id2"]},
                    "Areas":    {},
                    "Resources": {"Templates": ["id3"]},
                    "Archives": {},
                }

        files_index: Mapping of file_id -> enriched file dict (used to look up
            file names).  Unknown IDs are shown as ``"[unknown]"``.

    Returns:
        Formatted report string ready to print to the terminal.
    """
    lines: list[str] = []

    # Header
    lines.append("PROPOSED P.A.R.A. ORGANIZATION PLAN")
    lines.append("=====================================")

    # Total files count across all categories
    total_files = sum(
        len(file_ids)
        for category in PARA_CATEGORIES
        for file_ids in plan.get(category, {}).values()
    )
    lines.append(f"Total files to move: {total_files}")
    lines.append("")

    for category in PARA_CATEGORIES:
        subfolders: dict = plan.get(category, {})

        # Count all files in this category
        category_total = sum(len(ids) for ids in subfolders.values())

        lines.append(f"\U0001f4c1 {category}/ ({category_total} files)")

        for subfolder_name, file_ids in subfolders.items():
            subfolder_total = len(file_ids)
            lines.append(f"   └─ {subfolder_name} ({subfolder_total} files)")

            # Show up to 3 file names
            shown = file_ids[:3]
            for fid in shown:
                file_dict = files_index.get(fid)
                name = file_dict.get("name", "[unknown]") if file_dict else "[unknown]"
                lines.append(f"      • {name}")

            remaining = subfolder_total - len(shown)
            if remaining > 0:
                lines.append(f"      ... and {remaining} more")

        lines.append("")

    lines.append("=====================================")
    lines.append("Review the plan above. Reply 'yes' to execute or describe changes you want.")

    return "\n".join(lines)
