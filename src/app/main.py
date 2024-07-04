import httpx, logging, os, time, json, sqlite3, random
from typing import Annotated

from fastapi.responses import (
    HTMLResponse,
    Response,
)
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi import FastAPI, Request, Depends
from fastapi_utils.tasks import repeat_every
from .config import (
    SOURCE_HOST,
    SOURCE_SCHEME,
    DEBUG,
    LOG_PATH,
    LOGDB_PATH,
    LLAMA_LOCKFILE_PATH,
)

if DEBUG:
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s %(levelname)-8s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    logging.debug("Debug logging requested from config env DEBUG")
else:
    logging.basicConfig(
        format="%(asctime)s %(levelname)-8s %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )

if not os.path.exists(LOG_PATH):
    try:
        os.makedirs(LOG_PATH)
    except:
        logging.error(
            f"Could not create log directory {LOG_PATH}, or it already exists"
        )


wait = 3 / random.randint(1, 5)
logging.debug(f"Wait for {wait} s")
time.sleep(wait)
if not os.path.exists(LLAMA_LOCKFILE_PATH):
    logging.debug(f"Starting Meta-Llama-3-70B-Instruct.Q4_0.llamafile")
    open(LLAMA_LOCKFILE_PATH, "w").write("LOCKED")
    os.popen("/models/Meta-Llama-3-70B-Instruct.Q4_0.llamafile  --nobrowser -ngl 9999")
else:
    logging.debug(f"{LLAMA_LOCKFILE_PATH} exists, skipping llamafile start")


app = FastAPI(openapi_url="/openapi")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

from .am import *


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def homepage(request: Request):

    response = templates.TemplateResponse(
        "homepage.html",
        {
            "request": request,
        },
    )
    return response


@app.get("/chat", response_class=HTMLResponse, include_in_schema=False)
async def chat(request: Request):
    if not request.user.is_authenticated:
        raise StarletteHTTPException(
            status_code=401,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    response = templates.TemplateResponse(
        "chat.html",
        {
            "request": request,
        },
    )
    return response


def check_authorization_header(request: Request):
    if "Authorization" not in request.headers:
        raise HTTPException(status_code=401, detail="Authorization header missing")

    token = request.headers["Authorization"].replace("Bearer ", "")
    if verify_auth_token(token):
        return request.headers["Authorization"]

    raise HTTPException(status_code=401, detail=f"Invalid token: {token}")


@app.api_route(
    "/v1/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"]
)
async def proxy(
    request: Request, path: str, auth: str = Depends(check_authorization_header)
):
    url = f"{SOURCE_SCHEME}://{SOURCE_HOST}/v1/{path}"
    client = httpx.AsyncClient()

    hdrs = [h for h in request.headers.raw if h[0] != b"host"]
    hdrs.append(("host", SOURCE_HOST))

    logging.debug(f"Requesting {url} with headers {hdrs}")
    request_body = await request.body()
    logging.debug(f"Request body: {request_body.decode('utf8')}")

    response = await client.request(
        method=request.method,
        url=url,
        headers=hdrs,
        content=await request.body(),
        timeout=340,
    )

    log = {
        "auth": auth,
        "timestamp": time.time(),
        "url": url,
        "method": request.method,
        "request_headers": dict(request.headers),
        "request_body": request_body.decode("utf8"),
        "response": response.content.decode("utf8"),
        "status_code": response.status_code,
        "response_headers": dict(response.headers),
    }
    open(os.path.join(LOG_PATH, f"{time.time()}.log"), "w").write(json.dumps(log))

    # Create a response
    return Response(
        content=response.content,
        status_code=response.status_code,
        headers=dict(response.headers),
    )


@app.on_event("startup")
@repeat_every(seconds=60)
def ingest_logs():
    if not LOGDB_PATH:
        logging.error("LOGDB_PATH not set")
        return
    logs = os.listdir(LOG_PATH)
    buf = []
    for log in logs:
        if log.endswith(".log"):
            log_contents = open(os.path.join(LOG_PATH, log)).read()
            buf.append((log.replace(".log", ""), log_contents))
    try:
        DB = sqlite3.connect(LOGDB_PATH)
        DB.executemany("INSERT OR IGNORE INTO logs VALUES (?, ?)", buf)
        DB.commit()
    finally:
        for log in logs:
            os.remove(os.path.join(LOG_PATH, log))
    if len(logs) > 0:
        logging.debug(f"Ingested {len(logs)} logs")
