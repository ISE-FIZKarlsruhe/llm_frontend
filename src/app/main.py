import httpx, logging, os
from fastapi.responses import (
    HTMLResponse,
    JSONResponse,
    RedirectResponse,
    Response,
    PlainTextResponse,
)
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.exception_handlers import http_exception_handler
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi import Depends, FastAPI, Request, HTTPException, File, UploadFile
from .config import SOURCE_HOST, SOURCE_SCHEME, DEBUG

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


logging.debug("Starting Meta-Llama-3-70B-Instruct.Q4_0.llamafile")
os.popen("/models/Meta-Llama-3-70B-Instruct.Q4_0.llamafile  --nobrowser -ngl 9999")

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


@app.api_route(
    "/v1/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"]
)
async def proxy(request: Request, path: str):
    url = f"{SOURCE_SCHEME}://{SOURCE_HOST}/v1/{path}"
    client = httpx.AsyncClient()

    hdrs = [h for h in request.headers.raw if h[0] != b"host"]
    hdrs.append(("host", SOURCE_HOST))

    logging.debug(f"Requesting {url} with headers {hdrs}")
    response = await client.request(
        method=request.method,
        url=url,
        headers=hdrs,
        content=await request.body(),
        timeout=340,
    )

    # Create a response
    return Response(
        content=response.content,
        status_code=response.status_code,
        headers=dict(response.headers),
    )
