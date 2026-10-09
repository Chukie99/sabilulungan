import os, sys, json, urllib.request

API_URL = 'http://localhost:20128/v1/chat/completions'
AGENTS_FILE = 'agents.json'
ENV_FILE = ".env"

def load_env():
    config = {}
    if os.path.exists(ENV_FILE):
        with open(ENV_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                clean_line = line.strip()
                if '=' in clean_line and not clean_line.startswith('#'):
                    k, v = clean_line.split('=', 1)
                    config[k.strip()] = v.strip()
    return config

# Load config once
config = load_env()
API_KEY = config.get('API_KEY')
MODEL_NAME = config.get('MODEL', 'anthropic/claude-3.5-sonnet')

def save_env(provider, model, api_key):
    with open(ENV_FILE, 'w') as f:
        f.write(f"PROVIDER={provider}\n")
        f.write(f"MODEL={model}\n")
        f.write(f"API_KEY={api_key}\n")

def setup_wizard():
    print("=== ORCHESTRATOR CONFIGURATION ===")
    provider = input("Jenis Provider (contoh: 9router / openrouter / openai) [9router]: ").strip() or "9router"
    model = input("Isi Model (contoh: anthropic/claude-3.5-sonnet) [anthropic/claude-3.5-sonnet]: ").strip() or "anthropic/claude-3.5-sonnet"
    api_key = input("API Key (contoh: sk-or-v1-...): ").strip()
    
    save_env(provider, model, api_key)
    print("[OK] Konfigurasi tersimpan ke .env!\n")
    return provider, model, api_key

def load_agents():
    with open(AGENTS_FILE, 'r', encoding='utf-8') as f: return json.load(f)

def call_ai(system_prompt, user_prompt, model, api_key):
    API_URL = "http://localhost:20128/v1/chat/completions" if "9router" in model.lower() or "local" in model.lower() else "https://openrouter.ai/api/v1/chat/completions"
    
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt + "\nIf you generate code or project files, wrap them in markdown code blocks with the filename like ```python:main.py\nprint('hello')\n``` so the system can automatically save them to disk."},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.7
    }
    
    req = urllib.request.Request(API_URL, data=json.dumps(payload).encode('utf-8'), headers=headers, method='POST')
    try:
        with urllib.request.urlopen(req) as res:
            return json.loads(res.read())['choices'][0]['message']['content']
    except Exception as e:
        return f"[ERROR] Gagal akses API: {e}"

def extract_and_save_files(text):
    # Auto-extract code blocks formatted like ```python:filename.py ... ```
    import re
    pattern = r"```([a-zA-Z0-9_-]+):([a-zA-Z0-9_.-]+)\n(.*?)```"
    matches = re.findall(pattern, text, re.DOTALL)
    for lang, filename, content in matches:
        os.makedirs("output_project", exist_ok=True)
        filepath = os.path.join("output_project", filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content.strip())
        print(f"\n[BUILD SUCCESS] File otomatis dibuat: {filepath}")

def main():
    print("========================================")
    print("   AI MULTI-AGENT BUILDER & ORCHESTRATOR")
    print("========================================")
    
    config = load_env()
    if not config.get('API_KEY'):
        provider, model, api_key = setup_wizard()
    else:
        provider = config.get('PROVIDER', '9router')
        model = config.get('MODEL', 'anthropic/claude-3.5-sonnet')
        api_key = config.get('API_KEY')
        print(f"[INFO] Loaded config -> Provider: {provider} | Model: {model}\n")

    agents = load_agents()
    manager = agents['manager']
    
    print(f"Manager siap. Ketik goal lu (misal: 'Bikin script Python kalkulator web sederhana').\n")
    
    while True:
        user_input = input("You > ").strip()
        if not user_input: continue
        if user_input.lower() == 'exit': break
        
        print("\n[Manager] Menganalisis goal dan merancang tugas...")
        response = call_ai(manager['prompt'], user_input, model, api_key)
        print(f"\nMANAGER:\n{response}\n")
        
        extract_and_save_files(response)
        
        # Cek apakah manager mendelegasikan ke coder
        if "DELEGATE:coder" in response or "coder" in response.lower():
            print("\n[Orchestrator] Meneruskan tugas pembuatan kode ke CODER...")
            coder = agents['coder']
            coder_res = call_ai(coder['prompt'], f"Berdasarkan goal: {user_input}, tuliskan kode lengkapnya dan bungkus dalam format ```lang:filename.ext ... ```", model, api_key)
            print(f"\nCODER:\n{coder_res}\n")
            extract_and_save_files(coder_res)

if __name__ == '__main__':
    main()
