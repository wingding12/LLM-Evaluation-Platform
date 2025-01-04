from fastapi import FastAPI

app = FastAPI()

from . import api  # This will register all routes
