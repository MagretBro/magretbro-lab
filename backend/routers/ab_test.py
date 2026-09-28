from fastapi import APIRouter, File, UploadFile, Form, HTTPException
import pandas as pd

from backend.schemas.ab_test import ABTestResponse
from backend.services.ab_test import analyze_ab_test

router = APIRouter()


@router.post("/api/ab-test/analyze", response_model=ABTestResponse)
async def analyze_ab_test_endpoint(
    file: UploadFile = File(...),
    group_column: str = Form(...),
    metric_column: str = Form(...),
):
    try:
        df = pd.read_csv(file.file)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Ошибка чтения CSV-файла: {str(e)}")

    try:
        result = analyze_ab_test(df, group_column, metric_column)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return result
