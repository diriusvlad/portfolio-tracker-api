from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import auth, portfolios, prices, transactions

app = FastAPI(title="Portfolio Tracker API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(portfolios.router)
app.include_router(transactions.router)
app.include_router(prices.router)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}
