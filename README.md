# Sabilulungan — Staf AI v3

Workspace staf AI lokal dengan model melalui 9Router/OpenRouter. Beri tugas lewat dashboard; Manager dapat mendelegasikan ke spesialis, membaca sumber web, membuat file, dan memeriksa hasil. Progres berasal dari aktivitas runtime, bukan animasi kerja palsu.

## Menjalankan di Windows

1. Buka terminal di folder project dan jalankan `pip install -r requirements.txt`.
2. Salin `.env.example` ke `.env`, lalu atur `API_KEY`, `MODEL`, dan `API_URL` sesuai gateway lu.
3. Klik `START_DASHBOARD.bat`, atau jalankan `python dashboard.py`.
4. Buka http://127.0.0.1:5050. Pilih Manager, tulis tugas, lalu klik **Kerjakan tugas**.

Contoh tugas:

> Delegasikan ke copywriter untuk membuat 5 skrip reels horor Bahasa Indonesia, durasi sekitar 45 detik. Simpan tiap skrip sebagai file teks berbeda. Baca hasilnya lalu periksa apakah hook dan penutupnya jelas.

CLI alternatif: `python orchestrator.py` atau `python multi_agent.py`. Jangan jalankan CLI dan dashboard bersamaan dalam folder yang sama; keduanya memiliki worker dan memakai database yang sama.

## Fungsi yang tersedia

- Kantor pixel dengan 13 avatar staf, nama panggilan, dan meja. Klik avatar
  untuk memilih agen dan melihat tugas/memorinya. Animasi bekerja mengikuti
  agen yang sedang menjalankan langkah runtime, termasuk spesialis delegasi.
  Indikator menampilkan antrean, menunggu staf/persetujuan, selesai, dan gagal.
  Jika koneksi terputus, animasi berhenti dan status ditandai belum diperbarui.

- Antrean tugas latar belakang; menutup tab tidak menghentikan worker.
- Profil agen, konteks percakapan terpisah per agen utama, dan memori eksplisit per agen.
- Delegasi berantai maksimal 3 tingkat dengan total maksimal 24 langkah per tugas. Spesialis mengembalikan hasil ke agen pemberi tugas. Eksekusi serial untuk menghemat RAM dan mencegah benturan file.
- Tools `list_files`, `read_file`, `write_file`, `remember`, `delegate`, `read_url`, dan `run_python`.
- File tools dibatasi ke `workspace/`; file lama tidak ditimpa. Download file melalui dashboard.
- Membaca URL HTTPS publik sebagai teks, dengan batas ukuran, timeout, validasi DNS dan redirect. Tidak mendukung halaman yang memerlukan JavaScript atau login.
- Eksekusi Python setelah lu menyetujui kode persisnya di dashboard. Output/exit code dikembalikan ke agen, timeout 30 detik. Penolakan dikembalikan sebagai hasil tool agar agen dapat mencari alternatif.
- Rutinitas berulang berdasarkan interval menit. Simpan/jeda/aktifkan lewat dashboard. Jika aplikasi mati, jadwal yang terlewat dijalankan sekali setelah aktif; tidak menumpuk backlog.
- Skill berbentuk file Markdown di `workspace/skills/`. Minta agen menulis prosedur yang sudah berhasil ke `skills/nama.md`; daftar skill masuk ke konteks agen dan bisa dibaca dengan tool `read_file`.
- SQLite menyimpan tugas, aktivitas, memori, persetujuan, dan rutinitas. Tugas yang terputus ditandai `interrupted`, tidak diputar ulang otomatis.
- Hentikan tugas melalui dashboard. Panggilan model yang sedang berjalan berhenti setelah respons/timeout; kode Python yang sedang berjalan dihentikan pada pemeriksaan berikutnya.

## Batas yang perlu dipahami

Ini implementasi lokal fungsi inti, belum setara seluruh produk Grok Bot. Belum ada browser visual dengan klik/login, komputer cloud, aplikasi mobile, konektor akun, voice, grup chat, atau beberapa agen yang berjalan paralel. Model harus mengikuti protokol JSON; model yang tidak mengikuti protokol akan menghasilkan tugas gagal dengan pesan error, bukan laporan sukses palsu.

`run_python` berjalan langsung pada PC host, **bukan sandbox OS**. Kode dapat mengakses file, jaringan, dan menjalankan program dengan hak pengguna. Periksa setiap kode sebelum menyetujui. API key tidak diteruskan lewat environment subprocess, tetapi ini tidak mencegah kode membaca file konfigurasi pada PC. Timeout menghentikan proses Python utama; proses anak yang dibuat oleh kode tidak dijamin ikut berhenti. Rutinitas tidak dapat melewati persetujuan ini.

Semua agen berbagi workspace. Memori spesialis yang disimpan eksplisit dan aktivitas delegasinya bertahan; konteks percakapan otomatis diambil dari tugas selesai yang dimiliki agen tersebut. Reset memori mengarsipkan konteks tugas selesai dan menghapus memori eksplisit, tanpa menghapus file atau audit trail. Reset diblokir selama ada tugas aktif.

PC dan aplikasi harus hidup agar tugas/rutinitas berjalan. Server hanya mendengarkan localhost; tidak dirancang untuk diekspos ke internet.

## Pengujian

Tes koneksi **live** di PC yang menjalankan 9Router: klik `CHECK_9ROUTER.bat`
atau jalankan `python check_gateway.py` setelah mengisi `.env`. Tes memakai
gateway asli dan memeriksa delegasi, isi file, pembacaan coder/Manager, memori,
serta persistensi setelah runtime dibuka ulang. Klaim sukses model saja tidak
cukup. Database/file tes memakai folder sementara yang terpisah dari workspace
lu. Exit code 0 berarti seluruh pemeriksaan PASS; 1 berarti gagal. Tes dapat
memakai kuota model dan berjalan maksimal sekitar 10 menit ditambah waktu
penutupan panggilan model. Jangan merge berdasarkan tes tiruan saja jika
penerimaan koneksi live belum lolos.

Tes memori dikirim langsung ke coder sebagai tugas terpisah supaya tidak
bergantung pada kelengkapan instruksi yang diteruskan Manager. `memory`
memerlukan bukti tool `remember` sukses dan isi persis yang diminta.
`persistence` memeriksa tugas/aktivitas setelah runtime dibuka ulang;
`memory_persistence` khusus memeriksa memori tersimpan. Progres menampilkan
agen dan nama aksi tanpa isi respons gateway atau API key.

`python -m unittest discover -s tests -v`

Tes menggunakan model tiruan dan server HTTP nyata. Akses 9Router di PC pengguna harus diuji dengan konfigurasi pengguna; test suite tidak mengklaim koneksi tersebut sudah diuji.

Dependensi transkripsi/scraping lama ada di `requirements_full.txt` dan tidak diperlukan untuk dashboard inti.
