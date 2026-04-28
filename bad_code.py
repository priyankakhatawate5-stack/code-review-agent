import os
import sys
import json

API_KEY = "sk-proj-abcdefghijklmnopqrstuvwxyz1234567890"
DB_PASSWORD = "postgres://admin:password123@prod-db.example.com/myapp"

def get_data(user_id):
    query = f"SELECT * FROM users WHERE id = '{user_id}'"  # SQL injection
    print(f"Running: {query}")
    return query

# TODO: fix this mess
def validate(data):
    if data:
        if isinstance(data, dict):
            if "user" in data:
                if data["user"]:
                    if "email" in data["user"]:
                        return True
    return False
