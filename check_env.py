import importlib.util
import sys

print(f"Python: {sys.executable}")
print(f"Version: {sys.version.split()[0]}")
for name in ("flet", "FunPayAPI", "aiogram", "requests", "httpx", "tonutils"):
    status = "OK" if importlib.util.find_spec(name) else "MISSING"
    print(f"{name}: {status}")
