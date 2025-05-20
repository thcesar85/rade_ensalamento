import os
from dotenv import set_key, load_dotenv

ENV_PATH = ".env"
load_dotenv(ENV_PATH)

def get_db_config():
    return {
        "host": os.getenv("DB_HOST", "localhost"),
        "port": os.getenv("DB_PORT", "5432"),
        "name": os.getenv("DB_NAME", ""),
        "user": os.getenv("DB_USER", ""),
        "password": os.getenv("DB_PASSWORD", "")
    }

def save_db_config(host, port, name, user, password):
    set_key(ENV_PATH, "DB_HOST", host)
    set_key(ENV_PATH, "DB_PORT", port)
    set_key(ENV_PATH, "DB_NAME", name)
    set_key(ENV_PATH, "DB_USER", user)
    set_key(ENV_PATH, "DB_PASSWORD", password)
