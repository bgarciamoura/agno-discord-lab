import os

import requests
from dotenv import load_dotenv

load_dotenv()  # lê o .env da raiz do projeto (execute a partir da raiz)

API_KEY = os.getenv("TRELLO_API_KEY")
TOKEN = os.getenv("TRELLO_TOKEN")


url = "https://api.trello.com/1/members/me/boards"

params = {"key": API_KEY, "token": TOKEN}

response = requests.get(url, params=params)
response.raise_for_status()

boards = response.json()

for board in boards:
    print(board["name"], "->", board["id"])
