"""Zone backup and restore functionality."""
import json
from datetime import datetime
from pathlib import Path
from typing import Optional
from config.settings import BACKUPS_DIR


class ZoneBackup:
    """Handles zone backup and restore operations."""

    def __init__(self, backup_dir: Optional[Path] = None):
        self.backup_dir = backup_dir or BACKUPS_DIR
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def create_backup(self, domain: str, records: list[dict],
                      zone_info: Optional[dict] = None) -> tuple[bool, str, str]:
        """
        Create a backup of a zone.

        Args:
            domain: Domain name
            records: List of DNS records
            zone_info: Optional zone metadata

        Returns:
            (success, message, filename)
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{domain}_{timestamp}.json"
            filepath = self.backup_dir / filename

            backup_data = {
                "version": "1.0",
                "created_at": datetime.now().isoformat(),
                "domain": domain,
                "zone_info": zone_info or {},
                "record_count": len(records),
                "records": records,
            }

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, indent=2)

            return True, f"Backup created: {filename}", filename

        except Exception as e:
            return False, str(e), ""

    def list_backups(self, domain: Optional[str] = None) -> list[dict]:
        """
        List available backups.

        Args:
            domain: Optional domain filter

        Returns:
            List of backup metadata
        """
        backups = []

        for filepath in self.backup_dir.glob("*.json"):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                backup_domain = data.get("domain", "")
                if domain and backup_domain != domain:
                    continue

                backups.append({
                    "filename": filepath.name,
                    "path": str(filepath),
                    "domain": backup_domain,
                    "created_at": data.get("created_at"),
                    "record_count": data.get("record_count", 0),
                })
            except (json.JSONDecodeError, KeyError):
                continue

        # Sort by creation date, newest first
        backups.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return backups

    def load_backup(self, filename: str) -> tuple[bool, str, dict]:
        """
        Load a backup file.

        Args:
            filename: Backup filename

        Returns:
            (success, message, backup_data)
        """
        try:
            filepath = self.backup_dir / filename
            if not filepath.exists():
                return False, f"Backup not found: {filename}", {}

            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)

            return True, "Backup loaded", data

        except json.JSONDecodeError as e:
            return False, f"Invalid backup file: {e}", {}
        except Exception as e:
            return False, str(e), {}

    def compare_backup(self, backup_records: list[dict],
                       current_records: list[dict]) -> dict:
        """
        Compare backup records with current records.

        Args:
            backup_records: Records from backup
            current_records: Current DNS records

        Returns:
            Comparison result with added, removed, and modified records
        """
        # Create lookup dicts by type+name
        def make_key(record):
            return f"{record.get('type')}:{record.get('name')}"

        backup_dict = {}
        for r in backup_records:
            key = make_key(r)
            if key not in backup_dict:
                backup_dict[key] = []
            backup_dict[key].append(r)

        current_dict = {}
        for r in current_records:
            key = make_key(r)
            if key not in current_dict:
                current_dict[key] = []
            current_dict[key].append(r)

        added = []      # In current but not backup
        removed = []    # In backup but not current
        modified = []   # Same key but different content

        # Find removed and modified
        for key, backup_recs in backup_dict.items():
            if key not in current_dict:
                removed.extend(backup_recs)
            else:
                current_recs = current_dict[key]
                # Simple content comparison
                backup_contents = {r.get('content') for r in backup_recs}
                current_contents = {r.get('content') for r in current_recs}

                for r in backup_recs:
                    if r.get('content') not in current_contents:
                        removed.append(r)

                for r in current_recs:
                    if r.get('content') not in backup_contents:
                        # Check if this is a modification or addition
                        if any(c.get('content') != r.get('content') for c in backup_recs):
                            modified.append({
                                "current": r,
                                "backup": [b for b in backup_recs
                                           if b.get('content') != r.get('content')][0]
                                if backup_recs else None
                            })

        # Find added
        for key, current_recs in current_dict.items():
            if key not in backup_dict:
                added.extend(current_recs)

        return {
            "added": added,
            "removed": removed,
            "modified": modified,
            "summary": {
                "added_count": len(added),
                "removed_count": len(removed),
                "modified_count": len(modified),
            }
        }

    def delete_backup(self, filename: str) -> tuple[bool, str]:
        """
        Delete a backup file.

        Args:
            filename: Backup filename

        Returns:
            (success, message)
        """
        try:
            filepath = self.backup_dir / filename
            if not filepath.exists():
                return False, f"Backup not found: {filename}"

            filepath.unlink()
            return True, f"Backup deleted: {filename}"

        except Exception as e:
            return False, str(e)

    def export_to_bind(self, records: list[dict], domain: str) -> str:
        """
        Export records to BIND zone file format.

        Args:
            records: List of DNS records
            domain: Domain name

        Returns:
            BIND format string
        """
        lines = [
            f"; Zone file for {domain}",
            f"; Generated: {datetime.now().isoformat()}",
            f"$ORIGIN {domain}.",
            "$TTL 3600",
            "",
        ]

        for record in records:
            rtype = record.get("type", "")
            name = record.get("name", "@")
            content = record.get("content", "")
            ttl = record.get("ttl", 3600)
            priority = record.get("priority")

            # Adjust name - remove domain suffix if present
            if name.endswith(f".{domain}"):
                name = name[:-len(f".{domain}")]
            elif name == domain:
                name = "@"

            # Format TTL
            ttl_str = str(ttl) if ttl != 1 else ""

            # Build record line
            if rtype == "MX" and priority is not None:
                lines.append(f"{name}\t{ttl_str}\tIN\t{rtype}\t{priority}\t{content}.")
            elif rtype in ["CNAME", "NS", "MX"]:
                # Add trailing dot for hostnames
                if not content.endswith("."):
                    content += "."
                lines.append(f"{name}\t{ttl_str}\tIN\t{rtype}\t{content}")
            elif rtype == "TXT":
                # Quote TXT content
                lines.append(f'{name}\t{ttl_str}\tIN\t{rtype}\t"{content}"')
            else:
                lines.append(f"{name}\t{ttl_str}\tIN\t{rtype}\t{content}")

        return "\n".join(lines)
