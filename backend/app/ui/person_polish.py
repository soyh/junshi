PERSON_POLISH_STYLE = r'''
 html:has(body[data-client-view="people"]),html:has(body[data-client-view="auth"]){background:#0b1522}
 body[data-client-view="people"]{background:radial-gradient(ellipse at 50% 60%,#22455580,transparent 56%),radial-gradient(ellipse at 20% 10%,#30385850,transparent 55%),#0b1522!important}
 body[data-client-view="people"] #client-person-deck{padding:48px 32px 64px}
 body[data-client-view="people"] .client-person-card{animation:none!important;position:relative;isolation:isolate;translate:none;transform:none;transition:transform .32s cubic-bezier(.2,.8,.2,1);z-index:1}
 body[data-client-view="people"] .client-person-card::before,body[data-client-view="people"] .client-person-card::after{content:none!important;display:none!important}
 body[data-client-view="people"] .client-card-front{background:linear-gradient(140deg,#36546599,#132638cc)!important;backdrop-filter:blur(18px);border-color:#416474!important;box-shadow:0 18px 38px #0006,inset 0 1px #b8f5ff22!important;transition:border-color .25s,box-shadow .25s}
 body[data-client-view="people"] .client-person-card.is-selected{transform:none}
 @media(hover:hover) and (pointer:fine){
 body[data-client-view="people"] .client-person-card:not(.is-flipped):hover{transform:translateY(-14px) scale(1.055);z-index:3}
 body[data-client-view="people"] .client-person-card:hover .client-card-front{border-color:#a0f6eb!important;box-shadow:0 28px 48px #0009,0 0 28px #6fe8de38,inset 0 1px #d7fffa66!important}
 }
 body[data-client-view="people"] .client-person-card:has(.client-card-front:focus-visible){transform:translateY(-10px) scale(1.04);z-index:3}
 body[data-client-view="people"] .client-person-card:has(.client-card-front:focus-visible) .client-card-front{border-color:#a0f6eb!important}
 body[data-client-view="people"] .client-person-card.is-entering{transform:translateY(-16px) scale(1.14)!important;z-index:4;transition:transform .65s cubic-bezier(.2,.7,.2,1)}
 body[data-client-view="people"] .client-person-card.is-entering .client-card-inner{transition:transform .65s cubic-bezier(.2,.7,.2,1)!important}
 @media(prefers-reduced-motion:reduce){body[data-client-view="people"] .client-person-card{transition:none!important;transform:none!important}body[data-client-view="people"] .client-person-card.is-entering .client-card-inner{transition:none!important}}
 .china-time-control{position:relative;min-width:0;width:100%}
 .china-time-control>input{padding-right:46px!important;margin:0!important;width:100%;box-sizing:border-box}
 .china-time-control>small{display:none!important}
 .china-time-control>details>summary{position:absolute;right:6px;top:3px;width:34px;height:30px;display:grid;place-items:center;font-size:0;cursor:pointer;border-radius:6px;color:#24738b}
 .china-time-control>details>summary::after{content:'▦';font-size:23px}
 .china-time-control>details[open]>div{position:relative;z-index:10;padding:12px;margin-top:8px;border:1px solid #b5dceb;border-radius:12px;background:#f5fbff;box-shadow:0 8px 25px #123b5720}
 #client-delete-person{color:#a52e42;border-color:#ecc1c9;background:#fff6f7}
 #person-delete-status{color:#a52e42;font-size:14px;overflow-wrap:anywhere}
 body:not([data-client-view="person"]) #person-delete-status{display:none}
'''

PERSON_POLISH_SCRIPT = r'''
  for(const id of ['message-sent-at','client-media-sent-at']){
    const input=byId(id),note=input?.nextElementSibling,picker=note?.nextElementSibling;
    if(input && picker?.tagName==='DETAILS'){
      const wrap=document.createElement('div');wrap.className='china-time-control';
      input.before(wrap);wrap.append(input,note,picker);
      picker.querySelector('summary').title='选择日期和时间（北京时间）';
    }
  }
  const deletePersonButton=clientEl('button','','删除人物');deletePersonButton.type='button';deletePersonButton.id='client-delete-person';
  const deletePersonStatus=clientEl('p');deletePersonStatus.id='person-delete-status';deletePersonStatus.setAttribute('role','status');
  navWorkbar.append(deletePersonButton);navWorkbar.after(deletePersonStatus);
  deletePersonButton.addEventListener('click',async()=>{
    const person=selectedPersonId,token=currentAccessToken;if(!person || !token)return;
    const name=byId('person-select').selectedOptions[0]?.textContent || '该人物';
    if(!confirm(`永久删除「${name}」？\n其会话、聊天、截图/视频、关系、长期档案及更新记录将一并删除，无法在页面恢复。\n你的全局参考资料和模型设置保留。历史运维备份仍按备份保留策略处理。`))return;
    deletePersonButton.disabled=true;deletePersonStatus.textContent='正在删除人物及关联数据…';
    try{
      await api(`/api/v1/persons/${encodeURIComponent(person)}`,{method:'DELETE'});
      if(token!==currentAccessToken)return;
      byId('person-select').value='';byId('person-select').dispatchEvent(new Event('change',{bubbles:true}));
      await loadPersons();navShow('people',true);deletePersonStatus.textContent='';
    }catch(error){if(token===currentAccessToken)deletePersonStatus.textContent=error.message;}
    finally{deletePersonButton.disabled=false;}
  });
  const privacyNote=clientEl('p','note','模型 API 仅供当前账号使用，不与其他用户共用。每个账号都需要配置自己的 API；未配置时不会使用服务器密钥。');
  byId('provider').prepend(privacyNote);
'''
