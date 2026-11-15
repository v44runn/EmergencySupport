
from pydantic import BaseModel, Field
from typing import Optional


class EmergencyRequest(BaseModel):
    resource_type: Optional[str] = Field(
        default=None,
        description="Type of supply requested, such as water, food, or blankets"
    )

    quantity: Optional[int] = Field(
        default=None,
        ge=1,
        description="Number of items requested"
    )

    unit: Optional[str] = Field(
        default=None,
        description="Unit, such as bottles, cases, or boxes"
    )

    location_text: Optional[str] = Field(
        default=None,
        description="Delivery location mentioned in the message"
    )

    deadline: Optional[str] = Field(
        default=None,
        description="Requested deadline, if stated, in HH:MM format"
    )

    urgency: Optional[str] = Field(
        default=None,
        description="Urgency indicated in the message: low, medium, or high"
    )

    needs_review: bool = Field(
        default=True,
        description="Whether a human must review the extracted information"
    )
