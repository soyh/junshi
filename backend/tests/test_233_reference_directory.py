from app.services.reference_retrieval import retrieve
from app.services.reference_request import prepare_context
from tests.test_200_reference_catalog import item, context
from tests.test_197_reference_skills_context import _upload, OTHER_USER_ID


def test_all_44_documents_are_selectable_without_sending_all_bodies():
    library = [item(str(n), 'PRIVATE_BODY_' + str(n)) for n in range(44)]
    original = context(library)
    assert len(original['model_references']['catalog']) == 44
    seen = []
    def selector(catalog, query):
        seen.extend(catalog)
        return ['43']
    selected = prepare_context(original, selector)['model_references']
    assert len(seen) == 44
    assert all('content' not in row for row in seen)
    assert [row['reference_id'] for row in selected['items']] == ['43']
    assert 'candidates' not in selected
    assert selected['items'][0]['content'] == 'PRIVATE_BODY_43'


def test_explicit_guide_is_distinct_from_incidental_links_and_reports_source():
    guide = item('g', '- 修复：`target.md`', '主题指南.md')
    guide['is_guide'] = True
    result = retrieve([guide, item('s', '方法\n`missing.md`', kind='skill'), item('target', '补救')], '')
    report = result['retrieval']
    assert report['guide_count'] == 1
    assert report['guide_mode'] == 'explicit'
    assert report['warnings'][0]['source_id'] == 's'
    assert report['warnings'][0]['line'] == 2
    assert not next(x for x in result['catalog'] if x['reference_id'] == 's')['is_guide']


def test_guide_setting_and_inventory_are_owned_and_include_disabled(client):
    doc = _upload(client, 'own.md', b'own')
    disabled = _upload(client, 'disabled.md', b'disabled', enabled=False)
    foreign = _upload(client, 'private.md', b'foreign', headers={'X-User-ID': OTHER_USER_ID})
    route = '/api/v1/references/' + doc['id']
    assert client.patch(route, json={'is_guide': True}).json()['is_guide'] is True
    assert client.patch(route, json={'is_guide': False}, headers={'X-User-ID': OTHER_USER_ID}).status_code == 404
    report = client.get('/api/v1/references/catalog').json()['retrieval']
    inventory = {x['reference_id']: x for x in report['inventory']}
    assert inventory[doc['id']]['is_guide']
    assert not inventory[disabled['id']]['enabled']
    assert foreign['id'] not in inventory
    assert client.patch(route, json={'is_guide': False}).json()['is_guide'] is False


def test_diagnostic_inventory_never_expands_model_input():
    original = context([item('a', 'body')])
    original['model_references']['retrieval'].update(inventory=[{'name':'DIAGNOSTIC_ONLY'}], links=[{}], warnings=[{}])
    result = prepare_context(original, lambda *_: ['a'])
    assert not {'inventory','links','warnings','query'} & result['model_references']['retrieval'].keys()
