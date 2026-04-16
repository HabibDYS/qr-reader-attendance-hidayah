# Sistem Pembaca QR Kehadiran (QR Reader Attendance System)

Sistem pelacakan kehadiran berbasis Flask yang komprehensif menggunakan kode QR untuk pemeriksaan masuk/keluar siswa. Sistem ini menampilkan portal admin dan siswa terpisah dengan pelacakan kehadiran real-time, pembuatan laporan otomatis, dan manajemen data.

**© 2026 SMK Hidayah. Hak cipta dilindungi.**

---

## Daftar Isi

1. [Ikhtisar Proyek](#ikhtisar-proyek)
2. [Fitur](#fitur)
3. [Persyaratan Sistem](#persyaratan-sistem)
4. [Instalasi & Pengaturan](#instalasi--pengaturan)
5. [Pengaturan Database](#pengaturan-database)
6. [Impor & Konversi Data](#impor--konversi-data)
7. [Manajemen Pengguna](#manajemen-pengguna)
8. [Menjalankan Aplikasi](#menjalankan-aplikasi)
9. [Struktur Proyek](#struktur-proyek)
10. [Konfigurasi](#konfigurasi)
11. [Pemecahan Masalah](#pemecahan-masalah)

---

## Ikhtisar Proyek

Sistem Pembaca QR Kehadiran adalah solusi terpusat untuk melacak kehadiran siswa menggunakan teknologi kode QR. Sistem ini menyediakan:

- **Pelacakan Kehadiran Real-time**: Siswa memindai kode QR untuk menandai kehadiran
- **Dashboard Admin**: Pantau kehadiran, kelola siswa, dan buat laporan
- **Pembuatan Kode QR Otomatis**: Setiap siswa mendapat kode QR unik
- **Impor Data**: Konversi file Excel berisi data siswa ke format CSV dan impor ke sistem
- **Laporan Kehadiran**: Buat laporan kehadiran mingguan/bulanan dalam format CSV
- **Dukungan Multi-rolle**: Peran pengguna Admin dan Siswa dengan tingkat akses berbeda

---

## Fitur

### Fitur Admin
- Daftarkan dan kelola akun siswa
- Buat dan kelola kode QR siswa
- Pindai kode QR untuk pelacakan kehadiran
- Lihat catatan kehadiran dan buat laporan
- Ekspor data kehadiran ke CSV
- Manajemen akun admin

### Fitur Siswa
- Lihat kode QR pribadi untuk absen
- Absen/Pulang melalui pemindaian kode QR
- Lihat catatan kehadiran pribadi
- Unduh laporan kehadiran mingguan
- Perbarui informasi profil

### Fitur Sistem
- Penandaan kehadiran terlambat otomatis (default: setelah pukul 7:00 pagi)
- Sinkronisasi kehadiran real-time
- Hashing kata sandi aman
- Manajemen sesi dengan Flask-Login
- Fungsionalitas impor/ekspor CSV
- Versioning database dengan SQLAlchemy

---

## Persyaratan Sistem

- **Python**: Versi 3.8 atau lebih tinggi
- **Database**: SQLite (disertakan dengan Python)
- **Webcam**: Diperlukan untuk pemindaian kode QR
- **Sistem Operasi**: Windows, macOS, atau Linux

---

## Instalasi & Pengaturan

### Langkah 1: Clone atau Unduh Proyek

```bash
cd c:\Users\Lenovo\qr-reader-attendance-system
```

### Langkah 2: Instal Dependensi Python

```bash
pip install -r requirements.txt
```

**Paket yang Diperlukan:**
- Flask 3.1.3 - Framework web
- Flask-SQLAlchemy 3.1.1 - ORM Database
- Flask-Login 0.6.3 - Manajemen sesi pengguna
- qrcode[pil] 8.2 - Pembuatan kode QR
- opencv-python 4.11.0.86 - Pengolahan gambar dan akses webcam
- pyzbar 0.1.9 - Pembacaan kode QR
- pandas 2.2.3 - Pemrosesan data dan penanganan CSV
- Pillow 11.2.1 - Pengolahan gambar
- python-dotenv 1.1.0 - Variabel lingkungan

### Langkah 3: Inisialisasi Database

Jalankan skrip inisialisasi database untuk membuat tabel dan direktori:

```bash
python init_db.py
```

Ini akan:
- Membuat database SQLite di `instance/attendance.db`
- Membuat folder upload di `app/static/uploads`
- Membuat folder kode QR di `app/static/qrcodes`

---

## Pengaturan Database

### Struktur Database

Sistem menggunakan SQLite dengan tabel utama berikut:

**Tabel Pengguna:**
- `id` - ID Pengguna (kunci utama)
- `username` - Nama pengguna unik
- `email` - Alamat email
- `name` - Nama lengkap
- `password_hash` - Hash kata sandi
- `role` - Peran pengguna ('admin' atau 'siswa')
- `qr_code` - Nama file kode QR
- `qr_code_created_at` - Stempel waktu pembuatan kode QR
- `profile_picture` - Nama file foto profil
- `email_notifications` - Preferensi notifikasi email
- `attendance_reminders` - Preferensi pengingat kehadiran
- `weekly_reports` - Preferensi laporan mingguan
- `language` - Preferensi bahasa pengguna (default: 'en')
- `timezone` - Zona waktu pengguna (default: 'UTC')
- `last_login` - Stempel waktu login terakhir
- `login_attempts` - Penghitung upaya login gagal
- `account_locked_until` - Stempel waktu kunci akun

**Tabel Kehadiran:**
- `id` - ID Catatan (kunci utama)
- `user_id` - Kunci asing ke Pengguna
- `check_in` - Stempel waktu masuk
- `check_out` - Stempel waktu pulang
- `date` - Tanggal kehadiran
- `status` - Status ('hadir', 'terlambat', 'tidak hadir', 'dengan izin')
- `notes` - Catatan tambahan

---

## Impor & Konversi Data

### Ikhtisar

Sistem menyediakan alat untuk mengimpor data siswa dari file Excel dan mengkonversinya ke format CSV untuk operasi massal.

### Mengonversi Excel ke CSV

#### Langkah 1: Persiapkan File Excel Anda

Pastikan file Excel Anda berisi:
- Nama siswa (kolom harus berisi teks "Nama Siswa" atau "nama")
- Kelas/Tingkat siswa (jika beberapa lembar, setiap lembar mewakili kelas)
- Beberapa lembar untuk kelas berbeda (10, 11, 12)

Contoh struktur:
```
Lembar: 10 TKJ
| No | Nama Siswa      | ... |
|----|-----------------|-----|
| 1  | Budi Santoso    | ... |
| 2  | Siti Nurhaliza  | ... |
```

#### Langkah 2: Jalankan Skrip Konversi

```bash
python convert_excel_to_csv.py
```

**Apa yang dilakukan skrip:**
1. Membaca semua lembar dari file Excel (misalnya, "Data Siswa 10.11.12 TA. 2026.xlsx")
2. Mengekstrak nama siswa dari setiap lembar
3. Menghasilkan nama pengguna unik dari nama (mengonversi ke huruf kecil, mengganti spasi dengan garis bawah)
4. Menangani nama pengguna duplikat secara otomatis (menambahkan akhiran penghitung)
5. Mengeluarkan file gabungan `students.csv` di `app/static/qrcodes/app/static/students.csv`

**Format CSV yang Dihasilkan:**
```csv
username,name,class
budi_santoso,Budi Santoso,TKJ 10
siti_nurhaliza,Siti Nurhaliza,TKJ 10
```

**Logika Pembuatan Nama Pengguna:**
- Menghapus karakter khusus
- Mengganti spasi dengan garis bawah
- Mengonversi ke huruf kecil
- Menangani duplikat dengan menambahkan penghitung (misalnya, `john_doe2`)

#### Langkah 3: Pembuatan CSV Manual (Alternatif)

Jika Anda tidak memiliki file Excel, buat CSV secara manual:

```csv
username,name,class
john_doe,John Doe,X TKJ
jane_smith,Jane Smith,X TKJ
```

Simpan sebagai `students.csv`

### Mengimpor Siswa dari CSV

#### Opsi A: Impor Massal melalui Portal Admin

1. Masuk ke akun admin
2. Buka **Dashboard Admin > Kelola Siswa**
3. Klik **Impor Siswa**
4. Unggah file CSV
5. Sistem akan membuat akun dan kode QR

#### Opsi B: Pembuatan Siswa Manual

```bash
# Buat siswa tunggal secara manual (melalui portal admin)
# Atau gunakan: python create_test_student.py
```

---

## Manajemen Pengguna

### Membuat Akun Admin

#### Metode 1: Menggunakan Skrip

```bash
python create_admin.py
```

Skrip akan meminta Anda untuk:
- Nama pengguna admin
- Email admin
- Kata sandi admin
- Nama lengkap admin

#### Metode 2: Menggunakan Kunci Registrasi

1. Mulai aplikasi
2. Buka `/auth/register`
3. Selama pendaftaran, masukkan **Kunci Registrasi Admin** (default: "Cheese borger")
4. Akun akan dibuat sebagai admin

### Membuat Akun Siswa

#### Metode 1: Impor via Admin

Lihat bagian "Impor & Konversi Data" di atas

#### Metode 2: Registrasi Manual

1. Siswa membuka `/auth/register`
2. Mengisi detail pendaftaran
3. Akun dibuat dengan peran 'siswa'

#### Metode 3: Pembuatan Siswa Uji

```bash
python create_test_student.py
```

Membuat akun siswa uji untuk tujuan pengembangan.

### Operasi Admin

```bash
# Daftarkan admin sekunder
python register_admin.py

# Perbarui kredensial admin
python update_admin.py

# Daftar semua pengguna
python list_users.py

# Hapus semua data pengguna (hati-hati!)
python clear_data.py

# Atur ulang database
python reset_db.py
```

---

## Menjalankan Aplikasi

### Metode 1: Menggunakan Python Langsung

```bash
python run.py
```

Aplikasi akan dimulai di: **http://127.0.0.1:8000**

### Metode 2: Menggunakan File Batch (Windows)

```bash
start_app.bat
```

### Metode 3: Perintah Flask Manual

```bash
set FLASK_APP=run.py
set FLASK_ENV=development
flask run --port=8000
```

### Titik Akses

| URL | Tujuan |
|-----|--------|
| `http://localhost:8000` | Halaman utama |
| `http://localhost:8000/auth/login` | Halaman login |
| `http://localhost:8000/auth/register` | Halaman registrasi |
| `http://localhost:8000/admin/` | Dashboard admin (hanya admin) |
| `http://localhost:8000/student/` | Dashboard siswa (hanya siswa) |
| `http://localhost:8000/attendance/` | Portal kehadiran |

---

## Struktur Proyek

```
qr-reader-attendance-system/
├── app/                              # Aplikasi Flask utama
│   ├── __init__.py                  # Pabrik aplikasi dan inisialisasi
│   ├── config.py                    # Pengaturan konfigurasi
│   ├── models/                      # Model database
│   │   ├── user.py                  # Model pengguna
│   │   └── attendance.py            # Model kehadiran
│   ├── routes/                      # Rute API
│   │   ├── admin.py                 # Rute admin
│   │   ├── auth.py                  # Rute autentikasi
│   │   ├── student.py               # Rute siswa
│   │   ├── attendance.py            # Rute kehadiran
│   │   └── main.py                  # Rute utama
│   ├── templates/                   # Template HTML
│   │   ├── base.html                # Template dasar
│   │   ├── index.html               # Halaman utama
│   │   ├── admin/                   # Template admin
│   │   ├── student/                 # Template siswa
│   │   └── attendance/              # Template kehadiran
│   ├── static/                      # File statis
│   │   ├── uploads/                 # File yang diunggah
│   │   └── qrcodes/                 # Kode QR yang dibuat
│   └── utils/                       # Fungsi utilitas
│       ├── qr_generator.py          # Pembuatan kode QR
│       └── attendance.py            # Utilitas kehadiran
├── instance/                        # Folder instance
│   └── attendance.db                # Database SQLite
├── config.py                        # Konfigurasi akar
├── run.py                           # Titik masuk aplikasi
├── init_db.py                       # Inisialisasi database
├── convert_excel_to_csv.py          # Konverter Excel ke CSV
├── create_admin.py                  # Pembuat akun admin
├── create_test_student.py           # Pembuat siswa uji
├── list_users.py                    # Daftar semua pengguna
├── register_admin.py                # Daftarkan admin sekunder
├── update_admin.py                  # Perbarui kredensial admin
├── clear_data.py                    # Hapus semua data
├── reset_db.py                      # Atur ulang database
├── requirements.txt                 # Dependensi Python
└── README.md                        # File ini
```

---

## Konfigurasi

### Edit Konfigurasi

Edit `config.py` untuk memodifikasi:

```python
# Kunci rahasia untuk manajemen sesi
SECRET_KEY = 'Hoshimachi Suisei is the best waifu'

# Kunci registrasi admin (lindungi pembuatan akun admin)
ADMIN_REGISTRATION_KEY = 'Cheese borger'

# Ambang batas terlambat (kapan kehadiran ditandai sebagai terlambat)
LATE_THRESHOLD_HOUR = 7      # 7:00 pagi
LATE_THRESHOLD_MINUTE = 0

# Pengaturan unggahan file
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # Maks 16 MB

# Lokasi database
SQLALCHEMY_DATABASE_URI = 'sqlite:///instance/attendance.db'
```

### Variabel Lingkungan

Buat file `.env` di akar proyek:

```env
FLASK_ENV=development
SECRET_KEY=your-secret-key-here
ADMIN_REGISTRATION_KEY=your-admin-key-here
DATABASE_URL=sqlite:///instance/attendance.db
```

---

## Pemecahan Masalah

### Masalah Database

**Kesalahan: "File database tidak ditemukan"**
```bash
python init_db.py
```

**Kesalahan: "Tabel sudah ada"**
```bash
python reset_db.py
# Ini akan menghapus semua data dan membuat ulang tabel
```

### Masalah Impor

**Kesalahan: "File Excel tidak ditemukan"**
- Pastikan file Excel berada di direktori akar proyek
- Periksa nama file cocok di `convert_excel_to_csv.py`
- File harus: "Data Siswa 10.11.12 TA. 2026.xlsx"

**Impor CSV tidak berfungsi:**
- Verifikasi CSV memiliki kolom yang benar: `username,name,class`
- Periksa karakter khusus dalam nama file
- Pastikan enkoding file adalah UTF-8

### Masalah Aplikasi

**Kesalahan: "Port 8000 sudah digunakan"**
```bash
# Gunakan port yang berbeda
python -m flask run --port=5000
```

**Webcam tidak terdeteksi:**
- Periksa apakah izin webcam diberikan
- Pastikan tidak ada aplikasi lain yang menggunakan webcam
- Instal ulang opencv-python: `pip install --upgrade opencv-python`

**Pemindaian kode QR tidak berfungsi:**
```bash
# Verifikasi instalasi pyzbar
pip install --upgrade pyzbar

# Windows: Mungkin perlu instalasi manual pustaka zbar
```

### Masalah Login

**Kesalahan: "Pengguna tidak ditemukan"**
- Buat akun pengguna terlebih dahulu atau gunakan fitur impor
- Periksa ejaan nama pengguna

**Kesalahan: "Kata sandi tidak valid"**
- Atur ulang kata sandi (admin dapat mengatur ulang kata sandi siswa)
- Gunakan kapitalisasi yang benar jika kata sandi peka huruf besar-kecil

### Masalah Kinerja

**Database lambat:**
- Hapus catatan kehadiran lama menggunakan skrip pengarsipan
- Buat ulang indeks database: `python reset_db.py`

**Unggahan file besar:**
- Modifikasi `MAX_CONTENT_LENGTH` di config.py
- Default adalah 16 MB, tingkatkan jika diperlukan

---

## Panduan Memulai Cepat

### Untuk Pengaturan Pertama Kali:

```bash
# 1. Instal dependensi
pip install -r requirements.txt

# 2. Inisialisasi database
python init_db.py

# 3. Buat akun admin
python create_admin.py

# 4. Mulai aplikasi
python run.py

# 5. Login di http://localhost:8000
```

### Untuk Mengimpor Data Siswa:

```bash
# 1. Persiapkan file Excel dengan nama siswa
# 2. Jalankan konversi
python convert_excel_to_csv.py

# 3. Impor melalui dashboard admin atau buat akun secara manual
```

### Untuk Operasi Harian:

```bash
# Mulai server
python run.py

# Akses di http://localhost:8000
```

---

## Dukungan & Dokumentasi

- **Model Database**: Lihat `app/models/` untuk struktur tabel terperinci
- **Rute**: Lihat `app/routes/` untuk titik akhir API
- **Utilitas**: Lihat `app/utils/` untuk fungsi pembantu
- **Konfigurasi**: Edit `config.py` dan variabel lingkungan

---

## Lisensi

© 2026 SMK Hidayah. Hak cipta dilindungi.

Perangkat lunak ini bersifat proprietary dan rahasia. Penyalinan atau distribusi tanpa izin dilarang.

---

**Terakhir Diperbarui**: April 2026
**Versi**: 1.0.0
