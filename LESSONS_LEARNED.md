# Lessons Learned - Cloudflare DNS Manager

## PyQt6 Development

### Lambda Binding in Loops
**Problem:** When connecting button signals inside a loop, lambdas capture the variable by reference, not value. All buttons end up using the last value.

```python
# WRONG - all buttons call with last filename
for filename in filenames:
    btn.clicked.connect(lambda: self.view_backup(filename))

# RIGHT - use functools.partial to bind the value
from functools import partial
for filename in filenames:
    btn.clicked.connect(partial(self.view_backup, filename))
```

### Dialog Window Flags for Resize/Maximize
**Problem:** QDialog by default doesn't have minimize/maximize buttons.

```python
# Enable resize and maximize for dialogs
self.setWindowFlags(
    Qt.WindowType.Window |
    Qt.WindowType.WindowMinMaxButtonsHint |
    Qt.WindowType.WindowCloseButtonHint
)
```

### Stylesheet Specificity
**Problem:** Global button styles override buttons in table cells, making them unreadable.

```css
/* Target buttons specifically inside tables */
QTableWidget QPushButton {
    background-color: #F2F3F4;
    color: #4C5351;
    border: 1px solid #7B7D72;
}
```

### QThread for API Calls
**Problem:** Long API calls freeze the GUI.

```python
class ApiWorker(QThread):
    finished = pyqtSignal(bool, str, dict)

    def run(self):
        result = self.client.api_call()
        self.finished.emit(True, "Done", result)

# Usage
self.worker = ApiWorker(...)
self.worker.finished.connect(self.on_complete)
self.worker.start()
```

## Claude API Integration

### Two-Step Validation Pattern
For user-provided text that needs parsing AND validation:
1. First call: Parse natural language → structured data
2. Second call: Validate against best practices → corrected data

This catches errors like `v=spfl` → `v=spf1` that pure parsing misses.

### JSON Response Extraction
Claude sometimes wraps JSON in markdown code blocks:

```python
if "```json" in response_text:
    start = response_text.find("```json") + 7
    end = response_text.find("```", start)
    json_str = response_text[start:end].strip()
elif "{" in response_text:
    start = response_text.find("{")
    end = response_text.rfind("}") + 1
    json_str = response_text[start:end]
```

### Prompt Engineering for DNS
- Be explicit about common typos: "v=spfl is a typo for v=spf1"
- Request structured JSON output with specific fields
- Include examples of expected output format
- Ask for "reason" fields to explain recommendations to users

## Credential Security

### Fernet Encryption with PBKDF2
- Use PBKDF2 for key derivation (480,000+ iterations)
- Fernet for symmetric encryption
- Never log or display API keys
- Clear sensitive data from memory when locking

```python
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

kdf = PBKDF2HMAC(
    algorithm=hashes.SHA256(),
    length=32,
    salt=salt,
    iterations=480000,
)
key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
fernet = Fernet(key)
```

## UI/UX Patterns

### Consistent Theming
- Use `setObjectName()` or `setProperty()` for targeted styling
- Keep font sizes consistent (8pt base, 12pt headings)
- Define color constants in a central styles module

### Health Assessment UX
- Show overall score prominently (A-F with color coding)
- Tree view for categories → findings drill-down
- Separate "what's wrong" from "how to fix"
- Always show manual action items for non-automatable fixes

### Pending Changes Pattern
- Queue changes, don't apply immediately
- Show diff view of pending changes
- AI review before applying
- Audit log everything

## Windows Deployment

### Start Menu Shortcut
Use PowerShell with WScript.Shell COM object:

```powershell
$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("$env:APPDATA\Microsoft\Windows\Start Menu\Programs\MyApp.lnk")
$Shortcut.TargetPath = "pythonw.exe"  # Use pythonw to hide console
$Shortcut.Arguments = "`"path\to\main.py`""
$Shortcut.WorkingDirectory = "path\to\app"
$Shortcut.Save()
```

### GitHub CLI
- Install via `winget install GitHub.cli`
- Auth with `gh auth login`
- Update repo: `gh repo edit owner/repo --description "..." --add-topic tag`

## Project Structure

```
app/
├── main.py              # Entry point, applies stylesheet
├── config/settings.py   # Constants, model names
├── core/                # Business logic
│   ├── credential_manager.py
│   ├── cloudflare_client.py
│   ├── claude_client.py
│   └── ...
├── gui/                 # PyQt6 UI
│   ├── main_window.py
│   ├── styles.py        # Centralized stylesheet
│   ├── *_dialog.py      # Feature dialogs
│   └── widgets/         # Reusable components
└── data/                # Runtime data (gitignored)
```

## Testing Tips

- Always syntax check before running: `python -m py_compile file.py`
- Test API integration with simple prompts first
- Check thread safety when updating UI from workers
- Verify signal/slot connections actually fire
