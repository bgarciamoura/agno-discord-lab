import os

import requests
from dotenv import load_dotenv

load_dotenv()  # lê o .env da raiz do projeto (execute a partir da raiz)

API_KEY = os.getenv("TRELLO_API_KEY")
TOKEN = os.getenv("TRELLO_TOKEN")
BOARD_ID = os.getenv("TRELLO_BOARD_ID")


url = f"https://api.trello.com/1/boards/{BOARD_ID}/lists"

params = {"key": API_KEY, "token": TOKEN}

response = requests.get(url, params=params)
response.raise_for_status()

lists = response.json()

for item in lists:
    print(item["name"], "->", item["id"])
