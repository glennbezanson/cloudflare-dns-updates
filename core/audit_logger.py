"""Audit logging for DNS changes."""
import json
from datetime import datetime
from pathlib import Path
from typing import Optional
from config.settings import AUDIT_LOG


class AuditLogger:
    """Logs all DNS changes with timestamps for audit trail."""

    def __init__(self, log_path: Optional[Path] = None):
        self.log_path = log_path or AUDIT_LOG

    def log(self, action: str, domain: str, record_type: str, name: str,
            content: str, details: Optional[dict] = None,
            claude_review: Optional[dict] = None):
        """
        Log a DNS change action.

        Args:
            action: The action performed (add, edit, delete)
            domain: The domain name
            record_type: DNS record type
            name: Record name
            content: Record content
            details: Additional details (old values for edit, etc.)
            claude_review: Claude's review assessment if available
        """
        entry = {
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "domain": domain,
            "record": {
                "type": record_type,
                "name": name,
                "content": content,
            },
        }

        if details:
            entry["details"] = details

        if claude_review:
            entry["claude_review"] = {
                "assessment": claude_review.get("assessment"),
                "summary": claude_review.get("summary"),
            }

        self._write_entry(entry)

    def log_batch(self, action: str, domain: str, records: list[dict],
                  claude_review: Optional[dict] = None):
        """Log a batch of changes."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "action": f"batch_{action}",
            "domain": domain,
            "records": records,
            "count": len(records),
        }

        if claude_review:
            entry["claude_review"] = {
                "assessment": claude_review.get("assessment"),
                "summary": claude_review.get("summary"),
            }

        self._write_entry(entry)

    def log_backup(self, action: str, domain: str, filename: str, record_count: int):
        """Log backup/restore operations."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "domain": domain,
            "backup_file": filename,
            "record_count": record_count,
        }
        self._write_entry(entry)

    def _write_entry(self, entry: dict):
        """Write an entry to the log file."""
        try:
            with open(self.log_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps(entry) + "\n")
        except Exception as e:
            print(f"Failed to write audit log: {e}")

    def get_entries(self, limit: int = 100, domain: Optional[str] = None,
                    action: Optional[str] = None) -> list[dict]:
        """
        Get audit log entries.

        Args:
            limit: Maximum number of entries to return
            domain: Filter by domain name
            action: Filter by action type

        Returns:
            List of log entries (newest first)
        """
        entries = []

        if not self.log_path.exists():
            return entries

        try:
            with open(self.log_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        entry = json.loads(line)

                        # Apply filters
                        if domain and entry.get("domain") != domain:
                            continue
                        if action and not entry.get("action", "").startswith(action):
                            continue

                        entries.append(entry)
                    except json.JSONDecodeError:
                        continue

            # Return newest first, limited
            return list(reversed(entries[-limit:]))
        except Exception as e:
            print(f"Failed to read audit log: {e}")
            return []

    def export_log(self, output_path: Path, domain: Optional[str] = None) -> tuple[bool, str]:
        """
        Export audit log to a file.

        Args:
            output_path: Path to export file
            domain: Optional domain filter

        Returns:
            (success, message)
        """
        try:
            entries = self.get_entries(limit=10000, domain=domain)

            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(entries, f, indent=2)

            return True, f"Exported {len(entries)} entries"
        except Exception as e:
            return False, str(e)

    def clear_log(self) -> tuple[bool, str]:
        """Clear the audit log. Returns (success, message)."""
        try:
            if self.log_path.exists():
                self.log_path.unlink()
            return True, "Audit log cleared"
        except Exception as e:
            return False, str(e)
