from pydantic import BaseModel, ConfigDict, Field, SecretStr


class AuthRegisterRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    username: str = Field(
        min_length=3,
        max_length=64,
        pattern=r"^[A-Za-z0-9._-]+$",
    )
    password: SecretStr = Field(min_length=12, max_length=256)


class AuthLoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    username: str = Field(
        min_length=3,
        max_length=64,
        pattern=r"^[A-Za-z0-9._-]+$",
    )
    password: SecretStr = Field(min_length=1, max_length=256)


class AuthPasswordChangeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    current_password: SecretStr = Field(min_length=1, max_length=256)
    new_password: SecretStr = Field(min_length=12, max_length=256)
