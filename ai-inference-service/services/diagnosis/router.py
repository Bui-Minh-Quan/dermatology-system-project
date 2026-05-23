from fastapi import (
    APIRouter,
    UploadFile,
    File,
    Form,
    HTTPException
)

from services.diagnosis.schemas import DiagnosisInput

from services.diagnosis.inference import run_diagnosis

router = APIRouter(
    prefix="/diagnosis",
    tags=["Diagnosis"]
)


def parse_body_vector(raw_value: str):

    try:

        cleaned = (
            raw_value
            .replace("[", "")
            .replace("]", "")
            .replace(" ", "")
        )

        values = cleaned.split(",")

        vector = [float(x) for x in values]

        if len(vector) != 8:
            raise ValueError()

        return vector

    except Exception:

        raise HTTPException(
            status_code=400,
            detail=(
                "Invalid body_vector format. "
                "Expected: [1,0,0,0,0,0,0,0]"
            )
        )


@router.post("/infer")
async def infer(
    image: UploadFile = File(...),
    symptoms: str = Form(default=""),
    body_vector: str = Form(default="[0,0,0,0,0,0,0,0]")
):

    validated_input = DiagnosisInput(
        symptoms=symptoms,
        body_vector=parse_body_vector(body_vector)
    )

    result = await run_diagnosis(
        image=image,
        symptoms=validated_input.symptoms,
        body_vector=validated_input.body_vector
    )

    return result