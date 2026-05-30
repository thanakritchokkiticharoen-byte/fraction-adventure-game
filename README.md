# Fraction Adventure Game - Version 2

เกมผจญภัยเศษส่วนระดับประถมศึกษา สร้างด้วย Flask + HTML + CSS + JavaScript + SQLite

## ฟีเจอร์ Version 2
- Login / Register ผู้เล่น
- เลือกตัวละคร Knight / Wizard / Priest / Archer
- เลือกระดับ Easy / Normal / Hard
- 5 ด่าน ด่านละ 10 ข้อ
- จับเวลา 30 วินาทีต่อข้อ
- Wizard ได้ 35 วินาทีต่อข้อ
- Knight ได้ Crystal เริ่มต้น +5
- Priest มี Shield ตอบผิดฟรี 1 ครั้งต่อด่าน
- Archer ตอบไวภายใน 5 วินาที ได้โบนัส +2 Crystal
- Ranking รวมผู้เล่น
- Teacher Dashboard
- Export คะแนนเป็น CSV
- QR Code Page
- ปุ่ม Google Form ประเมินความพึงพอใจ

## วิธีรัน
```bash
cd fraction_adventure_game_v2
pip install -r requirements.txt
python app.py
```

เปิดเว็บ:
```text
http://127.0.0.1:5000
```

## แก้ Google Form
เปิดไฟล์ `app.py` แล้วแก้บรรทัด:
```python
GOOGLE_FORM_URL = "https://forms.gle/CHANGE_ME"
```

## แก้ URL QR Code หลัง Deploy
เปิดไฟล์ `app.py` แล้วแก้บรรทัด:
```python
PUBLIC_GAME_URL = "http://127.0.0.1:5000"
```
เป็น URL จริงของเว็บ เช่น
```python
PUBLIC_GAME_URL = "https://your-game.onrender.com"
```
