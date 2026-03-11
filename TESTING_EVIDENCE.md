# Testing Evidence - UI Screenshots

This file records the UI verification run for the Placement Portal frontend.

## Commands used

```bash
cd frontend
python -m http.server 8080
```

Playwright script was used to capture:
- Login/Register page
- Admin dashboard (logged in)
- Company dashboard (logged in)
- Student dashboard (logged in)

## Note

For deterministic screenshot capture of all role pages in one run, API responses were mocked during Playwright automation.
