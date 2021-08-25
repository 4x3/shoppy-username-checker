import subprocess
import sys
from pathlib import Path


def install_requirements() -> None:
    print("[*] Installing dependencies from requirements.txt...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])


def ensure_file(path: Path, sample: str) -> None:
    if path.exists():
        print(f"[*] {path.name} already exists")
        return
    path.write_text(sample, encoding="utf-8")
    print(f"[+] Created {path.name}")


def finish() -> None:
    print("\n[✓] Setup complete")
    print("Run: python shoppy_checker.py")


if __name__ == "__main__":
    install_requirements()
    ensure_file(Path("usernames.txt"), "@ivory\n@example\n")
    ensure_file(Path("proxies.txt"), "127.0.0.1:8080\n")
    finish()
