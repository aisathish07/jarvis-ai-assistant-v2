import os, requests
CORE = os.getenv("JARVIS_CORE_URL", "http://127.0.0.1:8000")
BRIDGE = os.getenv("BRIDGE_URL", "http://127.0.0.1:8080")

def check(url):
    try:
        r = requests.get(url + "/health", timeout=3)
        print(url, "->", r.status_code, r.text)
    except Exception as e:
        print(url, "-> ERROR:", e)

if __name__ == "__main__":
    check(CORE)
    check(BRIDGE)
