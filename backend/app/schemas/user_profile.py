from pydantic import AliasChoices, BaseModel, Field


class UserProfilePayload(BaseModel):
    nickname: str = Field(default="", max_length=40)
    gender: str = Field(default="", max_length=20)
    birth_year: str = Field(default="", max_length=20)
    city: str = Field(default="", max_length=40)
    job: str = Field(default="", max_length=40)
    hobbies: str = Field(default="", max_length=120)
    # Older desktop builds send "relationship"; keep accepting it on input while
    # the response keeps the canonical name the web workspace reads.
    relationship_status: str = Field(
        default="",
        max_length=40,
        validation_alias=AliasChoices("relationship_status", "relationship"),
    )
    about: str = Field(default="", max_length=400)
    reply_rules: str = Field(default="", max_length=1500)


class UserProfileResponse(UserProfilePayload):
    updated_at: str = ""
