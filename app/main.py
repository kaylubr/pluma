from fastapi import FastAPI, UploadFile, File
from typing import List
from services.extractors import extract_text

app = FastAPI()

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