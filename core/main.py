from contextlib import asynccontextmanager

from fastapi import FastAPI

from core.api.routes import questions, reviewers
from core.db.session import DEFAULT_DB_PATH, create_db_engine, ensure_schema
from core.services.nlp import get_analyzer, get_sentencizer


@asynccontextmanager
async def lifespan(app: FastAPI):
    get_analyzer()
    get_sentencizer()
    engine = create_db_engine(DEFAULT_DB_PATH)
    ensure_schema(engine)
    engine.dispose()
    yield


app = FastAPI(lifespan=lifespan)

app.include_router(reviewers.router)
app.include_router(questions.router)
