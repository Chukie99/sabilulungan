import os, sys, json, urllib.request, urllib.error, socket, re
from config import CONFIG, BASE_DIR

AGENTS_FILE = os.path.join(BASE_DIR, "agents.json")

def load_agents():
    with open(AGENTS_FILE, 'r', encoding='utf-8') as f: return json.load(f)

def call_ai(system_prompt, user_prompt, model, api_key, api_url):
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}
    payload = {
        "model": model,
        "messages": [
            {
                "role": "system", 
                "content": system_prompt + "\n**CRITICAL EMITTER:** Output valid JSON only. Field 'delegation_action' can be 'complete' or 'delegate'. If 'delegate', include 'target_agent' and 'instructions'. Do NOT use markdown fences."
            },
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.7
    }
    
    req = urllib.request.Request(api_url, data=json.dumps(payload).encode('utf-8'), headers=headers, method='POST')
    try:
        with urllib.request.urlopen(req, timeout=30) as res:
            response_text = res.read().decode('utf-8')
            try:
                res_json, idx = json.JSONDecoder().raw_decode(response_text)
                return res_json
            except json.JSONDecodeError:
                return {"error": "Invalid JSON response from model", "raw": response_text}
    except (urllib.error.URLError, socket.timeout, Exception) as e:
        return {"error": str(e)}

def extract_and_save_files(text):
    if not isinstance(text, str): return
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
    
    agents = load_agents()
    manager = agents['manager']
    
    api_url = CONFIG["API_URL"]
    api_key = CONFIG["API_KEY"]
    model = CONFIG["MODEL"]
    
    print(f"[INFO] Loaded config -> Model: {model}\n")
    print(f"Manager siap. Ketik goal lu (misal: 'Bikin script Python kalkulator web sederhana').\n")
    
    while True:
        user_input = input("You > ").strip()
        if not user_input: continue
        if user_input.lower() == 'exit': break
        
        print("\n[Manager] Menganalisis...")
        res = call_ai(manager['prompt'], user_input, model, api_key, api_url)
        
        if "error" in res:
            print(f"MANAGER ERROR: {res['error']}")
            continue
            
        print(f"\nMANAGER RESPONSE:\n{json.dumps(res, indent=2)}\n")
        
        # Proper delegation check using strict JSON fields instead of greedy string matching
        if res.get('delegation_action') == 'delegate' and res.get('target_agent'):
            target = res.get('target_agent').lower()
            if target in agents:
                print(f"\n[Orchestrator] Meneruskan ke {target.upper()}...")
                inst = res.get('instructions', user_input)
                agent_res = call_ai(agents[target]['prompt'], inst, model, api_key, api_url)
                
                if "error" in agent_res:
                    print(f"AGENT ERROR: {agent_res['error']}")
                else:
                    print(f"\n{target.upper()} RESPONSE:\n{json.dumps(agent_res, indent=2)}\n")
                    resp_text = agent_res.get('final_response', json.dumps(agent_res))
                    extract_and_save_files(resp_text)
            else:
                print(f"Unknown agent: {target}")

if __name__ == '__main__':
    main()
