import os
from dotenv import load_dotenv
from twilio.rest import Client
from typing import Optional
from fastapi import FastAPI

load_dotenv()

app = FastAPI()

account_sid = os.environ.get("ACCOUNT_SID")
api_key = os.environ.get("API_KEY")
api_secret = os.environ.get("API_SECRET")

client = Client(api_key, api_secret, account_sid)

@app.get("/health")
async def health():
    return {"message": "ok"}

@app.get("/messages")
async def root():
    messages = client.messages.list()
    if len(messages) == 0:
        return {"message": "No messages"}

    
    out = ""
    for sms in client.messages.list():
        out += f"{sms.from_} -> {sms.to}, sent on {sms.date_sent}, num_media={sms.num_media}"
        out += f"=====\n{sms.body}\n====="

    return {"message": out}

