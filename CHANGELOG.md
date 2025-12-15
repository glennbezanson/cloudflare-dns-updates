# Changelog

All notable changes to this project will be documented in this file.

## [1.3.0] - 2024-12-10

### Added
- **DNS Health Assessment** - Comprehensive health check with A-F grading
  - Analyzes Email Security (SPF, DKIM, DMARC, MX)
  - Checks Security Records (CAA, verification TXT)
  - Reviews Web Configuration (A, AAAA, www)
  - Best Practices evaluation
  - Critical issues highlighted with recommendations
- **Implement Best Practices** - One-click fix generation
  - Claude generates specific DNS record fixes
  - Select which fixes to apply
  - Adds fixes to pending changes for review
  - Shows manual action items for non-automatable fixes

### Changed
- Reduced font size from 10pt to 8pt for compact UI
- Quick Add dialog now resizable and maximizable
- Table cell buttons (View/Compare/Delete) now readable with proper contrast

## [1.2.0] - 2024-12-10

### Added
- **Professional UI Styling** - Complete UI refresh with consistent color theme
  - Primary blue (#486D87) for headers, navigation, primary buttons
  - Accent green (#C6D219) for accent buttons, success states, CTAs
  - Centralized stylesheet with consistent styling across all dialogs
- Validation status badges with theme colors

### Fixed
- Backup View/Compare/Delete buttons not working (lambda binding issue)
- Added automatic tab switching to show backup comparison results

## [1.1.0] - 2024-12-10

### Added
- **Paste Request** feature - paste ticket/email text and Claude parses DNS records
- Two-step validation: Parse → Validate against best practices
- Auto-fix common errors:
  - `v=spfl` → `v=spf1` (common typo)
  - `include: example.com` → `include:example.com` (extra space)
  - SPF, DKIM, DMARC syntax validation
- Color-coded validation status (green=fixed, yellow=warning)
- Tooltip shows original content when fixes applied

## [1.0.0] - 2024-12-10

### Added
- Initial release
- Secure encrypted credential storage with master password
- Full DNS record management (A, AAAA, CNAME, MX, TXT, NS, SRV, CAA)
- Claude AI integration for change review
- Change approval workflow with diff view
- Audit logging with export capability
- Zone backup/restore (JSON and BIND format)
- SPF record syntax validation
- Record filtering and search
