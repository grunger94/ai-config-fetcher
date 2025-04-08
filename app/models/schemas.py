from pydantic import BaseModel, Field
from typing import List

class AppEnvExtractionOutput(BaseModel):
    apps: List[str] = Field(..., description="List of application names")
    envs: List[str] = Field(..., description="List of environment names")