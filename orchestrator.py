import os, sys, json, urllib.request

API_URL = 'http://localhost:20128/v1/chat/completions'
AGENTS_FILE = 'agents.json'
ENV_FILE = ".env"

from config import CONFIG

# Load config once
API_KEY = CONFIG.get('API_KEY')
MODEL_NAME = CONFIG.get('MODEL', 'anthropic/claude-3.5-sonnet')
PROVIDER_NAME = CONFIG.get('PROVIDER', '9router')

def save_env(provider, model, api_key):
    with open(ENV_FILE, 'w', encoding='utf-8') as f:
        f.write(f"PROVIDER={provider}\n")
        f.write(f"MODEL={model}\n")
        f.write(f"API_KEY={api_key}\n")

def load_agents():
    with open(AGENTS_FILE, 'r', encoding='utf-8') as f: return json.load(f)

def call_ai(system_prompt, user_prompt, model, api_key, provider="9router"):
    if provider.lower() == 'openrouter':
        API_URL = "https://openrouter.ai/api/v1/chat/completions"
    else:
        API_URL = "http://localhost:20128/v1/chat/completions"
    
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}
    payload = {
        "model": model,
        "messages": [
            {
"role": "system", 
"content": system_prompt + "\n**CRITICAL EMITTER:** You MUST output responses as valid JSON. Do NOT wrap in markdown fences. Example valid output: {\\"delegation_action\\": \\"progress\\", \\"subtasks\\": [...], \\"notes\\": \"...\\"} or {\\"delegation_action\\": \\"complete\\", \\"final_response\\": \"...\\"}. Unless explicitly delegated, your final_response field contains the full answer directly – do not prefix or add meta."
            },
            {
"role": "user", 
"content": user_prompt
            }
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
        response = call_ai(manager['prompt'], user_input, model, api_key, provider)
        print(f"\nMANAGER:\n{response}\n")
        
        extract_and_save_files(response)
        
        # Cek apakah manager mendelegasikan ke coder (JSON field check)
        try:
            json_start = response.find('{')
            if json_start != -1:
                json_response_str = '{' + response[json_start:]
                manager_json = json.loads(json_response_str)
                
                # If manager explicitly signals delegation
                if manager_json.get('delegation_action') == 'delegate' or manager_json.get('subtasks'):
                    print("\n[Orchestrator] Meneruskan tugas pembuatan kode ke CODER...")
                    coder = agents['coder']
                    coder_res = call_ai(coder['prompt'], f"Berdasarkan goal: {user_input}, tuliskan kode lengkapnya dan bungkus dalam format ```lang:filename.ext ... ```", model, api_key, provider)
                    print(f"\nCODER:\n{coder_res}\n")
                    extract_and_save_files(coder_res)
                else:
                    # No delegation, just show manager's text
                    pass
        except json.JSONDecodeError:
            # Plain text fallback, parse manually for "DELEGATE:" token
            if "DELEGATE:coder" in response or "coder" in response.lower():
                print("\n[Orchestrator] Meneruskan tugas pembuatan kode ke CODER...")
                coder = agents['coder']
                coder_res = call_ai(coder['prompt'], f"Berdasarkan goal: {user_input}, tuliskan kode lengkapnya dan bungkus dalam format ```lang:filename.ext ... ```", model, api_key, provider)
                print(f"\nCODER:\n{coder_res}\n")
                extract_and_save_files(coder_res)
            else:
                pass  # Plain text output

if __name__ == '__main__':
    main()
