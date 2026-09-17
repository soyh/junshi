from pydantic import BaseModel, Field, SecretStr


class AuthRegisterRequest(BaseModel):
    username: str = Field(
        min_length=3,
        max_length=64,
        pattern=r"^[A-Za-z0-9._-]+$",
    )
    password: SecretStr = Field(min_length=12, max_length=256)


class AuthLoginRequest(BaseModel):
    username: str = Field(
        min_length=3,
        max_length=64,
        pattern=r"^[A-Za-z0-9._-]+$",
    )
    password: SecretStr = Field(min_length=1, max_length=256)
