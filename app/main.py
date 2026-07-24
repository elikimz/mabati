from fastapi import FastAPI


app = FastAPI(
    title="FastAPI Project",
    version="1.0.0"
)


@app.get("/")
async def root():
    return {
        "message": "API is running"
    }