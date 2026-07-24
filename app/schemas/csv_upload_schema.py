from pydantic import BaseModel
from fastapi import File

class CsvUploadResponse(BaseModel):
    message : str