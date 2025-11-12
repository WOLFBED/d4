import json, os, subprocess, sys

def load_reqs():
    with open("external_requirements.json") as f:
        return json.load(f)

def get_distro():
    if os.path.exists("/etc/arch-release"):
        return "arch"
    elif os.path.exists("/etc/debian_version"):
        return "debian"
    elif os.path.exists("/etc/redhat-release"):
        return "redhat"
    else:
        sys.exit("Unsupported distro")

def check_installed(pkg):
    return subprocess.call(["which", pkg], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) == 0

def check_system_reqs():
    distro = get_distro()
    reqs = load_reqs()[distro]
    missing = [p for p in reqs if not check_installed(p)]
    if missing:
        print("Missing packages:", ", ".join(missing))
        sys.exit(1)
    else:
        print("All external dependencies are present.")

def install_system_reqs():
    distro = get_distro()
    reqs = load_reqs()[distro]
    if distro == "arch":
        subprocess.run(["sudo", "pacman", "-S", "--needed", *reqs])
    elif distro == "debian":
        subprocess.run(["sudo", "apt", "install", "-y", *reqs])
    elif distro == "redhat":
        subprocess.run(["sudo", "dnf", "install", "-y", *reqs])
    print("System packages installed.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: setup_env.py [check_system_reqs|install_system_reqs]")
        sys.exit(1)
    globals()[sys.argv[1]]()
