# Fraction Adventure Game - Web Deploy Version

## Run locally
```cmd
pip install -r requirements.txt
python app.py
```
Open: http://127.0.0.1:5000

## Deploy to Render Free
1. Create account at Render.com
2. Upload this project to GitHub
3. Render > New > Web Service > Connect GitHub repository
4. Settings:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn app:app`
5. Environment Variables:
   - SECRET_KEY = any long random text
   - PUBLIC_GAME_URL = your Render URL, e.g. `https://fraction-adventure-game.onrender.com`
   - GOOGLE_FORM_URL = your Google Form URL
6. Open your Render URL.
7. QR code page: `/qr`

## Important note
This version uses SQLite. On free hosting, database persistence can reset after redeploy/restart depending on host storage. For classroom testing this is OK. For real long-term ranking, upgrade later to PostgreSQL.
