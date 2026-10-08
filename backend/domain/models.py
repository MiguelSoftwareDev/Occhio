from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

Percent = Annotated[float, Field(ge=0, le=100, allow_inf_nan=False)]


class Snapshot(BaseModel):
    model_config = ConfigDict(extra="forbid")
    host_name: str = Field(min_length=1, max_length=255, pattern=r"^[\w.\-]+$")
    captured_at: datetime
    cpu_percent: Percent
    memory_percent: Percent
    memory_used_bytes: int = Field(ge=0)
    memory_total_bytes: int = Field(gt=0)
    disk_percent: Percent
    process_count: int = Field(ge=0)
    uptime_seconds: int = Field(ge=0)

    # Valida a memória e o fuso || Validate memory and timezone
    @model_validator(mode="after")
    def validate_snapshot(self):
        if self.memory_used_bytes > self.memory_total_bytes:
            raise ValueError("Memória utilizada excede o total")
        if self.captured_at.tzinfo is None:
            raise ValueError("A coleta deve informar o fuso horário")
        return self


class Analysis(Snapshot):
    analysis_id: UUID
    analyzed_at: datetime
    model: str = Field(min_length=1, max_length=120)
    analysis_text: str = Field(min_length=1, max_length=32000)
    inference_ms: float = Field(ge=0, allow_inf_nan=False)
    prompt_version: str
