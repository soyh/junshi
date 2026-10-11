PERSON_POLISH_STYLE = r'''
 html:has(body[data-client-view="people"]),html:has(body[data-client-view="auth"]){background:#0b1522}
 body[data-client-view="people"]{background:radial-gradient(ellipse at 50% 60%,#22455580,transparent 56%),radial-gradient(ellipse at 20% 10%,#30385850,transparent 55%),#0b1522!important}
 body[data-client-view="people"] #client-person-deck{padding-bottom:80px}
 body[data-client-view="people"] .client-person-card{animation:personHover 6s ease-in-out infinite!important;position:relative;isolation:isolate}
 body[data-client-view="people"] .client-person-card:nth-child(2n){animation-delay:-2.5s!important}
 body[data-client-view="people"] .client-person-card::after{content:"";position:absolute;pointer-events:none;bottom:-38px;left:12%;width:76%;height:13px;border-radius:50%;background:#80f5e980;box-shadow:0 0 8px #afffee,0 0 32px 12px #40c6d04d,0 12px 28px #000;transform:rotateX(35deg);z-index:-1}
 body[data-client-view="people"] .client-person-card::before{content:"";position:absolute;pointer-events:none;inset:60% 3% -35px;clip-path:polygon(0 0,100% 0,75% 100%,25% 100%);background:linear-gradient(0deg,#6be9e22b,transparent);filter:blur(9px);z-index:-1}
 body[data-client-view="people"] .client-card-front{background:linear-gradient(140deg,#36546599,#132638cc)!important;backdrop-filter:blur(18px);box-shadow:0 26px 55px #0009,inset 0 1px #b8f5ff33!important}
 body[data-client-view="people"] .client-person-card.is-flipped,body[data-client-view="people"] .client-person-card.is-entering{animation:none!important}
 @keyframes personHover{0%,100%{translate:0 0}50%{translate:0 -10px}}
 @media(prefers-reduced-motion:reduce){body[data-client-view="people"] .client-person-card{animation:none!important}}
 .china-time-control{position:relative;min-width:0;width:100%}
 .china-time-control>input{padding-right:46px!important;margin:0!important;width:100%;box-sizing:border-box}
 .china-time-control>small{display:none!important}
 .china-time-control>details>summary{position:absolute;right:6px;top:3px;width:34px;height:30px;display:grid;place-items:center;font-size:0;cursor:pointer;border-radius:6px;color:#24738b}
 .china-time-control>details>summary::after{content:'▦';font-size:23px}
 .china-time-control>details[open]>div{position:relative;z-index:10;padding:12px;margin-top:8px;border:1px solid #b5dceb;border-radius:12px;background:#f5fbff;box-shadow:0 8px 25px #123b5720}
 #client-delete-person{color:#a52e42;border-color:#ecc1c9;background:#fff6f7}
 #person-delete-status{color:#a52e42;font-size:14px;overflow-wrap:anywhere}
 body:not([data-client-view="person"]) #person-delete-status{display:none}
 body[data-client-view="people"] .client-person-card:hover,body[data-client-view="people"] .client-person-card:focus-within{animation-play-state:paused!important}
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
