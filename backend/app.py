from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import pandas as pd
import tempfile
from pathlib import Path

from liftplan import generate_lift_plan, draw_liftplan_pdf  # your existing module

app = FastAPI()

# ✅ Allow requests from your frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://lift-plan-converter.vercel.app/"],  # update after frontend deploy
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/generate_liftplan/")
async def generate_liftplan(
    tieup: UploadFile = File(...),
    treadling: UploadFile = File(...),
):
    tieup_df = pd.read_csv(tieup.file)
    treadling_df = pd.read_csv(treadling.file)

    lift_plan_df = generate_lift_plan(tieup_df, treadling_df)

    tmpdir = Path(tempfile.gettempdir())
    pdf_path = tmpdir / "liftplan.pdf"
    draw_liftplan_pdf(lift_plan_df, pdf_path)

    return FileResponse(pdf_path, filename="liftplan.pdf", media_type="application/pdf")
