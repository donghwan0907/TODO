from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware
from controllers import router


app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="secret-key")
app.include_router(router)