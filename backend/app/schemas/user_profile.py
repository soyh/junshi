from pydantic import BaseModel, Field


class UserProfilePayload(BaseModel):
    nickname: str = Field(default="", max_length=40)
    gender: str = Field(default="", max_length=20)
    birth_year: str = Field(default="", max_length=20)
    city: str = Field(default="", max_length=40)
    job: str = Field(default="", max_length=40)
    hobbies: str = Field(default="", max_length=120)
    relationship_status: str = Field(default="", max_length=40)
    about: str = Field(default="", max_length=400)
    reply_rules: str = Field(default="", max_length=1500)


class UserProfileResponse(UserProfilePayload):
    updated_at: str = ""
