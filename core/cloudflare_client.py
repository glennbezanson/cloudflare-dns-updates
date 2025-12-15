"""Cloudflare API client wrapper."""
from typing import Optional
import cloudflare


class CloudflareClient:
    """Wrapper for Cloudflare API operations."""

    def __init__(self, api_token: str = ""):
        self._token = api_token
        self._client: Optional[cloudflare.Cloudflare] = None

    def set_token(self, token: str):
        """Set or update the API token."""
        self._token = token
        self._client = None

    def _get_client(self) -> cloudflare.Cloudflare:
        """Get or create Cloudflare client."""
        if not self._client and self._token:
            self._client = cloudflare.Cloudflare(api_token=self._token)
        return self._client

    def test_connection(self) -> tuple[bool, str]:
        """Test API connection. Returns (success, message)."""
        try:
            client = self._get_client()
            if not client:
                return False, "No API token configured"
            # Verify token works
            client.user.tokens.verify()
            return True, "Connection successful"
        except Exception as e:
            return False, str(e)

    def list_zones(self) -> list[dict]:
        """List all zones/domains."""
        try:
            client = self._get_client()
            if not client:
                return []
            zones = []
            for zone in client.zones.list():
                zones.append({
                    "id": zone.id,
                    "name": zone.name,
                    "status": zone.status,
                    "paused": zone.paused,
                })
            return zones
        except Exception as e:
            print(f"Error listing zones: {e}")
            return []

    def get_zone(self, zone_id: str) -> Optional[dict]:
        """Get zone details."""
        try:
            client = self._get_client()
            if not client:
                return None
            zone = client.zones.get(zone_id=zone_id)
            return {
                "id": zone.id,
                "name": zone.name,
                "status": zone.status,
                "paused": zone.paused,
            }
        except Exception:
            return None

    def list_dns_records(self, zone_id: str) -> list[dict]:
        """List all DNS records for a zone."""
        try:
            client = self._get_client()
            if not client:
                return []
            records = []
            for record in client.dns.records.list(zone_id=zone_id):
                records.append({
                    "id": record.id,
                    "type": record.type,
                    "name": record.name,
                    "content": record.content,
                    "ttl": record.ttl,
                    "proxied": getattr(record, 'proxied', False),
                    "priority": getattr(record, 'priority', None),
                })
            return records
        except Exception as e:
            print(f"Error listing DNS records: {e}")
            return []

    def create_dns_record(self, zone_id: str, record_type: str, name: str,
                          content: str, ttl: int = 1, proxied: bool = False,
                          priority: Optional[int] = None) -> tuple[bool, str, Optional[dict]]:
        """Create a new DNS record. Returns (success, message, record)."""
        try:
            client = self._get_client()
            if not client:
                return False, "No API token configured", None

            params = {
                "zone_id": zone_id,
                "type": record_type,
                "name": name,
                "content": content,
                "ttl": ttl,
            }

            # Only add proxied for A/AAAA/CNAME records
            if record_type in ["A", "AAAA", "CNAME"]:
                params["proxied"] = proxied

            # Add priority for MX/SRV records
            if record_type in ["MX", "SRV"] and priority is not None:
                params["priority"] = priority

            record = client.dns.records.create(**params)
            return True, "Record created successfully", {
                "id": record.id,
                "type": record.type,
                "name": record.name,
                "content": record.content,
                "ttl": record.ttl,
            }
        except Exception as e:
            return False, str(e), None

    def update_dns_record(self, zone_id: str, record_id: str, record_type: str,
                          name: str, content: str, ttl: int = 1,
                          proxied: bool = False,
                          priority: Optional[int] = None) -> tuple[bool, str]:
        """Update an existing DNS record. Returns (success, message)."""
        try:
            client = self._get_client()
            if not client:
                return False, "No API token configured"

            params = {
                "zone_id": zone_id,
                "dns_record_id": record_id,
                "type": record_type,
                "name": name,
                "content": content,
                "ttl": ttl,
            }

            if record_type in ["A", "AAAA", "CNAME"]:
                params["proxied"] = proxied

            if record_type in ["MX", "SRV"] and priority is not None:
                params["priority"] = priority

            client.dns.records.update(**params)
            return True, "Record updated successfully"
        except Exception as e:
            return False, str(e)

    def delete_dns_record(self, zone_id: str, record_id: str) -> tuple[bool, str]:
        """Delete a DNS record. Returns (success, message)."""
        try:
            client = self._get_client()
            if not client:
                return False, "No API token configured"

            client.dns.records.delete(zone_id=zone_id, dns_record_id=record_id)
            return True, "Record deleted successfully"
        except Exception as e:
            return False, str(e)

    def export_zone(self, zone_id: str) -> tuple[bool, str, list[dict]]:
        """Export all DNS records for a zone. Returns (success, message, records)."""
        try:
            records = self.list_dns_records(zone_id)
            return True, f"Exported {len(records)} records", records
        except Exception as e:
            return False, str(e), []
