from pydantic import AliasChoices, BaseModel, Field


class UserProfilePayload(BaseModel):
    nickname: str = Field(default="", max_length=40)
    gender: str = Field(default="", max_length=20)
    birth_year: str = Field(default="", max_length=20)
    city: str = Field(default="", max_length=40)
    # 籍贯/老家、当前所在地（手机/浏览器定位写入）、工作地址。放在 city 之后，
    # 让三端表单顺序一致：现居城市 → 老家 → 当前所在地 → 工作地址。
    hometown: str = Field(default="", max_length=40)
    current_location: str = Field(default="", max_length=80)
    work_address: str = Field(default="", max_length=120)
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
    # The user's own WeChat id, so the assistant can hand it over when the
    # counterpart asks for a contact (only once the user opts in below).
    wechat_id: str = Field(default="", max_length=60)
    # Words that mean "WeChat" on censoring platforms ("V", "绿泡泡", ...).
    # Recognition only; comma separated so one text box serves every client.
    wechat_aliases: str = Field(default="", max_length=200)
    # The word a reply may use instead of 微信 when it hands the id over.
    wechat_display_alias: str = Field(default="微信", max_length=20)
    # Explicit opt-in for the desktop bridge sending drafts unchanged.
    auto_send_authorized: bool = False
    # Opt-in for handing out `wechat_id` inside a reply. None keeps the stored
    # choice (the PC form omits it), same rule as strategic_plan_enabled.
    contact_handoff_enabled: bool | None = None
    # The planner stage ("marshal") that reads the situation before wording.
    # None means "leave the stored setting alone": the PC client saves the
    # profile without this field and must not flip a choice made on the web.
    strategic_plan_enabled: bool | None = None


class UserProfileResponse(UserProfilePayload):
    updated_at: str = ""
