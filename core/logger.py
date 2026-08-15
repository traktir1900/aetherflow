
class Logger:
    def info(self, msg): print(f"[INFO] {msg}")
    def success(self, msg): print(f"[SUCCESS] ✓ {msg}")
    def warn(self, msg): print(f"[WARN] ⚠ {msg}")
    def error(self, msg): print(f"[ERROR] ✖ {msg}")
    def profile(self, name, duration): print(f"[PROFILE] {name} took {duration:.3f}s")

log = Logger()
