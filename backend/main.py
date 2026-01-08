from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from services.search_service import search_clinic
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.get("/search")
def search(query: str):
    """
    Search for a clinic by name.
    """
    result = search_clinic(query)
    return result
