import os
import bcrypt
import jwt
import datetime

from dotenv import load_dotenv
from twilio.rest import Client
from typing import Optional
from pydantic import BaseModel

from fastapi import FastAPI, Form, HTTPException, Depends, Cookie, Body, Request
from fastapi.responses import HTMLResponse, RedirectResponse

load_dotenv()

app = FastAPI()

account_sid = os.environ.get("ACCOUNT_SID")
api_key = os.environ.get("API_KEY")
api_secret = os.environ.get("API_SECRET")
jwt_secret = os.environ.get("JWT_SECRET")
jwt_expires_in_s = int(os.environ.get("JWT_EXPIRES_IN_S"))
password_hashed = os.environ.get("PASSWORD_HASHED").encode()

client = Client(api_key, api_secret, account_sid)


def verify_password(password_plain, password_hashed):
    return bcrypt.checkpw(password_plain, password_hashed)


def create_access_token():
    payload = {
        "exp": datetime.datetime.now(tz=datetime.timezone.utc)
        + datetime.timedelta(seconds=jwt_expires_in_s)
    }
    return jwt.encode(payload, jwt_secret, algorithm="HS256")


def decode_access_token(encoded):
    try:
        return jwt.decode(encoded, jwt_secret, algorithms=["HS256"])
    except:
        raise HTTPException(
            status_code=302, detail="can't decode token", headers={"Location": "/login"}
        )


def get_decoded_token(request: Request):
    access_token = request.cookies.get("access_token")
    if not access_token:
        raise HTTPException(
            status_code=302, detail="no cookie", headers={"Location": "/login"}
        )

    decoded_token = decode_access_token(access_token)

    return decoded_token


@app.head("/health")
async def head_health():
    return {"message": "ok"}


@app.get("/health")
async def health():
    return {"message": "ok"}


@app.get("/login")
async def login_main():
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha3/dist/css/bootstrap.min.css" rel="stylesheet" integrity="sha384-KK94CHFLLe+nY2dmCWGMq91rCGa5gtU4mk92HdvYe+M/SXH301p5ILy+dN9+nJOZ" crossorigin="anonymous">
    </head>
    <body>
        <div class="table-responsive p-3">
            <h1>Login</h1>
            <form action="/login" method="post">
                <div class="form-group mb-3">
                   <label for="password">Password:</label>
                   <input type="password" class="form-control" id="password" name="password" required>
                </div>
                <button type="submit" class="btn btn-primary">Login</button>
            </form>
        </div>
    </body>
    """

    return HTMLResponse(content=html_content)


@app.post("/login")
async def login(password: str = Form(...)):
    password = password.encode()
    if not verify_password(password, password_hashed):
        raise HTTPException(
            status_code=302, detail="password no good", headers={"Location": "/login"}
        )

    access_token = create_access_token()

    response = RedirectResponse(url="/messages", status_code=302)
    response.set_cookie(key="access_token", value=access_token)
    return response


@app.post("/message")
async def message_send(
    from_: str = Form(...),
    to: str = Form(...),
    body: str = Form(...),
    decoded_token: str = Depends(get_decoded_token),
):
    client.messages.create(from_=from_, to=to, body=body)
    return RedirectResponse(url="/messages", status_code=303)


@app.get("/messages-json")
async def messages_json(decoded_token: str = Depends(get_decoded_token)):
    messages = client.messages.list()
    if len(messages) == 0:
        return {"message": "No messages"}

    out = []
    for sms in client.messages.list():
        out_i = {}
        out_i["from_"] = sms.from_
        out_i["to"] = sms.to
        out_i["num_media"] = sms.num_media
        out_i["body"] = sms.body
        out.append(out_i)

    return {"message": out}


@app.get("/messages")
async def messages(decoded_token: str = Depends(get_decoded_token)):
    messages = client.messages.list()
    exp = decoded_token['exp']
    now = datetime.datetime.now(tz=datetime.timezone.utc).timestamp()
    expires_in = exp - now
    expires_in_h = int(expires_in/3600)
    expires_in_m = int(expires_in%3600/60)
    expires_in_s = int(expires_in%60)

    body = ""
    for sms in client.messages.list():
        body += "<tr>"
        body += f"<td>{sms.from_}</td>"
        body += f"<td>{sms.to}</td>"
        body += f"<td>{sms.date_sent}</td>"
        body += f"<td>{sms.body}</td>"
        body += f"<td>{sms.num_media}</td>"
        body += "</tr>"

    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha3/dist/css/bootstrap.min.css" rel="stylesheet" integrity="sha384-KK94CHFLLe+nY2dmCWGMq91rCGa5gtU4mk92HdvYe+M/SXH301p5ILy+dN9+nJOZ" crossorigin="anonymous">
    </head>
    <body>
        <div class="table-responsive p-3">
            <h3>Login expires in 
    """
    html_content += f"{expires_in_h}h {expires_in_m}m {expires_in_s}s"
    html_content += """
             </h3>
        </div>
        <div class="table-responsive p-3">
            <h3>Send message</h3>
            <form id="message_send_form" action="/message" method="post">
                <div class="row">
                    <div class="col-md-6 mb-3">
                       <label for="from_">From:</label>
                       <input type="text" class="form-control" id="from_" name="from_" required>
                    </div>
                    <div class="col-md-6 mb-3">
                       <label for="to">To:</label>
                       <input type="text" class="form-control" id="to" name="to" required>
                    </div>
                </div>
                <div class="row">
                    <div class="col-md-12 mb-3">
                       <label for="body">Body:</label>
                       <input type="text" class="form-control" id="body" name="body" required>
                    </div>
                </div>
                <button type="submit" class="btn btn-primary">Send</button>
            </form>
        </div>
        <div class="table-responsive p-3">
            <table id="messages_table" class="table">
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
    """
    html_content += body
    html_content += """
                </tbody>
            </table>
        </div>
        <script>
            document.addEventListener("DOMContentLoaded", function() {
                var table = document.getElementById("messages_table");
                var form = document.getElementById("message_send_form");
                table.addEventListener("click", function(event) {
                    var row = event.target.parentElement;
                    var cells = row.getElementsByTagName("td");
                    var from_ = cells[0].innerText;
                    var to = cells[1].innerText;

                    form.from_.value = to;
                    form.to.value = from_;
                });
            });
        </script>
    </body>
    """

    return HTMLResponse(content=html_content)
