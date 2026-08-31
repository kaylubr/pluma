from contextlib import asynccontextmanager

from fastapi import FastAPI

from core.api.routes import questions, reviewers, uploads
from core.services.nlp import get_analyzer, get_sentencizer


@asynccontextmanager
async def lifespan(app: FastAPI):
    get_analyzer()
    get_sentencizer()
    yield


app = FastAPI(lifespan=lifespan)

app.include_router(uploads.router)
app.include_router(reviewers.router)
app.include_router(questions.router)
