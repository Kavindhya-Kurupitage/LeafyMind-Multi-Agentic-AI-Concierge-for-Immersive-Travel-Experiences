"""GuestProfile schema — structured preferences extracted during profiling."""



import re

from typing import Any, Literal



from pydantic import BaseModel, Field, field_validator



TravelStyle = Literal[

    "relaxation", "adventure", "nature", "romance", "wellness", "culture", "luxury", "budget"

]

GroupType = Literal["solo", "couple", "family", "group"]

BudgetTier = Literal["budget", "mid_range", "luxury"]

FitnessLevel = Literal["low", "moderate", "high"]

ContactPreference = Literal["email", "whatsapp", "both"]



REQUIRED_PROFILE_FIELDS = (

    "travel_style",

    "group_type",

    "budget_tier",

    "dietary_restrictions",

    "duration_nights",

)



# Optional contact fields — never required for profile completion.

OPTIONAL_CONTACT_FIELDS = ("email", "whatsapp_number", "contact_preference")



EMAIL_PATTERN = re.compile(

    r"^[a-zA-Z0-9](?:[a-zA-Z0-9._%+-]*[a-zA-Z0-9])?@"

    r"[a-zA-Z0-9](?:[a-zA-Z0-9.-]*[a-zA-Z0-9])?\.[a-zA-Z]{2,}$"

)



CONTACT_PREFERENCES = frozenset({"email", "whatsapp", "both"})



SKIP_CONTACT_PHRASES = frozenset({

    "skip",

    "no",

    "none",

    "later",

    "pass",

    "n/a",

    "na",

    "no thanks",

    "not now",

    "prefer not",

    "don't have",

    "do not have",

})





def _is_skip_value(value: Any) -> bool:

    if value is None:

        return False

    text = str(value).strip().lower()

    if not text:

        return True

    return text in SKIP_CONTACT_PHRASES or text.startswith("no ")





def normalize_email(value: Any) -> str | None:

    """Return a lowercased email if valid; otherwise None (invalid or skipped)."""

    if _is_skip_value(value):

        return None

    email = str(value).strip().lower()

    if not email or not EMAIL_PATTERN.match(email):

        return None

    return email





def normalize_whatsapp(value: Any) -> str | None:

    """

    Strip spaces/dashes; require 7–15 digits; store as +{digits} (e.g. +94771234567).

  """

    if _is_skip_value(value):

        return None

    raw = str(value).strip()

    if not raw:

        return None

    cleaned = re.sub(r"[\s\-().]", "", raw)

    if cleaned.startswith("+"):

        digits = cleaned[1:]

    elif cleaned.startswith("00"):

        digits = cleaned[2:]

    else:

        digits = cleaned

    if not digits.isdigit() or not (7 <= len(digits) <= 15):

        return None

    return f"+{digits}"





def normalize_contact_preference(value: Any) -> str | None:

    if _is_skip_value(value):

        return None

    pref = str(value).strip().lower()

    if pref in CONTACT_PREFERENCES:

        return pref

    return None





def infer_contact_preference(

    email: str | None,

    whatsapp_number: str | None,

    explicit: str | None,

) -> str | None:

    """Infer preference when the guest did not state one explicitly."""

    if explicit:

        return explicit

    if email and whatsapp_number:

        return "both"

    if email:

        return "email"

    if whatsapp_number:

        return "whatsapp"

    return None





class GuestProfile(BaseModel):

    """Guest travel preferences built through conversational profiling."""



    travel_style: str | None = None

    group_type: str | None = None

    group_size: int | None = Field(default=None, ge=1, le=20)

    budget_tier: str | None = None

    dietary_restrictions: str | None = None

    arrival_date: str | None = None

    duration_nights: int | None = Field(default=None, ge=1, le=90)

    interests: list[str] = Field(default_factory=list)

    fitness_level: str | None = None

    origin_country: str | None = None

    special_occasions: str | None = None

    email: str | None = None

    whatsapp_number: str | None = None

    contact_preference: str | None = None



    @field_validator("interests", mode="before")

    @classmethod

    def normalise_interests(cls, value: Any) -> list[str]:

        if value is None:

            return []

        if isinstance(value, str):

            return [value] if value.strip() else []

        if isinstance(value, list):

            return [str(v) for v in value if v]

        return []



    @field_validator("email", mode="before")

    @classmethod

    def normalise_email_field(cls, value: Any) -> str | None:

        return normalize_email(value)



    @field_validator("whatsapp_number", mode="before")

    @classmethod

    def normalise_whatsapp_field(cls, value: Any) -> str | None:

        return normalize_whatsapp(value)



    @field_validator("contact_preference", mode="before")

    @classmethod

    def normalise_contact_preference_field(cls, value: Any) -> str | None:

        return normalize_contact_preference(value)



    @classmethod

    def from_dict(cls, data: dict[str, Any] | None) -> "GuestProfile":

        """Build a GuestProfile from a partial session dict (ignores unknown keys)."""

        if not data:

            return cls()

        known = cls.model_fields.keys()

        filtered = {k: v for k, v in data.items() if k in known and not str(k).startswith("_")}

        return cls.model_validate(filtered)



    def merge(self, partial: dict[str, Any]) -> "GuestProfile":

        """Return a new GuestProfile with partial fields overlaid."""

        current = self.model_dump()

        for key, value in partial.items():

            if key in self.model_fields and value is not None and value != "":

                current[key] = value

        return GuestProfile.model_validate(current)



    def is_complete(self) -> bool:

        """True when all required profiling fields are present (contact fields optional)."""

        for field in REQUIRED_PROFILE_FIELDS:

            value = getattr(self, field)

            if value is None or value == "" or value == []:

                return False

        return True



    def to_session_dict(self) -> dict[str, Any]:

        """Serialise for JSONB storage on the session."""

        return self.model_dump(exclude_none=False)


