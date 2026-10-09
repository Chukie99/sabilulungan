# Sabilulungan (Digital Staff System)

Framework multi-agen kolaboratif berbasis Python & Local LLM Gateway (9Router / OpenRouter) dengan antarmuka dashboard yang aman.

## Struktur Project
- `config.py`: Pengelola konfigurasi dan `.env` terpusat.
- `dashboard.py`: Secure HTTP server dengan pembatasan rute dan proteksi *Origin/Host*.
- `orchestrator.py`: CLI multi-agen dan pipeline delegasi tugas.
- `multi_agent.py`: Interface alternatif interaktif.
- `index.html`: Dashboard UI (XSS-mitigated, with chat & reset support).
- `agents.json`: Profil agen (Manager, Coder, Designer, dsb).

## Instalasi & Cara Menjalankan

1. **Install Dependensi:**
   ```bash
   pip install -r requirements.txt
   ```
2. **Konfigurasi Environment (.env):**
   Salin file `.env.example` menjadi `.env`, lalu isi konfigurasi API Key dan Provider Anda:
   ```env
   PROVIDER=9router
   API_KEY=your_api_key_here
   MODEL=gpt-4o
   ```
3. **Menjalankan Dashboard:**
   Klik dua kali pada `START_DASHBOARD.bat` atau jalankan via terminal:
   ```bash
   python dashboard.py
   ```
   Akses di browser: `http://localhost:5050`
