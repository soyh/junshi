"""Resumable import/generation; copying is deliberately not a server action."""
from uuid import uuid4


def new_job(person, conversation, text, media, sent_at):
    return {'person': person, 'conversation': conversation, 'text': text, 'media': media, 'sent_at': sent_at,
            'message_operation': str(uuid4()), 'message_saved': False,
            'media_operations': [str(uuid4()) for _ in media], 'media_ids': {}, 'analyzed': set(),
            'confirm_operation': str(uuid4()), 'confirmed_text': None, 'confirmed': False}


def generate(client, job, progress):
    conversation = job['conversation']
    if job['text'].strip() and not job['message_saved']:
        progress('正在保存对方消息…')
        client.request('POST', '/pc/messages', {'operation_id': job['message_operation'], 'conversation_id': conversation,
                       'sender_type': 'person', 'content': job['text'], 'sent_at': job['sent_at']})
        job['message_saved'] = True
    for index, media in enumerate(job['media']):
        if index not in job['media_ids']:
            progress(f'正在上传附件 {index+1}/{len(job["media"])}…')
            result = client.request('POST', f'/pc/conversations/{conversation}/media',
                                    {'operation_id': job['media_operations'][index], 'sent_at': job['sent_at']}, media=media)
            job['media_ids'][index] = result['id']
        if index not in job['analyzed']:
            progress(f'正在识别附件 {index+1}（图片/视频需配置视觉模型）…')
            client.request('POST', f'/media/{job["media_ids"][index]}/analyze')
            job['analyzed'].add(index)
    progress('记录已保存，正在基于最新聊天生成建议…')
    result = client.request('GET', f'/conversations/{conversation}/strategic-reply/context')
    draft = result.get('draft')
    if not isinstance(draft, str) or not draft.strip():
        raise ValueError('模型没有返回有效建议；记录已保留，可以重试生成')
    # Schedule memory after obtaining the draft so slow profile work never hides it.
    return draft


def confirm_sent(client, job, text, sent_at):
    if job['confirmed']:
        return False
    if job['confirmed_text'] is not None and job['confirmed_text'] != (text, sent_at):
        raise ValueError('上次确认结果不确定，请保持相同文字和时间重试，或先在主页面核对记录')
    job['confirmed_text'] = (text, sent_at)
    client.request('POST', '/pc/messages', {'operation_id': job['confirm_operation'], 'conversation_id': job['conversation'],
                   'sender_type': 'user', 'content': text, 'sent_at': sent_at})
    job['confirmed'] = True
    return True
