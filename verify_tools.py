import sys
import os

# Ensure the agent_hub directory is in the path
sys.path.insert(0, 'C:/Users/SOPIAN/agent_hub')

print("Verifying tools...")

try:
    import faster_whisper
    print("faster_whisper: IMPORT OK")
except ImportError as e:
    print(f"faster_whisper: IMPORT FAILED - {e}")

try:
    import scrapling
    print("scrapling: IMPORT OK")
except ImportError as e:
    print(f"scrapling: IMPORT FAILED - {e}")

# Try to load the modules
try:
    import tools_transcribe
    print("tools_transcribe: LOAD OK")
except Exception as e:
    print(f"tools_transcribe: LOAD FAILED - {e}")

try:
    import tools_scrape
    print("tools_scrape: LOAD OK")
except Exception as e:
    print(f"tools_scrape: LOAD FAILED - {e}")
