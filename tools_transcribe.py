import os
from faster_whisper import WhisperModel

# Pakai model 'tiny' atau 'base' supaya kuat di CPU Haswell 4GB RAM
MODEL_SIZE = "tiny"

def transcribe_audio(file_path: str) -> str:
    if not os.path.exists(file_path):
        return f"Error: File {file_path} tidak ditemukan."
    
    print(f"[*] Loading Whisper ({MODEL_SIZE}) on CPU...")
    model = WhisperModel(MODEL_SIZE, device="cpu", compute_type="int8")
    
    print(f"[*] Transcribing {file_path}...")
    segments, info = model.transcribe(file_path, beam_size=5)
    
    text_result = ""
    for segment in segments:
        text_result += f"[{segment.start:.2f}s -> {segment.end:.2f}s] {segment.text}\n"
        
    return text_result

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        print(transcribe_audio(sys.argv[1]))
    else:
        print("Usage: python transcriber.py <path_to_audio>")
