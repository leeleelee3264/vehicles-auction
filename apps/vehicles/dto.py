from dataclasses import dataclass
from datetime import date
from typing import List
from django.core.files.uploadedfile import UploadedFile


@dataclass(frozen=True)
class VehicleCreateDTO:
    model_id: int
    year: int
    first_registration_date: date
    color: str
    fuel_type: str
    transmission: str
    mileage: int
    region: str
    images: List[UploadedFile]


