"""Owner-scoped diagnostics only; never added to a provider request."""
import re
from app.services.reference_retrieval import filename


def check_topics(items):
    aliases = {}
    for item in items:
        for name in (item['name'], item.get('original_filename')):
            if name:
                aliases.setdefault(filename(name), {})[item['id']] = item
    explicit = {i['id'] for i in items if i.get('is_guide') and i['effective_enabled']}
    rows = []
    for guide in items:
        lines = guide.get('content', '').splitlines()
        for number, line in enumerate(lines, 1):
            targets = re.findall(r'`([^`\n]+\.(?:md|markdown|txt|skill|docx))`|\[[^\]]*\]\(([^)]+)\)', line, re.I)
            if not targets:
                if guide.get('is_guide') and re.match(r'^\s*[-*]\s+', line):
                    rows.append({'topic': line.strip(' -*：:' )[:160], 'source_id': guide['id'],
                                 'source_name': guide['name'], 'line': number, 'filename': '',
                                 'file_status': 'unbound', 'topic_active': guide['effective_enabled'],
                                 'effective': False, 'reason': 'no_file_link', 'matches': []})
                continue
            topic = re.split(r'`|\[[^\]]*\]\(', line, maxsplit=1)[0].strip(' -：:;；')[:160]
            source_active = guide['effective_enabled'] and (not explicit or guide['id'] in explicit)
            for code, link in targets:
                target = code or link
                if '://' in target or target.startswith('#'):
                    continue
                matches = list(aliases.get(filename(target.split('#', 1)[0]), {}).values())
                active = [m for m in matches if m['effective_enabled']]
                status = ('missing' if not matches else 'disabled' if not active else
                          'ambiguous' if len(active) > 1 else 'available')
                effective = bool(topic) and source_active and status == 'available'
                reason = ('empty_topic' if not topic else 'guide_disabled' if not guide['effective_enabled']
                          else 'supplementary_source' if not source_active else status)
                rows.append({'topic': topic, 'source_id': guide['id'], 'source_name': guide['name'],
                             'line': number, 'filename': target[:200], 'file_status': status,
                             'topic_active': bool(topic) and source_active, 'effective': effective,
                             'reason': reason,
                             'matches': [{'id': m['id'], 'name': m['name'],
                                          'enabled': m['effective_enabled'],
                                          'global_enabled': m['enabled_by_default'],
                                          'override_enabled': m.get('override_enabled')} for m in matches]})
    return {'scope_note': '可供主题路由和检索使用，不代表本次模型已经选用或采纳。',
            'checked_links': len(rows), 'effective_links': sum(r['effective'] for r in rows), 'rows': rows}
