"""Safe diagnostics for memory jobs; never include model output or user data."""
from pydantic import ValidationError
from app.services.llm import LLMRequestError


class MemoryResponseError(ValueError):
    pass


class MemoryProvenanceError(ValueError):
    pass


def diagnose(error):
    if isinstance(error, LLMRequestError):
        code=error.category
        return code, LLMRequestError.MESSAGES[code], code in {'timeout','network','upstream','local_budget','context_limit'}
    if isinstance(error, MemoryProvenanceError):
        return 'evidence', '模型引用了本批聊天以外的依据，结果未采用。', True
    if isinstance(error, MemoryResponseError):
        return 'response_format', '模型未返回可解析的 JSON 档案。', True
    if isinstance(error, ValidationError):
        return 'schema', '模型返回的档案字段或摘要长度未通过校验。', True
    return 'internal', '档案处理或保存失败，请联系维护人员查看错误类别。', False


def correction_hint(error):
    code,_,_=diagnose(error)
    fields=[]
    if isinstance(error, ValidationError):
        allowed={'description','facts','inferences','constraints','unknowns','relationship_status','relationship_stage','reason','evidence_source_ids'}
        fields=sorted({str(e['loc'][0]) for e in error.errors(include_input=False,include_context=False) if e['loc'] and e['loc'][0] in allowed})
    return {'error_code':code,'fields':fields,
            'instruction':'Return the complete JSON schema. Keep the combined summary under 1800 Chinese characters and 8192 UTF-8 bytes. Use exact evidence_source_ids only from messages. Do not invent evidence or discard important prior constraints.'}
