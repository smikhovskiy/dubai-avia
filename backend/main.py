from datetime import date
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from search import fetch_flights
from scoring import score_flights

load_dotenv()

app = FastAPI(title="Dubai-Moscow Flight Finder")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.get("/search")
async def search(
    date_from: date = Query(..., description="Earliest outbound departure date (YYYY-MM-DD)"),
    date_to: date = Query(..., description="Latest outbound departure date (YYYY-MM-DD)"),
    return_from: date = Query(..., description="Earliest return departure date (YYYY-MM-DD)"),
    return_to: date = Query(..., description="Latest return departure date (YYYY-MM-DD)"),
):
    try:
        flights = await fetch_flights(date_from, date_to, return_from, return_to)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc))

    ranked = score_flights(flights)
    return {"count": len(ranked), "flights": ranked}


@app.get("/health")
def health():
    return {"status": "ok"}
