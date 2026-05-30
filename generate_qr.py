"""สร้าง QR Code หลังจากมี URL เว็บจริงแล้ว
วิธีใช้:
python generate_qr.py https://your-game-url.com
"""
import sys
import qrcode

url = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:5000"
img = qrcode.make(url)
img.save("fraction_game_qr.png")
print(f"Created fraction_game_qr.png for {url}")
