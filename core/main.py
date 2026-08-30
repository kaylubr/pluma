from contextlib import asynccontextmanager
from fastapi import FastAPI, UploadFile, File, HTTPException
from typing import List

from core.services.extractors import extract_text
from core.services.nlp import get_analyzer, get_sentencizer


@asynccontextmanager
def lifespan(app: FastAPI):
    get_analyzer()
    get_sentencizer()
    yield

app = FastAPI(lifespan=lifespan)


@app.post("/upload")
async def upload_files(files: List[UploadFile] = File(...)):
    results = []
    for file in files:
        contents = await file.read()
        try:
            text = extract_text(file.filename, contents)
            results.append({"filename": file.filename, "text": text, "error": None})
        except ValueError as e:
            results.append({"filename": file.filename, "text": None, "error": str(e)})
    return {"results": results}


@app.post("/upload/single")
async def upload_single(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    ext = file.filename.rsplit(".", 1)[-1].lower()
    if ext not in ("pdf", "pptx"):
        raise HTTPException(status_code=400, detail=f"Unsupported file type: .{ext}. Only PDF and PPTX are supported.")

    contents = await file.read()
    try:
        text = extract_text(file.filename, contents)
        return {"filename": file.filename, "text": text, "error": None}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))