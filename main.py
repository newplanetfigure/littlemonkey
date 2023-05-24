import os
from twilio.rest import Client
from typing import Optional
from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI()

account_sid = os.environ.get("ACCOUNT_SID")
api_key = os.environ.get("API_KEY")
api_secret = os.environ.get("API_SECRET")

client = Client(api_key, api_secret, account_sid)

@app.get("/health")
async def health():
    return {"message": "ok"}

@app.get("/messages-json")
async def messages_json():
    messages = client.messages.list()
    if len(messages) == 0:
        return {"message": "No messages"}

    
    out = ""
    for sms in client.messages.list():
        out += f"{sms.from_} -> {sms.to}, sent on {sms.date_sent}, num_media={sms.num_media}"
        out += f"=====\n{sms.body}\n====="

    return {"message": out}

@app.get("/messages", response_class=HTMLResponse)
async def messages():
    messages = client.messages.list()

    body = ""
    for sms in client.messages.list():
        body += "<tr>"
        body += f"<td>{sms.from_}</td>"
        body += f"<td>{sms.to}</td>"
        body += f"<td>{sms.date_sent}</td>"
        body += f"<td>{sms.body}</td>"
        body += f"<td>{sms.num_media}</td>"
        body += "</tr>"

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha3/dist/css/bootstrap.min.css" rel="stylesheet" integrity="sha384-KK94CHFLLe+nY2dmCWGMq91rCGa5gtU4mk92HdvYe+M/SXH301p5ILy+dN9+nJOZ" crossorigin="anonymous">
    </head>
    <body>
        <div class="container">
            <table class="table">
                <thead>
                    <tr>
                        <th>From</th>
                        <th>To</th>
                        <th>Date sent</th>
                        <th>Body</th>
                        <th>Num media</th>
                    </tr>
                </thead>
                <tbody>
                {body}
                </tbody>
            </table>
        </div>
    </body>
    """

    return HTMLResponse(content=html_content)

