# INSTALL: Dependencies untuk Sabilulungan

## Windows (Native)
```cmd
# Buka Git Bash (atau Windows PowerShell, tapi PATH pakai bash)
cd C:\Users\SOPIAN\agent_hub
pip install -r requirements.txt
pip install -r requirements_full.txt
```

## Apa yg ini install (kecil sekali)
- **requests**, **python-dotenv**, **urllib3**
- **faster-whisper** → Transkripsi audio lokal (offline)
- **scrapling** → Scrape web & bypass anti-bot
- **yfinance**, **polymarket** → Crawler data finansial
- **lancedb** → Vektor lokal, no-SQL memory

Semua pakai CPU: **tak butuh GPU, RAM < 500 MB**.

## Mengecek
a) Console:
```
python tools_transcribe.py missing.wav
# keluar: Error: File missing.wav tidak ditemukan.

python tools_scrape.py https://example.com
# keluar: Data bersih halaman contoh (sekitar 5k char).
```

b) Verify import:
```
python verify_tools.py
# keluar: faster_whisper: IMPORT OK, scrapling: IMPORT OK, tools_transcribe: LOAD OK, tools_scrape: LOAD OK
```

Semua siap: **Sabilulungan Agent Framework** siap operasi.
