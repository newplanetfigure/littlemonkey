import os
from twilio.rest import Client
from typing import Optional
from fastapi import FastAPI
from fastapi import Form
from fastapi.responses import HTMLResponse
from fastapi.responses import RedirectResponse

app = FastAPI()

account_sid = os.environ.get("ACCOUNT_SID")
api_key = os.environ.get("API_KEY")
api_secret = os.environ.get("API_SECRET")

client = Client(api_key, api_secret, account_sid)

@app.get("/health")
async def health():
    return {"message": "ok"}

@app.post('/message')
async def message_send(from_: str = Form(...), to: str = Form(...), body: str = Form(...)):
    client.messages.create(
        from_=from_,
        to=to,
        body=body
    )
    return RedirectResponse(url='/messages', status_code=303)
    

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

@app.get("/messages")
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

    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha3/dist/css/bootstrap.min.css" rel="stylesheet" integrity="sha384-KK94CHFLLe+nY2dmCWGMq91rCGa5gtU4mk92HdvYe+M/SXH301p5ILy+dN9+nJOZ" crossorigin="anonymous">
    </head>
    <body>
        <div class="table-responsive p-3">
            <h1>Send message</h1>
            <form id="message_send_form" action="/message" method="post">
                <div class="form-group">
                   <label for="from_">From:</label>
                   <input type="text" class="form-control" id="from_" name="from_" required>
                </div>
                <div class="form-group">
                   <label for="to">To:</label>
                   <input type="text" class="form-control" id="to" name="to" required>
                </div>
                <div class="form-group">
                   <label for="body">Body:</label>
                   <input type="text" class="form-control" id="body" name="body" required>
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

