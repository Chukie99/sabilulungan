import os, json, sys

# Jalankan di root direktori
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Top-level resources
API_URL = os.getenv("API_URL", "http://localhost:20128/v1/chat/completions")
MODEL = os.getenv("MODEL", "anthropic/claude-3.5-sonnet")

# List of allowed endpoints (lightweight)
ALLOWED_ENDPOINTS = {
    "api/index.html": True,
    "api/api/chat": True
}

# Function to handle requests (simulasi seperti dashboard.py)
def request_handler(method, endpoint, origin, host, body):
    if method == "GET":
        if endpoint not in ALLOWED_ENDPOINTS:
            return 404, "404 Not Found"
        if endpoint == "api/index.html":
            return 200, "<!html><body>Halo dunia</body></html>"
        return 200, "OK"
    elif method == "POST":
        # Validasi CSRF
        if not (origin == "http://127.0.0.1:5050" and host == "127.0.0.1:5050"):
            return 403, "Forbidden: Cross-Origin Request Blocked"
        if endpoint not in ALLOWED_ENDPOINTS:
            return 404, "404 Not Found"
        # Simulasi panggilan API
        if body.get("reset"):
            return 200, "{\"status\": \"success\", \"message\": \"Memori percakapan di-reset.\"}"
        return 200, "{\"status\": \"success\", \"reply\": \"Halo\", \"agent\": \"manager\"}"
    else:
        return 501, "501 Unsupported method"

# CLI test function
def cli_test():
    print("🧪 Serverless Agent Hub Compliance Test\n")
    
    tests = [
        ("GET /index.html", "GET", "api/index.html", "http://127.0.0.1:5050", "127.0.0.1:5050", {}, 200),
        ("POST /api/chat dengan Origin benar", "POST", "api/api/chat", "http://127.0.0.1:5050", "127.0.0.1:5050", {"message": "tes"}, 200),
        ("POST /api/chat dengan Origin salah", "POST", "api/api/chat", "http://evil-site.com", "127.0.0.1:5050", {"message": "tes"}, 403),
        ("POST /api/chat dengan Host salah", "POST", "api/api/chat", "http://127.0.0.1:5050", "evil-host.com", {"message": "tes"}, 403),
        ("GET method tidak didukung", "HEAD", "api/index.html", "http://127.0.0.1:5050", "127.0.0.1:5050", {}, 501),
        ("Endpoint tidak ditemukan", "GET", "api/unknown", "http://127.0.0.1:5050", "127.0.0.1:5050", {}, 404),
    ]
    
    passed = 0
    total = len(tests)
    
    for name, method, endpoint, origin, host, body, expected_code in tests:
        code, resp = request_handler(method, endpoint, origin, host, body)
        success = (code == expected_code)
        status = "PASS" if success else "FAIL"
        print(f"{status}: {name}")
        print(f"  Metode: {method} {endpoint}")
        print(f"  Origin: {origin} | Host: {host}")
        print(f"  Respon Code: {code} (expected: {expected_code})")
        print(f"  Respon: {resp}\n")
        if success:
            passed += 1
    
    print(f"\n📊 Hasil: {passed}/{total} tes berhasil")
    if passed == total:
        print("✅ Semua tes lolos. Server siap operasi.")
        return True
    else:
        print("❌ Beberapa tes gagal. Harap periksa konfigurasi.")
        return False

if __name__ == "__main__":
    if not cli_test():
        sys.exit(1)
