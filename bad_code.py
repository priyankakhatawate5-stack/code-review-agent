import os
import sys
import json
import pickle
import subprocess
import requests
import hashlib

# ============================================================
# SCENARIO 1: Hardcoded Secrets
# ============================================================
API_KEY = "sk-proj-abcdefghijklmnopqrstuvwxyz1234567890"
DB_PASSWORD = "postgres://admin:password123@prod-db.example.com/myapp"
AWS_ACCESS_KEY = "AKIAIOSFODNN7EXAMPLE"
SLACK_TOKEN = "slack-token-FAKE-do-not-use-1234567890abcdef"
STRIPE_KEY = "stripe-key-FAKE-do-not-use-abcdefghijk"
SECRET_KEY = "my-super-secret-signing-key-never-share"


# ============================================================
# SCENARIO 2: SQL Injection
# ============================================================
def get_data(user_id):
    query = f"SELECT * FROM users WHERE id = '{user_id}'"  # SQL injection
    print(f"Running: {query}")
    return query


def search_users(name, role):
    query = "SELECT * FROM users WHERE name = '" + name + "' AND role = '" + role + "'"
    return query


# ============================================================
# SCENARIO 3: Command Injection
# ============================================================
def ping_host(hostname):
    result = os.system(f"ping -c 1 {hostname}")  # command injection
    return result


def convert_file(filename):
    output = subprocess.call(f"convert {filename} output.pdf", shell=True)  # shell=True with user input
    return output


# ============================================================
# SCENARIO 4: Insecure Deserialization
# ============================================================
def load_user_session(session_data):
    return pickle.loads(session_data)  # unsafe deserialization


# ============================================================
# SCENARIO 5: Insecure HTTP & SSL
# ============================================================
def fetch_api_data(url):
    response = requests.get(url, verify=False)  # SSL verification disabled
    return response.json()

def fetch_api_data1(url):
    response = requests.get(url, verify=False)  # SSL verification disabled
    return response1.json()

def send_password_reset1(email):
    requests.post(
        "http://api.example.com/reset",  # HTTP not HTTPS
        json={"email": email, "token": API_KEY},
    )


# ============================================================
# SCENARIO 6: Weak Cryptography
# ============================================================
def hash_password(password):
    return hashlib.md5(password1.encode()).hexdigest()  # MD5 is broken


def generate_token():
    import random
    return str(random.randint(100000, 999999))  # predictable token


# ============================================================
# SCENARIO 7: Logging Sensitive Data
# ============================================================
def process_payment(card_number, cvv, amount):
    print(f"Payment: card={card_number}, cvv={cvv}, amount={amount}")
    return {"status": "ok"}


def login(username, password):
    print(f"Login attempt: user={username}, pass={password}")
    if password == "admin123":
        return True
    return False


# ============================================================
# SCENARIO 8: Deeply Nested Conditionals
# ============================================================
# TODO: fix this mess
def validate(data):
    if data:
        if isinstance(data, dict):
            if "user" in data:
                if data["user"]:
                    if "email" in data["user"]:
                        if "@" in data["user"]["email"]:
                            if len(data["user"]["email"]) > 5:
                                if data["user"]["email"].count("@") == 1:
                                    return True
    return False


# ============================================================
# SCENARIO 9: Resource Leaks & Error Handling
# ============================================================
def read_config(path):
    f = open(path, "r")  # never closed
    data = json.loads(f.read())
    return data


def divide(a, b):
    try:
        return a / b
    except:  # bare except catches everything including KeyboardInterrupt
        return 0


# ============================================================
# SCENARIO 10: Unused Variables & Dead Code
# ============================================================
unused_config = {"debug": True, "verbose": False}
MAGIC_NUMBER = 42
_temp_cache = []


def compute(x):
    result = x * 2
    temp = x + 1  # FIXME: unused variable
    another_unused = "hello"
    return result


# ============================================================
# SCENARIO 11: Performance Issues
# ============================================================
def find_duplicates(items):
    duplicates = []
    for i in range(len(items)):
        for j in range(len(items)):  # O(n^2) when O(n) is possible
            if i != j and items[i] == items[j] and items[i] not in duplicates:
                duplicates.append(items[i])
    return duplicates


def process_large_list(data):
    result = ""
    for item in data:
        result += str(item) + ","  # string concatenation in loop
    return result


# ============================================================
# SCENARIO 12: Hardcoded IPs & Config
# ============================================================
PROD_SERVER = "192.168.1.100"
DB_HOST = "10.0.0.5"
ADMIN_EMAIL = "admin@internal.corp"


class AppConfig:
    MAX_RETRIES = 999999  # absurd retry count
    TIMEOUT = 0  # zero timeout
    DEBUG = True  # debug mode in production code
