PERSON_MEMORY_SCRIPT = r'''
  let personMemoryOffset = 0, personMemoryEpoch = 0, personMemoryTimer = null;
  const memoryHost = document.createElement('section'); memoryHost.id='person-memory-panel';
  memoryHost.style.cssText='padding:16px;margin:12px 0;border:1px solid #bde4ff;border-radius:16px;max-width:100%;overflow-wrap:anywhere';
  const memoryHeading=document.createElement('h3');memoryHeading.textContent='人物长期档案与更新记录';
  const memoryStatus=document.createElement('p');memoryStatus.textContent='选择人物后显示。';
  const memorySummary=document.createElement('details');
  const memorySummaryTitle=document.createElement('summary');memorySummaryTitle.textContent='查看内部人物摘要';
  const memorySummaryBody=document.createElement('div');memorySummary.append(memorySummaryTitle,memorySummaryBody);
  const memoryEvents=document.createElement('div');
  const memoryRefresh=document.createElement('button');memoryRefresh.type='button';memoryRefresh.textContent='分析并更新人物档案';
  const memoryOlder=document.createElement('button');memoryOlder.type='button';memoryOlder.textContent='查看更早记录';
  const memoryLatest=document.createElement('button');memoryLatest.type='button';memoryLatest.textContent='返回最新记录';
  memoryHost.append(memoryHeading,memoryStatus,memoryRefresh,memorySummary,memoryEvents,memoryOlder,memoryLatest);
  (byId('client-person-stage') || byId('person-select').parentElement).appendChild(memoryHost);
  function memoryLine(host,text){const p=document.createElement('p');p.textContent=text;host.appendChild(p);}
  function memoryRender(data){
    memoryStatus.textContent=(data.stale?'原记录已变更，旧摘要已停用。':'')+`已分析 ${data.covered_count}/${data.total_count} 条聊天。`+(data.running?'后台正在更新…':'');
    memorySummaryBody.replaceChildren();
    memoryLine(memorySummaryBody,data.summary.description || '尚未建立摘要。');
    for(const [key,label] of [['facts','长期事实'],['constraints','约定与边界'],['unknowns','待确认事项']]){
      for(const text of data.summary[key] || [])memoryLine(memorySummaryBody,`${label}：${text}`);
    }
    memoryEvents.replaceChildren();
    for(const event of data.events){
      const row=document.createElement('details'),title=document.createElement('summary');
      const outcomes={updated:'已更新',failed:'更新失败',discarded:'未应用',invalidated:'摘要已失效'};
      title.textContent=`${chinaTimeText(event.created_at)} · ${event.source==='ai'?'AI 分析':'手动修改'} · ${outcomes[event.outcome] || event.outcome}`;
      row.append(title); memoryLine(row,`原因：${event.reason}`);
      const before=event.before.relationship || event.before, after=event.after.relationship || event.after;
      for(const [key,label] of [['status','关系状态'],['stage','关系阶段'],['name','姓名'],['nickname','昵称'],['notes','备注'],['current_goal','当前目标'],['long_term_goal','长期目标']]){
        if(before?.[key]!==after?.[key] && (before?.[key]!==undefined || after?.[key]!==undefined))memoryLine(row,`${label}：${before?.[key] ?? '未设置'} → ${after?.[key] ?? '未设置'}`);
      }
      if(event.after.from)memoryLine(row,`分析范围：${chinaTimeText(event.after.from)} — ${chinaTimeText(event.after.to)}`);
      if(event.before.summary)memoryLine(row,`修改前摘要：${event.before.summary.description || '无'}`);
      if(event.after.summary)memoryLine(row,`修改后摘要：${event.after.summary.description || '无'}`);
      if(event.after.summary)for(const [key,label] of [['facts','事实'],['constraints','约束'],['unknowns','不确定事项']]){
        memoryLine(row,`原${label}：${(event.before.summary?.[key] || []).join('；') || '无'}`);
        memoryLine(row,`新${label}：${(event.after.summary[key] || []).join('；') || '无'}`);
      }
      memoryEvents.appendChild(row);
    }
    memoryOlder.disabled=!data.has_more;memoryLatest.disabled=personMemoryOffset===0;
  }
  async function memoryLoad(continueUpdate=false){
    const person=selectedPersonId,token=currentAccessToken,epoch=personMemoryEpoch;
    if(!person || !token)return;
    const current=()=>person===selectedPersonId && token===currentAccessToken && epoch===personMemoryEpoch;
    try{
      const data=await api(`/api/v1/persons/${encodeURIComponent(person)}/memory?offset=${personMemoryOffset}`);
      if(!current())return;memoryRender(data);
      const failed=!data.running && data.events[0]?.outcome==='failed';
      if(continueUpdate && !failed && !data.running && (data.stale || data.covered_count<data.total_count)){
        await api(`/api/v1/persons/${encodeURIComponent(person)}/memory/refresh`,{method:'POST'});
        if(!current())return;
        memoryStatus.textContent+=' 已安排后台更新，回复生成无需等待。';
      }
      if(continueUpdate && !failed && (data.running || data.stale || data.covered_count<data.total_count)){
        clearTimeout(personMemoryTimer);personMemoryTimer=setTimeout(()=>{if(current())memoryLoad(true)},4000);
      }
    }catch(error){if(current())memoryStatus.textContent=`档案更新记录读取失败：${error.message}`;}
  }
  async function memoryStart(){
    if(!selectedPersonId || !currentAccessToken)return;
    const person=selectedPersonId,token=currentAccessToken;
    try{await api(`/api/v1/persons/${encodeURIComponent(person)}/memory/refresh`,{method:'POST'});
      if(person===selectedPersonId && token===currentAccessToken){personMemoryOffset=0;clearTimeout(personMemoryTimer);personMemoryTimer=setTimeout(()=>memoryLoad(true),1000);}
    }catch(error){if(person===selectedPersonId)memoryStatus.textContent=`档案分析未启动：${error.message}`;}
  }
  memoryRefresh.addEventListener('click',memoryStart);
  memoryOlder.addEventListener('click',()=>{personMemoryOffset+=20;memoryLoad();});
  memoryLatest.addEventListener('click',()=>{personMemoryOffset=0;memoryLoad();});
  byId('person-select').addEventListener('change',()=>{
    personMemoryEpoch++;clearTimeout(personMemoryTimer);personMemoryOffset=0;memoryEvents.replaceChildren();memorySummaryBody.replaceChildren();
    memoryStatus.textContent='正在读取人物档案…';queueMicrotask(()=>memoryLoad(true));
  });
  window.addEventListener('junshi:evidence-changed',event=>{
    if(!event.detail?.conversation_id || event.detail.conversation_id===selectedConversationId)memoryStart();
  });
  const memoryBaseClearSession=clearSession;
  clearSession=function(message){personMemoryEpoch++;clearTimeout(personMemoryTimer);memoryEvents.replaceChildren();memorySummaryBody.replaceChildren();memoryStatus.textContent='请先登录并选择人物。';memoryBaseClearSession(message);};
'''
