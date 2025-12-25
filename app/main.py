from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from .routers import ws_detection, token_router, auth_router


app = FastAPI(title="Proctoring Detection API")


# Private Network Access: browsers (Chromium) require a special response header
# when a page served from a less-private network (or insecure context) attempts
# to make requests to a more-private address (eg. loopback 127.0.0.1). The
# browser will include the request header 'Access-Control-Request-Private-Network'
# during preflight; the server must respond with
# 'Access-Control-Allow-Private-Network: true' to allow the request.
#
# We add a tiny middleware that echoes this when appropriate so local dev
# in certain network setups won't be blocked. Note: the browser also requires
# the page to be a secure context (https) for some cases — see the message
# in the browser console. The primary recommended fix is to open the FE at
# http://localhost or https; this header is an additional helper.
from fastapi import Request


@app.middleware("http")
async def _add_private_network_allow(request: Request, call_next):
    # If browser asks for private-network access during CORS preflight,
    # include the header in the response to allow it.
    response = await call_next(request)
    if request.headers.get("access-control-request-private-network"):
        response.headers["Access-Control-Allow-Private-Network"] = "true"
    return response

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*", "access-control-request-private-network"],
)

app.include_router(ws_detection.router)
app.include_router(token_router)
app.include_router(auth_router)


@app.get("/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
# placeholder
