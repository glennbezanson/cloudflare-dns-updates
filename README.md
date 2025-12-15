# Cloudflare DNS Manager

A Python GUI application for managing Cloudflare DNS records with Claude AI-powered review.

![Python](https://img.shields.io/badge/python-3.10+-blue.svg)
![PyQt6](https://img.shields.io/badge/PyQt6-6.5+-green.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)

## Features

- **Paste Request (Natural Language Input)** - Paste a ticket or email, Claude parses and validates DNS records automatically
  - Two-step process: Parse → Validate against best practices
  - Auto-fixes common errors (v=spfl → v=spf1, extra spaces in SPF includes)
  - Shows original vs corrected with color-coded status
- **Secure Credential Storage** - Master password encrypts API keys using Fernet encryption (PBKDF2 key derivation)
- **Full DNS Record Management** - Support for A, AAAA, CNAME, MX, TXT, NS, SRV, CAA records
- **Claude AI Review** - AI-powered analysis of DNS changes before applying:
  - SPF record syntax validation
  - Duplicate record detection
  - Security issue warnings
  - Best practice recommendations
- **Change Approval Workflow** - Queue changes → Get AI review → Approve → Apply
- **Audit Logging** - Complete trail of all DNS changes with timestamps
- **Zone Backup/Restore** - Export/import zones as JSON or BIND format

## Screenshots

```
┌─────────────────────────────────────────────────────────────────┐
│ Cloudflare DNS Manager                              [─] [□] [×] │
├─────────────────────────────────────────────────────────────────┤
│ File  Edit  View  Help                                          │
├─────────────────────────────────────────────────────────────────┤
│ ┌─────────────┐ ┌─────────────────────────────────────────────┐ │
│ │ Zones       │ │ DNS Records for: example.com                │ │
│ ├─────────────┤ ├─────────────────────────────────────────────┤ │
│ │○ example.com│ │ Type │ Name    │ Content          │ TTL    │ │
│ │  domain2.net│ │──────┼─────────┼──────────────────┼────────│ │
│ │  site3.org  │ │ A    │ @       │ 192.168.1.1      │ Auto   │ │
│ │             │ │ CNAME│ www     │ example.com      │ Auto   │ │
│ │             │ │ MX   │ @       │ mail.example.com │ 3600   │ │
│ │             │ │ TXT  │ @       │ v=spf1 include...│ Auto   │ │
│ └─────────────┘ └─────────────────────────────────────────────┘ │
│                                                                 │
│ [+ Add Record]  [Edit]  [Delete]  │  Pending Changes: 2        │
│                                                                 │
│ [🤖 Review with Claude]                      [Apply Changes]    │
└─────────────────────────────────────────────────────────────────┘
```

## Installation

### Prerequisites

- Python 3.10 or higher
- pip

### Install Dependencies

```bash
pip install -r requirements.txt
```

Or install manually:

```bash
pip install PyQt6 cloudflare anthropic cryptography
```

## Usage

### Running the Application

```bash
python main.py
```

### First-Time Setup

1. **Create Master Password** - On first launch, you'll be prompted to create a master password (minimum 8 characters). This encrypts all stored credentials.

2. **Configure API Keys** - Go to `File → Settings` and enter:
   - **Cloudflare API Token** - [Create one here](https://dash.cloudflare.com/profile/api-tokens) with "Edit zone DNS" permissions
   - **Anthropic API Key** - [Get one here](https://console.anthropic.com/) for Claude AI review

3. **Test Connections** - Click "Test Connection" for each API to verify they work.

### Managing DNS Records

1. **Select a Zone** - Click on a domain in the left panel
2. **View Records** - All DNS records are displayed in the table
3. **Add/Edit/Delete** - Use the buttons or double-click to edit
4. **Queue Changes** - Changes are queued, not applied immediately
5. **Review with Claude** - Click "Review with Claude AI" for analysis
6. **Apply Changes** - After review, click "Apply Changes"

### Paste Request (Quick Add)

The fastest way to add DNS records from tickets or emails:

1. Click the green **"Paste Request"** button
2. Paste your ticket text, e.g.:
   ```
   Can someone help John on ticket 1077. He needs these TXT records:

   apple-domain-verification=Pjl0nznIinJKyKF1
   google-site-verification=7uHnDNu8t-aeAGAMX5L9k6mD9K6_ZfbumR7V73AUoIM
   v=spfl include:spf.protection.outlook.com include: servers.mcsv.net -all
   ```
3. Click **"Parse & Validate with Claude AI"**
4. Claude will:
   - Extract DNS records from the text
   - Validate against best practices
   - Auto-fix errors (e.g., `v=spfl` → `v=spf1`, remove extra spaces)
5. Review the validated records (green = fixed, yellow = warning)
6. Click **"Add Selected Records"** to queue them

### Backup & Restore

- `Zone → Backup/Restore` to create backups
- Export as JSON or BIND zone file format
- Compare backups against current state

### Audit Log

- `View → Audit Log` to see all changes
- Filter by domain or action type
- Export log for compliance

## Project Structure

```
cloudflare-dns-manager/
├── main.py                    # Application entry point
├── requirements.txt           # Python dependencies
├── config/
│   └── settings.py            # App configuration constants
├── core/
│   ├── credential_manager.py  # Encrypted credential storage
│   ├── cloudflare_client.py   # Cloudflare API wrapper
│   ├── claude_client.py       # Anthropic/Claude API client
│   ├── audit_logger.py        # Change audit logging
│   └── zone_backup.py         # Backup/restore functionality
├── gui/
│   ├── main_window.py         # Main application window
│   ├── zone_panel.py          # Zone/domain selector
│   ├── record_panel.py        # DNS record table
│   ├── natural_input_dialog.py # Paste Request / natural language input
│   ├── settings_dialog.py     # API key configuration
│   ├── review_dialog.py       # Claude AI review dialog
│   ├── audit_viewer.py        # Audit log viewer
│   ├── backup_dialog.py       # Backup/restore UI
│   └── widgets/
│       ├── record_editor.py   # Add/edit record form
│       └── diff_viewer.py     # Change diff display
├── utils/
│   └── validators.py          # DNS record validation
└── data/                      # Created at runtime
    ├── config.enc             # Encrypted credentials
    ├── audit.log              # Audit trail
    └── backups/               # Zone backup files
```

## Security

- **Encryption** - Credentials are encrypted using Fernet symmetric encryption
- **Key Derivation** - Master password is processed with PBKDF2 (480,000 iterations)
- **No Plain Text** - API keys are never stored or logged in plain text
- **Local Storage** - All data stays on your machine

## API Requirements

### Cloudflare API Token

Create a token at [Cloudflare Dashboard](https://dash.cloudflare.com/profile/api-tokens) with:
- **Permissions**: Zone → DNS → Edit
- **Zone Resources**: Include → All zones (or specific zones)

### Anthropic API Key

Get an API key at [Anthropic Console](https://console.anthropic.com/):
- Used for Claude AI review of DNS changes
- Optional but recommended for catching errors

## Claude AI Review

When you click "Review with Claude AI", the system:

1. Sends current records and pending changes to Claude
2. Claude analyzes for:
   - SPF/DKIM/DMARC syntax errors
   - Duplicate or conflicting records
   - Security implications
   - Best practices
3. Returns assessment: **SAFE**, **CAUTION**, or **DANGER**
4. Provides specific issues, warnings, and recommendations

## License

MIT License - see [LICENSE](LICENSE) for details.

## Contributing

Contributions welcome! Please open an issue or PR.

## Credits

Built with:
- [PyQt6](https://www.riverbankcomputing.com/software/pyqt/) - GUI framework
- [Cloudflare Python SDK](https://github.com/cloudflare/cloudflare-python) - DNS management
- [Anthropic Python SDK](https://github.com/anthropics/anthropic-sdk-python) - Claude AI integration
- [Cryptography](https://cryptography.io/) - Secure credential storage

---

Made with Claude Code
