"""
One-time setup: writes the already-recovered temp_user credentials to
config/.env for permanent local use, per the approved Phase 7 (only run
after a successful publication or ALREADY_PUBLISHED). Values are read
straight from the existing approved template
(02_SOURCE/db_access_templates/temp_user.py) and never printed.
"""
import importlib.util
import os

ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
ENV_PATH = os.path.join(ROOT, "05_IMPLEMENTATION", "config", ".env")


def load_temp_user_config():
    template_path = os.path.join(ROOT, "02_SOURCE", "db_access_templates", "temp_user.py")
    spec = importlib.util.spec_from_file_location("temp_user_template", template_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.DB_CONFIG


def main():
    cfg = load_temp_user_config()
    lines = [
        f"PGHOST={cfg['host']}\n",
        f"PGPORT={cfg['port']}\n",
        f"PGDATABASE={cfg['dbname']}\n",
        f"PGUSER={cfg['user']}\n",
        f"PGPASSWORD={cfg['password']}\n",
    ]
    with open(ENV_PATH, "w", encoding="utf-8", newline="\n") as f:
        f.writelines(lines)
    print(f"Wrote {ENV_PATH} ({len(lines)} keys). Values not displayed.")


if __name__ == "__main__":
    main()
