PERSON_MEMORY_SCRIPT = r'''
  let personMemoryOffset = 0, personMemoryEpoch = 0, personMemoryTimer = null;
  const memoryHost = document.createElement('section'); memoryHost.id='person-memory-panel';
  const memoryStyle=document.createElement('style');memoryStyle.textContent=`
    #person-memory-panel{padding:12px 16px;margin:12px 0 0;border:1px solid #bde4ff;border-radius:16px;max-width:100%;min-width:0;overflow-wrap:anywhere;background:#f8fbff}
    #person-memory-panel .memory-header{display:flex;align-items:center;justify-content:space-between;gap:10px;flex-wrap:wrap}
    #person-memory-panel h3{font-size:16px;margin:0}
    #person-memory-panel p{margin:8px 0;line-height:1.6}
    #person-memory-panel button{margin:0;white-space:normal}
    #person-memory-panel summary{cursor:pointer;padding:8px 0;line-height:1.6}
    #person-memory-panel .memory-events{max-height:340px;overflow:auto;overscroll-behavior:contain;margin:8px 0}
    #person-memory-panel .memory-events>details{border-top:1px solid #dce8f3;padding:4px 8px;background:#fff}
    #person-memory-panel .memory-pages{display:flex;flex-wrap:wrap;gap:8px}
    @media(max-width:600px){#person-memory-panel{padding:12px}#person-memory-panel .memory-header{align-items:flex-start}#person-memory-panel .memory-events{max-height:280px}}
  `;document.head.append(memoryStyle);
  const memoryHeading=document.createElement('h3');memoryHeading.textContent='人物长期档案与更新记录';
  const memoryStatus=document.createElement('p');memoryStatus.textContent='选择人物后显示。';
  const memorySummary=document.createElement('details');
  const memorySummaryTitle=document.createElement('summary');memorySummaryTitle.textContent='查看内部人物摘要';
  const memorySummaryBody=document.createElement('div');memorySummary.append(memorySummaryTitle,memorySummaryBody);
  const memoryEvents=document.createElement('div');
  memoryEvents.className='memory-events';
  const memoryRefresh=document.createElement('button');memoryRefresh.type='button';memoryRefresh.textContent='分析并更新人物档案';
  const memoryOlder=document.createElement('button');memoryOlder.type='button';memoryOlder.textContent='查看更早记录';
  const memoryLatest=document.createElement('button');memoryLatest.type='button';memoryLatest.textContent='返回最新记录';
  const memoryHeader=document.createElement('div');memoryHeader.className='memory-header';memoryHeader.append(memoryHeading,memoryRefresh);
  const memoryDrawer=document.createElement('details');memoryDrawer.id='person-memory-details';
  const memoryDrawerTitle=document.createElement('summary');memoryDrawerTitle.textContent='展开档案与更新记录';
  const memoryPages=document.createElement('div');memoryPages.className='memory-pages';memoryPages.append(memoryOlder,memoryLatest);
  const profileDetails=document.createElement('details');
  const profileTitle=document.createElement('summary');profileTitle.textContent='查看完整档案条目与依据';
  const profileBody=document.createElement('div');profileBody.className='memory-events';
  const profileMore=document.createElement('button');profileMore.type='button';profileMore.textContent='加载更多档案条目';
  let profileOffset=0,profileLoaded=false,profileBusy=false;
  async function profileLoad(){
    if(profileBusy || !selectedPersonId)return;
    const person=selectedPersonId,epoch=personMemoryEpoch;profileBusy=true;profileMore.disabled=true;
    try{
      const data=await api(`/api/v1/persons/${encodeURIComponent(person)}/memory/profile?offset=${profileOffset}`);
      if(person!==selectedPersonId || epoch!==personMemoryEpoch)return;
      if(!profileLoaded){profileBody.replaceChildren();memoryLine(profileBody,'所有人物采用相同规则；回复时仅选取预算内的相关条目，不发送完整档案。');}
      if(data.stale)memoryLine(profileBody,'原聊天已修改，以下旧条目暂不用于回复，等待重建。');
      const labels={facts:'事实',preferences:'偏好',events:'重要事件',constraints:'约定与边界',unknowns:'待确认',inferences:'推断'};
      for(const item of data.items || []){
        const row=document.createElement('details'),title=document.createElement('summary');
        title.textContent=`${labels[item.kind] || item.kind} · ${item.active?'有效':'已被修订'}：${item.text}`;
        row.append(title);
        if(item.legacy)memoryLine(row,'来自升级前的摘要；原始更新记录仍可查询，未补造逐条依据。');
        if(item.revision_reason)memoryLine(row,`修订原因：${item.revision_reason}`);
        let read=false;
        row.addEventListener('toggle',async()=>{
          if(!row.open || read)return;read=true;
          for(const id of item.evidence || []){
            try{const m=await api(`/api/v1/messages/${encodeURIComponent(id)}`);
              if(person!==selectedPersonId || epoch!==personMemoryEpoch)return;
              memoryLine(row,`${chinaTimeText(m.sent_at)} · ${m.sender_type==='person'?'对方':'我'}：${m.content}`);
            }catch(_){if(person===selectedPersonId && epoch===personMemoryEpoch)memoryLine(row,'依据已删除或暂时无法读取。');}
          }
        });profileBody.append(row);
      }
      profileOffset+=(data.items || []).length;profileLoaded=true;profileMore.hidden=!data.has_more;
    }catch(_){if(person===selectedPersonId)memoryLine(profileBody,'档案条目读取失败，请重试。');}
    finally{profileBusy=false;profileMore.disabled=false;}
  }
  profileDetails.append(profileTitle,profileBody,profileMore);
  profileDetails.addEventListener('toggle',()=>{if(profileDetails.open && !profileLoaded)profileLoad();});
  profileMore.addEventListener('click',profileLoad);
  memoryDrawer.append(memoryDrawerTitle,memorySummary,profileDetails,memoryEvents,memoryPages);
  memoryHost.append(memoryHeader,memoryStatus,memoryDrawer);
  (byId('client-person-stage') || byId('person-select').parentElement).appendChild(memoryHost);
  function memoryLine(host,text){const p=document.createElement('p');p.textContent=text;host.appendChild(p);}
  function memoryRender(data){
    const label=byId('person-select').selectedOptions[0]?.textContent || '当前人物';
    memoryHeading.textContent=`${label} · 长期档案`;
    const failed=!data.running && data.latest_outcome==='failed';
    memoryStatus.textContent=(data.stale?'原记录已变更，旧摘要已停用。':'')+`已分析 ${data.covered_count}/${data.total_count} 条聊天。`+(data.running?'后台正在更新…':failed?'本批更新失败，已完成进度保留；展开记录查看原因。':'');
    memoryRefresh.disabled=Boolean(data.running);
    memoryRefresh.textContent=data.running?'正在后台分析…':failed?'重试未完成部分':'分析并更新人物档案';
    memorySummaryBody.replaceChildren();
    if(data.context_budget_bytes)memoryLine(memorySummaryBody,`回复用精简档案：${data.context_bytes}/${data.context_budget_bytes} 字节；未选入 ${data.omitted_entry_count} 条，完整条目仍保留。所有人物使用相同预算规则。`);
    memoryLine(memorySummaryBody,data.summary.description || '尚未建立摘要。');
    for(const [key,label] of [['facts','长期事实'],['preferences','偏好'],['events','重要事件'],['inferences','分析推断'],['constraints','约定与边界'],['unknowns','待确认事项']]){
      for(const text of data.summary[key] || [])memoryLine(memorySummaryBody,`${label}：${text}`);
    }
    const opened=new Set(Array.from(memoryEvents.children).filter(row=>row.open).map(row=>row.dataset.key));
    memoryEvents.replaceChildren();
    for(const event of data.events){
      const row=document.createElement('details'),title=document.createElement('summary');
      row.dataset.key=event.id || event.created_at;row.open=opened.has(row.dataset.key);
      const outcomes={updated:'已更新',failed:'更新失败',discarded:'未应用',invalidated:'摘要已失效'};
      title.textContent=`${chinaTimeText(event.created_at)} · ${event.source==='ai'?'AI 分析':'手动修改'} · ${outcomes[event.outcome] || event.outcome}`;
      row.append(title); memoryLine(row,`原因：${event.reason}`);
      if(event.after.error_code)memoryLine(row,`错误类别：${event.after.error_code}；本批已尝试 ${event.after.attempts || 1} 次。`);
      for(const change of event.after.profile_changes || []){
        memoryLine(row,`档案条目：${change.before?.text || '新增'} → ${change.after?.text || ''}${change.after?.active===false?'（已被修订）':''}`);
      }
      const before=event.before.relationship || event.before, after=event.after.relationship || event.after;
      for(const [key,label] of [['status','关系状态'],['stage','关系阶段'],['name','姓名'],['nickname','昵称'],['notes','备注'],['current_goal','当前目标'],['long_term_goal','长期目标']]){
        if(before?.[key]!==after?.[key] && (before?.[key]!==undefined || after?.[key]!==undefined))memoryLine(row,`${label}：${before?.[key] ?? '未设置'} → ${after?.[key] ?? '未设置'}`);
      }
      if(event.after.from)memoryLine(row,`分析范围：${chinaTimeText(event.after.from)} — ${chinaTimeText(event.after.to)}`);
      if(event.after.relationship_update_deferred)memoryLine(row,'较新聊天仍在分析中，关系状态将在全部处理后更新。');
      if(event.before.summary)memoryLine(row,`修改前摘要：${event.before.summary.description || '无'}`);
      if(event.after.summary)memoryLine(row,`修改后摘要：${event.after.summary.description || '无'}`);
      if(event.after.summary)for(const [key,label] of [['facts','事实'],['inferences','推断'],['constraints','约束'],['unknowns','不确定事项']]){
        memoryLine(row,`原${label}：${(event.before.summary?.[key] || []).join('；') || '无'}`);
        memoryLine(row,`新${label}：${(event.after.summary[key] || []).join('；') || '无'}`);
      }
      if(event.evidence?.length){
        const sources=document.createElement('details'),sourceTitle=document.createElement('summary');
        sourceTitle.textContent=`查看关联聊天依据（${event.evidence.length} 条）`;sources.append(sourceTitle);
        const person=selectedPersonId,token=currentAccessToken;
        let loaded=false;
        sources.addEventListener('toggle',async()=>{
          if(!sources.open || loaded)return;loaded=true;
          for(const id of event.evidence){
            try{
              const message=await api(`/api/v1/messages/${encodeURIComponent(id)}`);
              if(person!==selectedPersonId || token!==currentAccessToken)return;
              memoryLine(sources,`${chinaTimeText(message.sent_at)} · ${message.sender_type==='person'?'对方':'我'}：${message.content}`);
            }catch(_){if(person===selectedPersonId && token===currentAccessToken)memoryLine(sources,'这条依据已删除或暂时无法读取。');}
          }
        });row.appendChild(sources);
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
      const failed=!data.running && data.latest_outcome==='failed';
      const needsProfile=data.consolidated===false && data.covered_count===data.total_count && Object.keys(data.summary).length>0;
      if(continueUpdate && !failed && !data.running && (data.stale || data.covered_count<data.total_count || needsProfile)){
        await api(`/api/v1/persons/${encodeURIComponent(person)}/memory/refresh`,{method:'POST'});
        if(!current())return;
        memoryStatus.textContent+=' 已安排后台更新，回复生成无需等待。';
      }
      if(continueUpdate && !failed && (data.running || data.stale || data.covered_count<data.total_count || needsProfile)){
        clearTimeout(personMemoryTimer);personMemoryTimer=setTimeout(()=>{if(current())memoryLoad(true)},4000);
      }
    }catch(error){if(current())memoryStatus.textContent=`档案更新记录读取失败：${error.message}`;}
  }
  async function memoryStart(){
    if(!selectedPersonId || !currentAccessToken)return;
    const person=selectedPersonId,token=currentAccessToken;
    memoryRefresh.disabled=true;memoryStatus.textContent='正在安排后台分析，已完成进度保留…';
    try{await api(`/api/v1/persons/${encodeURIComponent(person)}/memory/refresh`,{method:'POST'});
      if(person===selectedPersonId && token===currentAccessToken){personMemoryOffset=0;clearTimeout(personMemoryTimer);personMemoryTimer=setTimeout(()=>memoryLoad(true),1000);}
    }catch(error){if(person===selectedPersonId){memoryRefresh.disabled=false;memoryStatus.textContent=`档案分析未启动：${error.message}`;}}
  }
  memoryRefresh.addEventListener('click',memoryStart);
  memoryOlder.addEventListener('click',()=>{personMemoryOffset+=20;memoryLoad();});
  memoryLatest.addEventListener('click',()=>{personMemoryOffset=0;memoryLoad();});
  byId('person-select').addEventListener('change',()=>{
    personMemoryEpoch++;clearTimeout(personMemoryTimer);personMemoryOffset=0;memoryEvents.replaceChildren();memorySummaryBody.replaceChildren();memoryDrawer.open=false;
    profileOffset=0;profileLoaded=false;profileDetails.open=false;profileBody.replaceChildren();
    memoryStatus.textContent='正在读取人物档案…';queueMicrotask(()=>memoryLoad(true));
  });
  window.addEventListener('junshi:evidence-changed',event=>{
    if(!event.detail?.conversation_id || event.detail.conversation_id===selectedConversationId)memoryStart();
  });
  const memoryBaseClearSession=clearSession;
  clearSession=function(message){personMemoryEpoch++;clearTimeout(personMemoryTimer);memoryEvents.replaceChildren();memorySummaryBody.replaceChildren();profileBody.replaceChildren();profileOffset=0;profileLoaded=false;profileDetails.open=false;memoryDrawer.open=false;memoryHeading.textContent='人物长期档案与更新记录';memoryStatus.textContent='请先登录并选择人物。';memoryBaseClearSession(message);};
'''
