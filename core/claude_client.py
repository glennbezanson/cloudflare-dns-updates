"""Claude API client for DNS change review."""
import json
from typing import Optional
import anthropic
from config.settings import CLAUDE_MODEL


class ClaudeClient:
    """Claude AI integration for reviewing DNS changes."""

    def __init__(self, api_key: str = ""):
        self._api_key = api_key
        self._client: Optional[anthropic.Anthropic] = None

    def set_api_key(self, key: str):
        """Set or update the API key."""
        self._api_key = key
        self._client = None

    def _get_client(self) -> Optional[anthropic.Anthropic]:
        """Get or create Anthropic client."""
        if not self._client and self._api_key:
            self._client = anthropic.Anthropic(api_key=self._api_key)
        return self._client

    def test_connection(self) -> tuple[bool, str]:
        """Test API connection. Returns (success, message)."""
        try:
            client = self._get_client()
            if not client:
                return False, "No API key configured"
            # Simple test message
            response = client.messages.create(
                model=CLAUDE_MODEL,
                max_tokens=50,
                messages=[{"role": "user", "content": "Say 'connected' if you can read this."}]
            )
            return True, "Connection successful"
        except Exception as e:
            return False, str(e)

    def review_changes(self, domain: str, current_records: list[dict],
                       pending_changes: list[dict]) -> tuple[bool, str, dict]:
        """
        Review pending DNS changes.

        Args:
            domain: The domain name
            current_records: List of current DNS records
            pending_changes: List of changes (add/edit/delete operations)

        Returns:
            (success, message, review_result)
        """
        try:
            client = self._get_client()
            if not client:
                return False, "No API key configured", {}

            prompt = self._build_review_prompt(domain, current_records, pending_changes)

            response = client.messages.create(
                model=CLAUDE_MODEL,
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}]
            )

            review_text = response.content[0].text

            # Parse the response
            result = self._parse_review_response(review_text)
            return True, "Review completed", result

        except Exception as e:
            return False, str(e), {}

    def _build_review_prompt(self, domain: str, current_records: list[dict],
                             pending_changes: list[dict]) -> str:
        """Build the review prompt for Claude."""
        prompt = f"""You are a DNS expert reviewing proposed changes to the domain: {domain}

## Current DNS Records:
```json
{json.dumps(current_records, indent=2)}
```

## Pending Changes:
```json
{json.dumps(pending_changes, indent=2)}
```

Please review these changes and provide:

1. **Overall Assessment**: Is this change safe to apply? (SAFE, CAUTION, or DANGER)

2. **Issues Found**: List any problems detected:
   - SPF record syntax errors
   - Duplicate records that would conflict
   - Missing required records
   - Records that might break email delivery
   - Records that might affect website availability
   - Security concerns (e.g., removing important TXT verification records)

3. **Warnings**: Things to be aware of (not blocking, but noteworthy)

4. **Recommendations**: Suggested improvements or best practices

5. **Summary**: One paragraph summary of the changes

Please format your response as JSON with this structure:
```json
{{
    "assessment": "SAFE|CAUTION|DANGER",
    "issues": ["issue1", "issue2"],
    "warnings": ["warning1", "warning2"],
    "recommendations": ["rec1", "rec2"],
    "summary": "Brief summary of changes and their impact"
}}
```

Be specific and actionable. If SPF records are involved, validate the syntax carefully.
If email-related records (MX, SPF, DKIM, DMARC) are being modified, pay extra attention."""

        return prompt

    def _parse_review_response(self, response_text: str) -> dict:
        """Parse Claude's review response into structured data."""
        # Try to extract JSON from the response
        try:
            # Look for JSON block
            if "```json" in response_text:
                start = response_text.find("```json") + 7
                end = response_text.find("```", start)
                json_str = response_text[start:end].strip()
            elif "{" in response_text:
                start = response_text.find("{")
                end = response_text.rfind("}") + 1
                json_str = response_text[start:end]
            else:
                json_str = response_text

            result = json.loads(json_str)

            # Ensure required fields exist
            return {
                "assessment": result.get("assessment", "CAUTION"),
                "issues": result.get("issues", []),
                "warnings": result.get("warnings", []),
                "recommendations": result.get("recommendations", []),
                "summary": result.get("summary", "Unable to parse review"),
                "raw_response": response_text
            }
        except json.JSONDecodeError:
            # If JSON parsing fails, return a basic structure with the raw text
            return {
                "assessment": "CAUTION",
                "issues": ["Unable to parse structured review"],
                "warnings": [],
                "recommendations": [],
                "summary": response_text[:500],
                "raw_response": response_text
            }

    def parse_natural_language(self, user_input: str, domain: str) -> tuple[bool, str, list[dict]]:
        """
        Parse natural language input into DNS record operations.

        Args:
            user_input: Natural language description of desired changes
            domain: The target domain

        Returns:
            (success, message, list of record operations)
        """
        try:
            client = self._get_client()
            if not client:
                return False, "No API key configured", []

            prompt = f"""You are a DNS expert. Parse the following natural language request into DNS record operations for the domain: {domain}

User request: "{user_input}"

Generate a list of DNS record operations. Each operation should be a JSON object with:
- "action": "add", "edit", or "delete"
- "type": DNS record type (A, AAAA, CNAME, MX, TXT, etc.)
- "name": record name (use "@" for root domain)
- "content": record content/value
- "ttl": TTL in seconds (use 1 for Auto)
- "priority": priority for MX records (optional)

Respond ONLY with a JSON array of operations. Example:
```json
[
    {{"action": "add", "type": "TXT", "name": "@", "content": "v=spf1 include:example.com -all", "ttl": 1}},
    {{"action": "add", "type": "A", "name": "www", "content": "192.168.1.1", "ttl": 3600}}
]
```

If the request is unclear or you cannot determine the exact records, respond with:
```json
{{"error": "explanation of what's unclear"}}
```"""

            response = client.messages.create(
                model=CLAUDE_MODEL,
                max_tokens=1000,
                messages=[{"role": "user", "content": prompt}]
            )

            response_text = response.content[0].text

            # Extract JSON
            if "```json" in response_text:
                start = response_text.find("```json") + 7
                end = response_text.find("```", start)
                json_str = response_text[start:end].strip()
            else:
                json_str = response_text.strip()

            result = json.loads(json_str)

            if isinstance(result, dict) and "error" in result:
                return False, result["error"], []

            return True, f"Parsed {len(result)} operations", result

        except json.JSONDecodeError as e:
            return False, f"Failed to parse response: {e}", []
        except Exception as e:
            return False, str(e), []

    def validate_records(self, records: list[dict], domain: str) -> tuple[bool, str, dict]:
        """
        Validate parsed DNS records against best practices.

        Args:
            records: List of parsed DNS records
            domain: The target domain

        Returns:
            (success, message, validation_result with corrected records)
        """
        try:
            client = self._get_client()
            if not client:
                return False, "No API key configured", {}

            prompt = f"""You are a DNS expert. Validate and correct the following DNS records for domain: {domain}

## Records to Validate:
```json
{json.dumps(records, indent=2)}
```

For each record, check for:

1. **SPF Records (TXT starting with v=spf)**:
   - Must start with "v=spf1" (NOT "v=spfl" - common typo)
   - No spaces after "include:" (e.g., "include:example.com" NOT "include: example.com")
   - Should end with "-all", "~all", or "?all"
   - Check for valid mechanisms (include, ip4, ip6, a, mx, ptr, exists, redirect)

2. **DKIM Records**:
   - Should be properly formatted
   - Name usually like "selector._domainkey"

3. **DMARC Records**:
   - Must start with "v=DMARC1"
   - Name should be "_dmarc"

4. **General TXT Records**:
   - Verification records (google-site-verification, apple-domain-verification, etc.) look valid
   - No obvious typos or formatting issues

5. **All Records**:
   - Name field makes sense for the record type
   - Content is properly formatted

Respond with JSON:
```json
{{
    "valid": true/false,
    "corrected_records": [
        {{
            "original": {{"type": "...", "name": "...", "content": "..."}},
            "corrected": {{"type": "...", "name": "...", "content": "...", "ttl": 1}},
            "issues": ["list of issues found"],
            "fixes_applied": ["list of fixes applied"],
            "warnings": ["non-critical warnings"]
        }}
    ],
    "summary": "Overall summary of validation"
}}
```

If a record is valid, "corrected" should match "original" and "fixes_applied" should be empty.
Always include the full corrected record with all fields (type, name, content, ttl, priority if applicable)."""

            response = client.messages.create(
                model=CLAUDE_MODEL,
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}]
            )

            response_text = response.content[0].text

            # Extract JSON
            if "```json" in response_text:
                start = response_text.find("```json") + 7
                end = response_text.find("```", start)
                json_str = response_text[start:end].strip()
            elif "{" in response_text:
                start = response_text.find("{")
                end = response_text.rfind("}") + 1
                json_str = response_text[start:end]
            else:
                json_str = response_text

            result = json.loads(json_str)

            return True, "Validation completed", result

        except json.JSONDecodeError as e:
            return False, f"Failed to parse validation response: {e}", {}
        except Exception as e:
            return False, str(e), {}

    def health_check(self, domain: str, records: list[dict]) -> tuple[bool, str, dict]:
        """
        Perform a comprehensive DNS health assessment.

        Args:
            domain: The domain name
            records: List of current DNS records

        Returns:
            (success, message, health_report)
        """
        try:
            client = self._get_client()
            if not client:
                return False, "No API key configured", {}

            prompt = f"""You are a DNS security and best practices expert. Perform a comprehensive health assessment of the DNS configuration for: {domain}

## Current DNS Records:
```json
{json.dumps(records, indent=2)}
```

Analyze this DNS configuration and provide a detailed health report covering:

## 1. Email Security (Critical)
- **SPF**: Is there an SPF record? Is it valid? Are there multiple SPF records (invalid)?
- **DKIM**: Are there DKIM selector records?
- **DMARC**: Is there a DMARC record at _dmarc? Is the policy appropriate (none/quarantine/reject)?
- **MX Records**: Are MX records properly configured with priorities?

## 2. Security Records
- **CAA Records**: Are there CAA records to control certificate issuance?
- **DNSSEC**: (Note if relevant records exist)
- **Domain Verification**: Are there verification TXT records (Google, Microsoft, etc.)?

## 3. Web Configuration
- **A/AAAA Records**: Is the root domain configured?
- **WWW**: Is www properly configured (A, AAAA, or CNAME)?
- **Cloudflare Proxy**: Are appropriate records proxied?

## 4. Best Practices
- **TTL Values**: Are TTLs appropriate?
- **Redundancy**: Are there backup MX records?
- **Deprecated Records**: Any outdated or unnecessary records?

## 5. Potential Issues
- **Conflicts**: Any conflicting records?
- **Missing Records**: Critical records that should exist but don't?
- **Security Risks**: Any records that could pose security risks?

Respond with JSON:
```json
{{
    "overall_score": "A|B|C|D|F",
    "overall_status": "Excellent|Good|Fair|Poor|Critical",
    "summary": "One paragraph executive summary",
    "categories": [
        {{
            "name": "Email Security",
            "score": "A|B|C|D|F",
            "status": "pass|warning|fail",
            "findings": [
                {{
                    "check": "SPF Record",
                    "status": "pass|warning|fail|missing",
                    "current": "current value or null",
                    "message": "detailed finding",
                    "recommendation": "what to do (if any)"
                }}
            ]
        }},
        {{
            "name": "Security Records",
            "score": "A|B|C|D|F",
            "status": "pass|warning|fail",
            "findings": [...]
        }},
        {{
            "name": "Web Configuration",
            "score": "A|B|C|D|F",
            "status": "pass|warning|fail",
            "findings": [...]
        }},
        {{
            "name": "Best Practices",
            "score": "A|B|C|D|F",
            "status": "pass|warning|fail",
            "findings": [...]
        }}
    ],
    "critical_issues": ["list of critical issues requiring immediate attention"],
    "recommendations": ["prioritized list of recommended improvements"]
}}
```

Be thorough but practical. Focus on actionable findings."""

            response = client.messages.create(
                model=CLAUDE_MODEL,
                max_tokens=3000,
                messages=[{"role": "user", "content": prompt}]
            )

            response_text = response.content[0].text

            # Extract JSON
            if "```json" in response_text:
                start = response_text.find("```json") + 7
                end = response_text.find("```", start)
                json_str = response_text[start:end].strip()
            elif "{" in response_text:
                start = response_text.find("{")
                end = response_text.rfind("}") + 1
                json_str = response_text[start:end]
            else:
                json_str = response_text

            result = json.loads(json_str)

            return True, "Health check completed", result

        except json.JSONDecodeError as e:
            return False, f"Failed to parse health check response: {e}", {}
        except Exception as e:
            return False, str(e), {}

    def generate_fixes(self, domain: str, records: list[dict],
                       health_report: dict) -> tuple[bool, str, list[dict]]:
        """
        Generate DNS record fixes based on health assessment.

        Args:
            domain: The domain name
            records: Current DNS records
            health_report: The health check result

        Returns:
            (success, message, list of record operations to fix issues)
        """
        try:
            client = self._get_client()
            if not client:
                return False, "No API key configured", []

            prompt = f"""You are a DNS expert. Based on the health assessment below, generate DNS record operations to fix the identified issues for domain: {domain}

## Current DNS Records:
```json
{json.dumps(records, indent=2)}
```

## Health Assessment Results:
```json
{json.dumps(health_report, indent=2)}
```

Generate a list of DNS record operations to implement best practices and fix issues. For each fix:

1. **SPF Record**: If missing or invalid, create a proper SPF record. Common includes:
   - Microsoft 365: include:spf.protection.outlook.com
   - Google Workspace: include:_spf.google.com
   - If unsure, use a permissive ~all until verified

2. **DMARC Record**: If missing, add at _dmarc with appropriate policy:
   - Start with p=none for monitoring
   - Include rua for reports if possible

3. **DKIM**: Note that DKIM records must come from the email provider - just flag if missing

4. **CAA Records**: If missing, add CAA records for common CAs:
   - letsencrypt.org
   - comodoca.com (Sectigo)
   - digicert.com

5. **MX Records**: Ensure proper priority ordering

6. **Missing www**: Add CNAME to root if www doesn't exist

Only generate fixes for issues that CAN be fixed via DNS records. Skip issues that require external action (like getting DKIM keys from email provider).

Respond with JSON:
```json
{{
    "fixes": [
        {{
            "action": "add|edit|delete",
            "type": "TXT|MX|CNAME|A|CAA|etc",
            "name": "record name (@ for root, _dmarc, etc)",
            "content": "record content",
            "ttl": 1,
            "priority": null,
            "reason": "why this fix is needed",
            "category": "Email Security|Security Records|Web Configuration|Best Practices"
        }}
    ],
    "cannot_auto_fix": [
        {{
            "issue": "description of issue",
            "reason": "why it can't be auto-fixed",
            "manual_action": "what the user needs to do"
        }}
    ],
    "summary": "Summary of fixes being applied"
}}
```

Be conservative - only suggest changes that are safe defaults. If in doubt, skip the fix."""

            response = client.messages.create(
                model=CLAUDE_MODEL,
                max_tokens=2500,
                messages=[{"role": "user", "content": prompt}]
            )

            response_text = response.content[0].text

            # Extract JSON
            if "```json" in response_text:
                start = response_text.find("```json") + 7
                end = response_text.find("```", start)
                json_str = response_text[start:end].strip()
            elif "{" in response_text:
                start = response_text.find("{")
                end = response_text.rfind("}") + 1
                json_str = response_text[start:end]
            else:
                json_str = response_text

            result = json.loads(json_str)

            fixes = result.get("fixes", [])
            return True, f"Generated {len(fixes)} fixes", result

        except json.JSONDecodeError as e:
            return False, f"Failed to parse fix response: {e}", []
        except Exception as e:
            return False, str(e), []
