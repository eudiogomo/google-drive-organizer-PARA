import re
from datetime import datetime, timezone
from typing import Any


class GoogleDriveOrganizer:
    FOLDER_MIME = "application/vnd.google-apps.folder"
    FILE_FIELDS = "id, name, mimeType, parents, size, createdTime, modifiedTime, owners, webViewLink"

    MIME_CATEGORY_MAP = {
        "application/vnd.google-apps.document": "Document",
        "application/vnd.google-apps.spreadsheet": "Spreadsheet",
        "application/vnd.google-apps.presentation": "Presentation",
        "application/vnd.google-apps.form": "Form",
        "application/vnd.google-apps.drawing": "Drawing",
        "application/pdf": "PDF",
    }

    def __init__(self, service: Any):
        self.service = service  # authenticated Drive API service

    # ------------------------------------------------------------------
    # 1. Recursive file listing
    # ------------------------------------------------------------------

    def get_all_files_recursive(
        self,
        folder_id: str = "root",
        max_depth: int = 10,
    ) -> list[dict]:
        """Recursively lists all non-folder files owned by the user."""
        all_files: list[dict] = []
        visited_folders: set[str] = set()
        self._recurse_folder(folder_id, max_depth, 0, visited_folders, all_files)
        return all_files

    def _recurse_folder(
        self,
        folder_id: str,
        max_depth: int,
        current_depth: int,
        visited_folders: set[str],
        result: list[dict],
    ) -> None:
        if current_depth >= max_depth:
            return
        if folder_id in visited_folders:
            return
        visited_folders.add(folder_id)

        page_token: str | None = None
        query = f"'{folder_id}' in parents and trashed=false"

        while True:
            kwargs: dict[str, Any] = {
                "q": query,
                "fields": f"nextPageToken, files({self.FILE_FIELDS})",
                "pageSize": 1000,
            }
            if page_token:
                kwargs["pageToken"] = page_token

            response = self.service.files().list(**kwargs).execute()
            items: list[dict] = response.get("files", [])

            for item in items:
                if item.get("mimeType") == self.FOLDER_MIME:
                    # Recurse into sub-folders
                    self._recurse_folder(
                        item["id"],
                        max_depth,
                        current_depth + 1,
                        visited_folders,
                        result,
                    )
                else:
                    # Keep only files owned by the authenticated user
                    owners = item.get("owners", [])
                    if any(owner.get("me") for owner in owners):
                        result.append(item)

            page_token = response.get("nextPageToken")
            if not page_token:
                break

    # ------------------------------------------------------------------
    # 2. Metadata enrichment
    # ------------------------------------------------------------------

    def get_file_metadata_enriched(self, file: dict) -> dict:
        """Returns the file dict enriched with PARA analysis fields."""
        enriched = dict(file)

        mime_type: str = file.get("mimeType", "")

        # -- mime_type_category --
        enriched["mime_type_category"] = self._resolve_mime_category(mime_type)

        # -- size_bytes --
        try:
            size_bytes = int(file.get("size", 0) or 0)
        except (ValueError, TypeError):
            size_bytes = 0
        enriched["size_bytes"] = size_bytes

        # -- size_category --
        enriched["size_category"] = self._resolve_size_category(size_bytes)

        # -- file_age_days & days_since_modified --
        now = datetime.now(tz=timezone.utc)
        enriched["file_age_days"] = self._days_since(file.get("createdTime"), now)
        days_since_modified = self._days_since(file.get("modifiedTime"), now)
        enriched["days_since_modified"] = days_since_modified

        # -- activity_level --
        if days_since_modified < 90:
            activity_level = "active"
        elif days_since_modified < 365:
            activity_level = "moderate"
        else:
            activity_level = "inactive"
        enriched["activity_level"] = activity_level

        # -- is_google_workspace --
        enriched["is_google_workspace"] = (
            mime_type.startswith("application/vnd.google-apps.")
            and mime_type != self.FOLDER_MIME
        )

        # -- name_keywords --
        name: str = file.get("name", "")
        tokens = re.split(r"[^a-zA-Z0-9]+", name)
        enriched["name_keywords"] = [
            t.lower() for t in tokens if len(t) > 2
        ]

        return enriched

    def _resolve_mime_category(self, mime_type: str) -> str:
        if mime_type in self.MIME_CATEGORY_MAP:
            return self.MIME_CATEGORY_MAP[mime_type]
        if mime_type.startswith("image/"):
            return "Image"
        if mime_type.startswith("video/"):
            return "Video"
        if mime_type.startswith("audio/"):
            return "Audio"
        return "Other"

    @staticmethod
    def _resolve_size_category(size_bytes: int) -> str:
        if size_bytes < 10_000:          # < 10 KB
            return "tiny"
        if size_bytes < 1_000_000:       # < 1 MB
            return "small"
        if size_bytes < 10_000_000:      # < 10 MB
            return "medium"
        if size_bytes < 100_000_000:     # < 100 MB
            return "large"
        return "huge"

    @staticmethod
    def _days_since(iso_timestamp: str | None, now: datetime) -> int:
        if not iso_timestamp:
            return 0
        try:
            dt = datetime.fromisoformat(iso_timestamp.replace("Z", "+00:00"))
            delta = now - dt
            return max(0, delta.days)
        except (ValueError, TypeError):
            return 0

    # ------------------------------------------------------------------
    # 3. Folder path resolution
    # ------------------------------------------------------------------

    def get_folder_path(self, file: dict, folders_cache: dict) -> str:
        """Returns a human-readable path string like 'Projects/MySubfolder'.

        Args:
            file: A raw or enriched Drive API file dict.
            folders_cache: Mapping of folder_id -> folder_name.

        Returns:
            Path string, or "" if parents are not in cache.
        """
        parents: list[str] = file.get("parents") or []
        if not parents:
            return ""

        parent_id = parents[0]
        path_parts: list[str] = []

        while parent_id and parent_id in folders_cache:
            folder_name = folders_cache[parent_id]
            path_parts.append(folder_name)
            # Try to look up the parent's parent via a secondary lookup.
            # folders_cache values are names; we need a way to navigate upward.
            # Since the cache maps id->name only, we stop here unless the caller
            # has embedded parent info. We build upward only one level here;
            # callers who need full paths should pass a richer cache or call
            # this helper after populating a full parent-chain cache.
            break

        if not path_parts:
            return ""

        path_parts.reverse()
        return "/".join(path_parts)

    # ------------------------------------------------------------------
    # 4. Create a single folder (idempotent)
    # ------------------------------------------------------------------

    def create_folder(self, name: str, parent_id: str) -> str:
        """Creates a Drive folder; returns existing folder ID if one already exists."""
        safe_name = self._sanitize_folder_name(name)

        # Check for existing folder with same name under parent
        query = (
            f"name='{safe_name}' and '{parent_id}' in parents "
            f"and mimeType='{self.FOLDER_MIME}' and trashed=false"
        )
        response = (
            self.service.files()
            .list(q=query, fields="files(id)", pageSize=1)
            .execute()
        )
        existing = response.get("files", [])
        if existing:
            return existing[0]["id"]

        # Create new folder
        metadata = {
            "name": safe_name,
            "mimeType": self.FOLDER_MIME,
            "parents": [parent_id],
        }
        created = (
            self.service.files()
            .create(body=metadata, fields="id")
            .execute()
        )
        return created["id"]

    @staticmethod
    def _sanitize_folder_name(name: str) -> str:
        """Remove invalid characters and truncate to 100 chars."""
        sanitized = re.sub(r'[<>:"/\\|?*]', "", name)
        return sanitized[:100]

    # ------------------------------------------------------------------
    # 5. Create a full folder hierarchy
    # ------------------------------------------------------------------

    def create_folder_hierarchy(self, path_parts: list[str], root_id: str) -> str:
        """Creates nested folders from path_parts under root_id.

        Example: create_folder_hierarchy(["Projects", "Website-Launch"], root_id)
        Returns the ID of the deepest (last) folder created.
        """
        current_parent = root_id
        for part in path_parts:
            current_parent = self.create_folder(part, current_parent)
        return current_parent

    # ------------------------------------------------------------------
    # 6. Move a file
    # ------------------------------------------------------------------

    def move_file(self, file_id: str, new_parent_id: str, old_parent_id: str) -> bool:
        """Moves a file to a new parent folder.

        Returns True on success, False on any API error.
        """
        try:
            self.service.files().update(
                fileId=file_id,
                addParents=new_parent_id,
                removeParents=old_parent_id,
                fields="id, parents",
            ).execute()
            return True
        except Exception:
            return False
