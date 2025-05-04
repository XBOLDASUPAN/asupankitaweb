# Asupan Bersama

Aplikasi web untuk mengelola dan berbagi video dari DoodStream.

## Fitur

- Panel admin untuk mengelola video
- Manajemen kategori
- Upload thumbnail
- Tampilan publik yang responsif
- Pencarian video
- Penghitung views

## Teknologi

- Python 3.11
- Flask
- SQLAlchemy
- Bootstrap 5
- Font Awesome

## Instalasi

1. Clone repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Jalankan aplikasi:
   ```
   python app.py
   ```

## Deployment

1. Pastikan semua dependencies terinstall
2. Set environment variables yang diperlukan
3. Jalankan dengan Gunicorn:
   ```
   gunicorn app:app
   ```

## Environment Variables

- `FLASK_ENV`: development/production
- `SECRET_KEY`: random string untuk keamanan
- `PORT`: port untuk running aplikasi (default: 8080)

## Lisensi

MIT License
