from pydantic import BaseModel,Field,ConfigDict
from fastapi import File
from typing import Any, Optional

class CsvUploadResponse(BaseModel):
    message : str

class GetCsvAnalyseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)  # allows .from_orm() / model_validate(orm_obj)

    parsed_data: dict[str, Any] | list[Any]
    data_category: Optional[str] = None

    summary: Optional[str] = None
    health_score: Optional[int] = None
    health_score_reason: Optional[str] = None

    growth_areas: Optional[list[Any] | dict[str, Any]] = None
    problem_areas: Optional[list[Any] | dict[str, Any]] = None
    recommendations: Optional[list[Any] | dict[str, Any]] = None
    metric_changes: Optional[list[Any] | dict[str, Any]] = None
