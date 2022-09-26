import os
import traceback
import httpx
from markdown import markdown as md

template = """<!DOCTYPE html>
<html>
<body>{body}</body>
</html>"""

def _wrap(msg):
    return template.replace("{body}", msg)

_sender = ""
_recipients: list[str] = []
_api_key = ""
_domain = ""
def init(sender, recipients, api_key, domain):
    global _sender, _recipients, _api_key, _domain
    _sender = sender
    _recipients = recipients
    _api_key = api_key
    _domain = domain

def send(msg: str, title: str):
    httpx.post(
        f"https://api.mailgun.net/v3/{_domain}/messages",
        auth=("api", _api_key),
        data={"from": _sender+'@'+_domain,
              "to": _recipients,
              "subject": title,
              "html": msg})

def on_success(before: str, after: str, deleted: int, config):
    with open(os.path.join(config.logging.path, "error.log"), "r") as f:
        error_log = f.read()

    msg = """
# Successfully Updated Library

### Library Info:

#### Before:  
```
{before}
```

#### After:  
```
{after}
```

**{deleted}**

### Error Log:

```
{error_log}
```
""".replace("{error_log}", error_log).replace(
    "{before}", before).replace("{after}", after).replace("{deleted}", 
    f"Encountered {deleted} deleted work{'s' * (deleted>1)}.")

    send(_wrap(md(msg, extensions=['fenced_code'])), "YAPC: Success")

def on_failure(exc_type, exc_value, exc_tb, config):
    with open(os.path.join(config.logging.path, "error.log"), "r") as f:
        error_log = f.read()
    msg = """
# Failed To Update Library

**Exception Type**: `{exc_type}`

**Exception Value**: `{exc_value}`

### Most Recent Traceback:

```
{traceback}
```

### Error Log:

```
{error_log}
```
 """.replace("{error_log}", error_log
    ).replace("{traceback}", '\n'.join(traceback.format_tb(exc_tb))
    ).replace("{exc_value}", str(exc_value)
    ).replace("{exc_type}", exc_type.__name__)

    send(_wrap(md(msg, extensions=['fenced_code'])), "YAPC: Failure")
