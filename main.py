from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/save")
async def save_text(req: Request):
    data = await req.json()
    text = data.get("text", "")
    with open("scraped_output.txt", "w", encoding="utf-8") as f:
        f.write(text)
    return {"status": "saved"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)