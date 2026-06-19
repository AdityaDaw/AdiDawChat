import platform
from pathlib import Path
from os import path

def get_chrome_profile_dir():
    home = Path.home()
    system = platform.system()

    if system == "Linux":
        return path.join(home, ".config", "google-chrome", "Default")
    elif system == "Darwin":  # macOS
        return path.join(home, "Library", "Application Support", "Google", "Chrome", "Default")
    elif system == "Windows":
        return path.join(home, "AppData", "Local", "Google", "Chrome", "User Data", "Default")
    else:
        raise OSError(f"Unsupported operating system: {system}")


def get_chrome_cookies_path():
    profile_dir = get_chrome_profile_dir()
    if path.exists(profile_dir):
        return profile_dir
    else:        raise OSError(f"Chrome profile directory does not exist: {profile_dir}")


if __name__ == "__main__":
    try:
        profile_dir = get_chrome_profile_dir()
        print(f"Chrome profile directory: {profile_dir}")
        print(f"Directory exists: {path.exists(profile_dir)}")
        cookies_path = get_chrome_cookies_path()
        print(f"Chrome cookies path: {cookies_path}")
    except OSError as e:
        print(e)