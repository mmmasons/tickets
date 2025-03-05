from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers.main import router

app = FastAPI()

origins = [
    "https://api.mmmasons.fund",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

app.include_router(router)
