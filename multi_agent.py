import os
import sys
import json
import time
import urllib.request
import urllib.error
import threading

API_URL = "http://localhost:20128/v1/chat/completions"
AGENTS_FILE = "agents.json"
API_KEY = os.environ.get("OPENROUTER_API_KEY", "your-api-key-here")
MODEL_NAME = "anthropic/claude-3.5-sonnet"

# ANSI TrueColor & Modern Palettes
C_RESET = "\033[0m"
C_DIM = "\033[2m"
C_BOLD = "\033[1m"
C_BORDER = "\033[38;5;238m"
C_GREEN = "\033[38;5;48m"
C_CYAN = "\033[38;5;51m"
C_AMBER = "\033[38;5;214m"
C_WHITE = "\033[38;5;255m"
C_PURPLE = "\033[38;5;141m"

AGENT_BADGES = {
    "manager": ("MANAGER ENGINE", "EXECUTION // 0-BS", C_PURPLE),
    "coder": ("CODER ENGINE", "ARCH // ZERO-DEBT", C_CYAN),
    "designer": ("DESIGN ENGINE", "ANTISLOP // MINIMAL", C_GREEN),
    "marketing": ("GROWTH ENGINE", "VIRAL // 0-BUDGET", C_AMBER),
    "seo": ("ORGANIC RADAR", "INDEX // INTENT", C_CYAN),
    "researcher": ("INTEL DETECTIVE", "TRUTH // GROUNDED", C_PURPLE),
}

def load_agents():
    with open(AGENTS_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def render_hud_header(agents_list):
    print(f"{C_BORDER}╭──────────────────────────────────────────────────────────────────────────╮{C_RESET}")
    print(f"{C_BORDER}│{C_RESET}  {C_BOLD}{C_GREEN}● SYSTEM OPERATIONAL{C_RESET}  {C_DIM}│ 9Router: localhost:20128 │ Model: claude-3.5-sonnet{C_RESET}   {C_BORDER}│{C_RESET}")
    print(f"{C_BORDER}├──────────────────────────────────────────────────────────────────────────┤{C_RESET}")
    roles = '  '.join([f"{C_WHITE}{r}{C_RESET}" for r in agents_list[:6]])
    print(f"{C_BORDER}│{C_RESET}  {C_DIM}Squad:{C_RESET} {roles:<67}{C_BORDER}│{C_RESET}")
    print(f"{C_BORDER}╰──────────────────────────────────────────────────────────────────────────╯{C_RESET}")

def render_agent_card(role, agent_data):
    title, tag, color = AGENT_BADGES.get(role, (agent_data['name'].upper(), "SPECIALIST UNIT", C_GREEN))
    print(f"\n{C_BORDER}╭─ {color}{C_BOLD}[ {title} ]{C_RESET}{C_BORDER} ────────────────────────────────────────────────────────╮{C_RESET}")
    print(f"{C_BORDER}│{C_RESET}  {C_GREEN}● ONLINE{C_RESET}  {C_DIM}Subroutine:{C_RESET} {tag:<47} {C_BORDER}│{C_RESET}")
    print(f"{C_BORDER}│{C_RESET}  {C_DIM}Directive:{C_RESET} {agent_data['prompt'][:52]}...  {C_BORDER}│{C_RESET}")
    print(f"{C_BORDER}╰──────────────────────────────────────────────────────────────────────────╯{C_RESET}")
    print(f"{C_DIM}Ketik perintah lu (atau 'exit' untuk kembali ke menu utama)...{C_RESET}\n")

def call_agent(agent_data, prompt):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }
    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": agent_data['prompt']},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7
    }
    req = urllib.request.Request(API_URL, data=json.dumps(payload).encode('utf-8'), headers=headers, method='POST')
    try:
        with urllib.request.urlopen(req) as response:
            res_body = response.read().decode('utf-8')
            return json.loads(res_body)['choices'][0]['message']['content']
    except Exception as e:
        return f"[ERR] Gagal terhubung ke 9Router: {e}"

def stream_text(text):
    for char in text:
        sys.stdout.write(char)
        sys.stdout.flush()
        time.sleep(0.005)
    print()

def main():
    agents = load_agents()
    os.system('cls' if os.name == 'nt' else 'clear')
    render_hud_header(list(agents.keys()))
    
    role = input(f"\n{C_BOLD}Select Unit {C_DIM}(ex: coder, manager, seo){C_RESET}{C_BOLD} > {C_RESET}").strip().lower()
    if role not in agents:
        print(f"{C_AMBER}[!] Unit '{role}' tidak terdaftar di sistem.{C_RESET}")
        return

    agent = agents[role]
    render_agent_card(role, agent)

    while True:
        try:
            user_input = input(f"{C_GREEN}user{C_DIM}@{C_RESET}{C_BOLD}{role}{C_RESET} {C_DIM}> {C_RESET}").strip()
            if not user_input:
                continue
            if user_input.lower() in ['exit', 'quit']:
                print(f"{C_DIM}[Unit {role} standby]{C_RESET}")
                break

            steps = agent.get('work_steps', [
                "Parsing telemetry buffer...",
                "Evaluating context tokens...",
                "Executing synthesis layer..."
            ])

            done = [False]
            def pulse_indicator():
                pulse_frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
                idx = 0
                step_idx = 0
                while not done[0]:
                    frame = pulse_frames[idx % len(pulse_frames)]
                    step_msg = steps[step_idx % len(steps)]
                    sys.stdout.write(f"\r  {C_CYAN}{frame}{C_RESET} {C_DIM}executing:{C_RESET} {C_WHITE}{step_msg:<40}{C_RESET}")
                    sys.stdout.flush()
                    time.sleep(0.12)
                    idx += 1
                    if idx % 8 == 0:
                        step_idx += 1
                sys.stdout.write("\r" + " " * 65 + "\r")

            t = threading.Thread(target=pulse_indicator)
            t.start()

            reply = call_agent(agent, user_input)
            done[0] = True
            t.join()

            print(f"{C_BORDER}╭─ {C_BOLD}{C_WHITE}{agent['name']}{C_RESET} {C_DIM}response{C_RESET} ──────────────────────────────────────╮{C_RESET}")
            stream_text(reply)
            print(f"{C_BORDER}╰──────────────────────────────────────────────────────────────────╯{C_RESET}\n")

        except KeyboardInterrupt:
            print(f"\n{C_DIM}[Session aborted]{C_RESET}")
            break

if __name__ == '__main__':
    main()
