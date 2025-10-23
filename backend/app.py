from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import pandas as pd
import tempfile
from pathlib import Path

from liftplan import get_num_shafts, load_sections, load_tieup, load_treadling, generate_lift_plan, draw_liftplan_pdf  # your existing module

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
    sections: UploadFile = File(...),
    treadling: UploadFile = File(...),
):
    tieup_df = load_tieup(tieup.file)
    sections_df = load_sections(sections.file)
    treadling_df = load_treadling(sections_df, treadling.file)
    num_shafts = get_num_shafts(tieup_df)
    lift_plan_df = generate_lift_plan(tieup_df, treadling_df, num_shafts)

    tmpdir = Path(tempfile.gettempdir())
    pdf_path = tmpdir / "liftplan.pdf"
    draw_liftplan_pdf(lift_plan_df, pdf_path)

    return FileResponse(pdf_path, filename="liftplan.pdf", media_type="application/pdf")
