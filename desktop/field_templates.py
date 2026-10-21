"""Editable starting points for every field the user has to fill in.

Nothing here is a rule: each value is dropped into the input box by the
"示例" button so the user can edit it instead of staring at an empty field.
"""

PERSON_SAMPLES = {
    "nickname": "小满",
    "gender": "女",
    "birth_year": "1998",
    "city": "杭州",
    "job": "产品经理",
    "hobbies": "爬山、看展、撸猫",
    "relationship": "单身",
    "notes": "话不多，喜欢先听；不太用书面语，偶尔发语音。",
}

QUIET_PRESETS = ["03:00-05:30", "23:30-07:30", "22:00-08:00", "00:00-00:00"]
CAP_PRESETS = ["10", "30", "50", "100"]

NAME_SAMPLES = {
    "wechat": "微信主号",
    "xhs": "小红书通道",
    "soul": "Soul 通道",
    "mock": "试运行通道",
}


def name_sample(channel: str) -> str:
    return NAME_SAMPLES.get(channel, "微信通道")


def person_sample(key: str) -> str:
    return PERSON_SAMPLES.get(key, "")
