"""Reply-rule templates: usable, editable and specific enough to steer style."""
import reply_rules as rr

assert rr.NAMES, "at least one template"
assert len(rr.NAMES) == len(set(rr.NAMES)), "template names must be unique"
for name, note, text in rr.TEMPLATES:
    assert note, name
    assert 40 <= len(text) <= 1500, (name, len(text))
    assert '不要' in text, f'{name}: a template must state what to avoid'
    assert '长度' in text or '原则' in text, f'{name}: a template must state length or stance'

note, text = rr.template(rr.NAMES[0])
assert text == rr.default_template() and note
assert rr.template('不存在的模板') == ('', '')
print(f'Reply templates {len(rr.NAMES)}: PASS')
