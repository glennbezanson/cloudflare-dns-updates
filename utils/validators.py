"""DNS record validation utilities."""
import re
from typing import Optional


def validate_ipv4(ip: str) -> tuple[bool, str]:
    """Validate IPv4 address."""
    pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
    if not re.match(pattern, ip):
        return False, "Invalid IPv4 format"

    parts = ip.split('.')
    for part in parts:
        if int(part) > 255:
            return False, f"Invalid octet: {part}"

    return True, ""


def validate_ipv6(ip: str) -> tuple[bool, str]:
    """Validate IPv6 address."""
    try:
        import socket
        socket.inet_pton(socket.AF_INET6, ip)
        return True, ""
    except socket.error:
        return False, "Invalid IPv6 format"


def validate_hostname(hostname: str) -> tuple[bool, str]:
    """Validate hostname/domain name."""
    if hostname == "@":
        return True, ""

    if len(hostname) > 253:
        return False, "Hostname too long (max 253 characters)"

    # Allow wildcard
    if hostname.startswith("*."):
        hostname = hostname[2:]

    pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9-]*[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9-]*[a-zA-Z0-9])?)*$'
    if not re.match(pattern, hostname):
        return False, "Invalid hostname format"

    return True, ""


def validate_spf(spf: str) -> tuple[bool, str]:
    """Validate SPF record syntax."""
    if not spf.startswith("v=spf1"):
        return False, "SPF record must start with 'v=spf1'"

    # Check for common mistakes
    if "v=spfl" in spf.lower():
        return False, "Typo detected: 'v=spfl' should be 'v=spf1'"

    # Check for valid mechanisms
    valid_mechanisms = ['all', 'include', 'a', 'mx', 'ptr', 'ip4', 'ip6', 'exists', 'redirect', 'exp']
    valid_qualifiers = ['+', '-', '~', '?']

    parts = spf.split()[1:]  # Skip v=spf1
    for part in parts:
        # Skip empty parts
        if not part:
            continue

        # Check qualifier
        if part[0] in valid_qualifiers:
            part = part[1:]

        # Check mechanism
        mechanism = part.split(':')[0].split('/')[0]
        if mechanism not in valid_mechanisms:
            return False, f"Unknown SPF mechanism: {mechanism}"

        # Check for common formatting issues
        if "include:" in part and part.count(':') > 1:
            return False, f"Invalid include syntax: {part}"

    # Check for multiple 'all' mechanisms
    all_count = sum(1 for p in parts if p.endswith('all'))
    if all_count > 1:
        return False, "Multiple 'all' mechanisms found"

    # Warn if no 'all' mechanism
    if all_count == 0:
        return True, "Warning: No 'all' mechanism - consider adding -all or ~all"

    return True, ""


def validate_mx_priority(priority: Optional[int]) -> tuple[bool, str]:
    """Validate MX priority."""
    if priority is None:
        return False, "MX record requires priority"
    if priority < 0 or priority > 65535:
        return False, "Priority must be between 0 and 65535"
    return True, ""


def validate_ttl(ttl: int) -> tuple[bool, str]:
    """Validate TTL value."""
    if ttl < 1:
        return False, "TTL must be positive"
    if ttl > 86400 * 365:  # Max 1 year
        return False, "TTL too high (max 1 year)"
    return True, ""


def validate_txt(content: str) -> tuple[bool, str]:
    """Validate TXT record content."""
    if len(content) > 4096:
        return False, "TXT record too long (max 4096 characters)"

    # Check for SPF if it looks like one
    if content.startswith("v=spf"):
        return validate_spf(content)

    return True, ""


def validate_record(record_type: str, name: str, content: str,
                    ttl: int = 1, priority: Optional[int] = None) -> tuple[bool, list[str]]:
    """
    Validate a complete DNS record.

    Returns:
        (is_valid, list of error/warning messages)
    """
    errors = []

    # Validate name
    valid, msg = validate_hostname(name)
    if not valid:
        errors.append(f"Name: {msg}")

    # Validate TTL
    if ttl != 1:  # 1 = Auto
        valid, msg = validate_ttl(ttl)
        if not valid:
            errors.append(f"TTL: {msg}")

    # Type-specific validation
    if record_type == "A":
        valid, msg = validate_ipv4(content)
        if not valid:
            errors.append(f"Content: {msg}")

    elif record_type == "AAAA":
        valid, msg = validate_ipv6(content)
        if not valid:
            errors.append(f"Content: {msg}")

    elif record_type == "CNAME":
        valid, msg = validate_hostname(content)
        if not valid:
            errors.append(f"Content: {msg}")

    elif record_type == "MX":
        valid, msg = validate_hostname(content)
        if not valid:
            errors.append(f"Content: {msg}")
        valid, msg = validate_mx_priority(priority)
        if not valid:
            errors.append(f"Priority: {msg}")

    elif record_type == "TXT":
        valid, msg = validate_txt(content)
        if not valid:
            errors.append(f"Content: {msg}")
        elif msg:  # Warning
            errors.append(msg)

    return len([e for e in errors if not e.startswith("Warning")]) == 0, errors
