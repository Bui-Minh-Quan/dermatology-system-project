from typing import List 
from pydantic import BaseModel, Field, field_validator

class DiagnosisInput(BaseModel):

    symptoms: str = ""

    body_vector: List[float] = Field(
        default_factory=lambda: [0.0] * 8,
        min_length=8,
        max_length=8
    )

    @field_validator("body_vector")
    @classmethod
    def validate_body_vector(cls, value):

        if len(value) != 8:
            raise ValueError(
                "body_vector must contain exactly 8 values"
            )

        return [float(x) for x in value]