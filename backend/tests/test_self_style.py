from app.services.analysis_strategic_reply import CHAT_EMOJI, build_self_style


def message(sender: str, content: str) -> dict:
    return {"id": f"m-{abs(hash(content)) % 65536}", "sender_type": sender, "content": content}


MIXED = [
    message("person", "今天忙吗"),
    message("user", "忙"),
    message("user", "刚开完会，累死了😮‍💨"),
    message("user", "你吃了吗？"),
    message("person", "吃了"),
    message("user", "哈哈哈好"),
    message("user", "今天下午连着三个会，脑子有点转不动，晚点再聊吧。"),
]
MINE = [item["content"] for item in MIXED if item["sender_type"] == "user"]
LENGTHS = [len(text) for text in MINE]


def test_self_style_is_empty_without_the_user_own_messages():
    assert build_self_style([]) == {}
    assert build_self_style(None) == {}
    assert build_self_style([message("person", "在吗"), message("person", "睡了吗")]) == {}


def test_self_style_measures_length_punctuation_and_emoji():
    style = build_self_style(MIXED)

    assert style["message_count"] == len(MINE) == 5
    assert style["avg_chars"] == round(sum(LENGTHS) / len(LENGTHS), 1)
    assert style["median_chars"] == sorted(LENGTHS)[len(LENGTHS) // 2]
    assert style["short_share"] == round(sum(1 for n in LENGTHS if n <= 15) / len(LENGTHS), 2)
    assert style["question_share"] == round(
        sum(1 for text in MINE if text.rstrip("。.!！~～ ").endswith(("?", "？"))) / len(MINE), 2
    )
    assert style["emoji_share"] == round(
        sum(1 for text in MINE if any(char in text for char in CHAT_EMOJI)) / len(MINE), 2
    )
    assert style["uses_period"] == round(
        sum(1 for text in MINE if text.endswith(("。", "."))) / len(MINE), 2
    )
    assert style["recent_samples"] == MINE


def test_self_style_keeps_a_short_and_a_long_example_apart():
    style = build_self_style(MIXED)
    assert style["short_share"] < 1.0
    assert style["median_chars"] < style["avg_chars"]


def test_self_style_never_replays_the_other_persons_words():
    style = build_self_style(MIXED)
    assert "今天忙吗" not in style["recent_samples"]
    assert all(sample in MINE for sample in style["recent_samples"])


def test_self_style_keeps_only_recent_samples_and_common_openers():
    messages = [message("person", "嗯")] + [message("user", f"好的{i}") for i in range(12)]
    style = build_self_style(messages)

    assert style["message_count"] == 12
    assert len(style["recent_samples"]) == 6
    assert style["recent_samples"][0] == "好的6"
    assert "好的" in style["common_openers"]
