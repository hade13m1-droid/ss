# Hade Portfolio (Flask)

This project now runs as a Flask server with:
- Live backend-powered contact form (`POST /api/contact`)
- Persisted portfolio config in SQLite (`GET/POST /api/config`)
- Admin inbox (`GET /api/messages`)

## Run locally

```bash
python3 -m pip install -r requirements.txt
python3 app.py
```

Then open:
- `http://localhost:5000/`
- `http://localhost:5000/admin`

## GitHub publish steps

```bash
git remote add origin <your-repo-url>
git push -u origin <branch-name>
```

If your repo already has a remote, use:

```bash
git push
```
