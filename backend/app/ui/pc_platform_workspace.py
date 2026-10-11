PC_PLATFORM_SCRIPT = r'''
  const pcStyle=document.createElement('style');pcStyle.textContent=`
    .pc-tools{padding:16px;border:1px solid #c7ddec;border-radius:16px;background:#f7fbff;color:#193249;margin:12px 0}
    .pc-tools label{display:block;margin:8px 0}.pc-tools input,.pc-tools select{width:100%;box-sizing:border-box}
    .pc-tools .pc-row{display:flex;flex-wrap:wrap;gap:8px;align-items:center}.pc-tools button{margin:4px 0}
    .pc-tools li{margin:8px 0;overflow-wrap:anywhere}body:not([data-client-view="person"]) #pc-platform-panel{display:none}
    @media(max-width:768px){.pc-tools{display:none!important}}
  `;document.head.append(pcStyle);
  const pcPanel=clientEl('details','pc-tools');pcPanel.id='pc-platform-panel';
  {
  const node1=document.createElement("summary");
  pcPanel.append(node1);
  node1.append(document.createTextNode("PC 聊天助手 · 人物多平台账号"));
  const node2=document.createElement("p");
  pcPanel.append(node2);
  node2.append(document.createTextNode("同一个人物可绑定多个平台账号，共用长期档案。账号仅记录身份，不会登录或接管聊天软件。"));
  const node3=document.createElement("ul");
  node3.setAttribute("id","pc-account-list");
  pcPanel.append(node3);
  const node4=document.createElement("div");
  node4.setAttribute("class","pc-row");
  pcPanel.append(node4);
  const node5=document.createElement("label");
  node4.append(node5);
  node5.append(document.createTextNode("平台"));
  const node6=document.createElement("select");
  node6.setAttribute("id","pc-platform");
  node5.append(node6);
  const node7=document.createElement("option");
  node7.setAttribute("value","wechat");
  node6.append(node7);
  node7.append(document.createTextNode("微信"));
  const node8=document.createElement("option");
  node8.setAttribute("value","douyin");
  node6.append(node8);
  node8.append(document.createTextNode("抖音"));
  const node9=document.createElement("option");
  node9.setAttribute("value","tantan");
  node6.append(node9);
  node9.append(document.createTextNode("探探"));
  const node10=document.createElement("option");
  node10.setAttribute("value","momo");
  node6.append(node10);
  node10.append(document.createTextNode("陌陌"));
  const node11=document.createElement("option");
  node11.setAttribute("value","soul");
  node6.append(node11);
  node11.append(document.createTextNode("Soul"));
  const node12=document.createElement("option");
  node12.setAttribute("value","other");
  node6.append(node12);
  node12.append(document.createTextNode("其他"));
  const node13=document.createElement("label");
  node4.append(node13);
  node13.append(document.createTextNode("账号标识"));
  const node14=document.createElement("input");
  node14.setAttribute("id","pc-handle");
  node14.setAttribute("maxlength","120");
  node14.setAttribute("placeholder","平台账号 ID，不按昵称自动合并");
  node13.append(node14);
  const node15=document.createElement("label");
  node4.append(node15);
  node15.append(document.createTextNode("显示名称"));
  const node16=document.createElement("input");
  node16.setAttribute("id","pc-display");
  node16.setAttribute("maxlength","120");
  node15.append(node16);
  const node17=document.createElement("button");
  node17.setAttribute("type","button");
  node17.setAttribute("id","pc-add-account");
  node4.append(node17);
  node17.append(document.createTextNode("绑定到此人物"));
  const node18=document.createElement("label");
  pcPanel.append(node18);
  node18.append(document.createTextNode("当前会话来源"));
  const node19=document.createElement("select");
  node19.setAttribute("id","pc-source");
  node18.append(node19);
  const node20=document.createElement("option");
  node20.setAttribute("value","");
  node19.append(node20);
  node20.append(document.createTextNode("未标注"));
  const node21=document.createElement("button");
  node21.setAttribute("type","button");
  node21.setAttribute("id","pc-save-source");
  pcPanel.append(node21);
  node21.append(document.createTextNode("保存会话来源"));
  const node22=document.createElement("p");
  pcPanel.append(node22);
  node22.append(document.createTextNode("一个会话对应一个来源；从其他平台导入时先新建会话。旧记录默认未标注，不会猜测来源。"));
  const node23=document.createElement("button");
  node23.setAttribute("type","button");
  node23.setAttribute("id","pc-paste");
  pcPanel.append(node23);
  node23.append(document.createTextNode("读取已复制的聊天文字"));
  const node24=document.createElement("button");
  node24.setAttribute("type","button");
  node24.setAttribute("id","pc-screenshot");
  pcPanel.append(node24);
  node24.append(document.createTextNode("选择聊天截图"));
  const node25=document.createElement("p");
  pcPanel.append(node25);
  node25.append(document.createTextNode("导入后请在下方核对内容、发送者和时间，再点击添加。生成建议后使用原有复制按钮，复制不会记作已经发送。"));
  const node26=document.createElement("p");
  node26.setAttribute("id","pc-status");
  node26.setAttribute("role","status");
  pcPanel.append(node26);
  }
  memoryHost.before(pcPanel);
  let pcEpoch=0;
  const pcNames={wechat:'微信',douyin:'抖音',tantan:'探探',momo:'陌陌',soul:'Soul',other:'其他'};
  function pcStatus(message){byId('pc-status').textContent=message;}
  async function pcLoad(){
    const epoch=++pcEpoch,person=selectedPersonId,conversation=selectedConversationId,token=currentAccessToken;
    byId('pc-account-list').replaceChildren();byId('pc-source').replaceChildren(new Option('未标注',''));
    if(!person || !token)return;
    try{
      const accounts=await api(`/api/v1/persons/${encodeURIComponent(person)}/platform-accounts`);
      const source=conversation?await api(`/api/v1/conversations/${encodeURIComponent(conversation)}/platform-source`):null;
      if(epoch!==pcEpoch || person!==selectedPersonId || token!==currentAccessToken)return;
      for(const account of accounts){
        const label=`${pcNames[account.platform]||account.platform} · ${account.display_name||account.account_handle} (${account.account_handle})`;
        byId('pc-source').add(new Option(label,account.id));
        const row=clientEl('li','',label),remove=clientEl('button','','解除绑定');remove.type='button';
        remove.addEventListener('click',async()=>{if(!confirm('解除账号绑定？已使用此账号的会话需要先解除来源。'))return;
          try{await api(`/api/v1/persons/${encodeURIComponent(person)}/platform-accounts/${encodeURIComponent(account.id)}`,{method:'DELETE'});await pcLoad();}catch(e){pcStatus(e.message);}});
        row.append(' ',remove);byId('pc-account-list').append(row);
      }
      byId('pc-source').value=source?.id||'';pcStatus(conversation?'已读取当前人物和会话来源。':'请先选择或新建会话。');
    }catch(e){if(epoch===pcEpoch)pcStatus(e.message);}
  }
  byId('pc-add-account').addEventListener('click',async()=>{
    if(!selectedPersonId || !currentAccessToken)return pcStatus('请先登录并选择人物。');
    const person=selectedPersonId;
    try{await api(`/api/v1/persons/${encodeURIComponent(person)}/platform-accounts`,{method:'POST',body:JSON.stringify({platform:byId('pc-platform').value,account_handle:byId('pc-handle').value,display_name:byId('pc-display').value})});
      if(person!==selectedPersonId)return;byId('pc-handle').value='';byId('pc-display').value='';await pcLoad();
    }catch(e){pcStatus(e.message);}
  });
  byId('pc-save-source').addEventListener('click',async()=>{
    if(!selectedConversationId)return pcStatus('请先选择会话。');
    if(!confirm('将当前会话整体标注为所选平台来源？已有聊天内容不会移动到其他人物。'))return;
    try{await api(`/api/v1/conversations/${encodeURIComponent(selectedConversationId)}/platform-source`,{method:'PUT',body:JSON.stringify({account_id:byId('pc-source').value||null})});pcStatus('会话来源已保存。');}catch(e){pcStatus(e.message);}
  });
  byId('pc-paste').addEventListener('click',async()=>{
    if(!selectedConversationId)return pcStatus('请先选择人物和会话。');
    const conversation=selectedConversationId,token=currentAccessToken;
    try{const text=await navigator.clipboard.readText();if(conversation!==selectedConversationId || token!==currentAccessToken)return;
      const input=byId('text-import-body');if(input.value && !confirm('替换尚未提交的输入内容？'))return;
      input.value=text;input.dispatchEvent(new Event('input',{bubbles:true}));input.focus();input.scrollIntoView({block:'center'});
      pcStatus('已填入输入框，尚未上传。请识别预览并确认双方身份后再添加。');
    }catch(_){pcStatus('浏览器未允许读取剪贴板，请直接在会话内容框按 Ctrl+V；HTTPS 或本机访问可使用此功能。');}
  });
  byId('pc-screenshot').addEventListener('click',()=>{if(!selectedConversationId)return pcStatus('请先选择会话。');byId('client-media-file')?.click();byId('client-media-import-card')?.scrollIntoView({block:'center'});});
  const pcBaseLoad=loadConversations;
  loadConversations=async function(...args){const value=await pcBaseLoad(...args);await pcLoad();return value;};
  byId('conversation-select').addEventListener('change',()=>queueMicrotask(pcLoad));
  byId('person-select').addEventListener('change',()=>{pcEpoch++;queueMicrotask(pcLoad);});
  const pcClear=clearSession;clearSession=function(...args){pcEpoch++;byId('pc-account-list').replaceChildren();byId('pc-source').replaceChildren(new Option('未标注',''));pcPanel.open=false;return pcClear(...args);};
  window.addEventListener('keydown',event=>{if(event.ctrlKey && event.altKey && event.code==='KeyJ' && matchMedia('(min-width:769px)').matches()){
    event.preventDefault();pcPanel.open=true;pcPanel.scrollIntoView({block:'center'});byId('pc-paste').focus();}});
  if(new URLSearchParams(location.search).get('pc')==='1')pcPanel.open=true;

  const transfer=clientEl('details','pc-tools');transfer.id='pc-transfer';
  {
  const node1=document.createElement("summary");
  transfer.append(node1);
  node1.append(document.createTextNode("PC 数据迁移 · 完整导出 / 导入"));
  const node2=document.createElement("p");
  transfer.append(node2);
  node2.append(document.createTextNode("导出当前账号全部业务数据、平台来源、长期档案、参考资料及媒体。登录凭据与模型密钥不导出。文件经密码加密，请牢记密码；不会上传到 GitHub。"));
  const node3=document.createElement("label");
  transfer.append(node3);
  node3.append(document.createTextNode("迁移密码（至少 12 个字符）"));
  const node4=document.createElement("input");
  node4.setAttribute("id","pc-transfer-password");
  node4.setAttribute("type","password");
  node4.setAttribute("minlength","12");
  node4.setAttribute("maxlength","256");
  node4.setAttribute("autocomplete","new-password");
  node3.append(node4);
  const node5=document.createElement("button");
  node5.setAttribute("type","button");
  node5.setAttribute("id","pc-export");
  transfer.append(node5);
  node5.append(document.createTextNode("完整导出到电脑"));
  const node6=document.createElement("label");
  transfer.append(node6);
  node6.append(document.createTextNode("迁移包"));
  const node7=document.createElement("input");
  node7.setAttribute("id","pc-transfer-file");
  node7.setAttribute("type","file");
  node7.setAttribute("accept",".jsa");
  node6.append(node7);
  const node8=document.createElement("button");
  node8.setAttribute("type","button");
  node8.setAttribute("id","pc-import");
  transfer.append(node8);
  node8.append(document.createTextNode("导入到当前空白账号"));
  const node9=document.createElement("p");
  transfer.append(node9);
  node9.append(document.createTextNode("仅导入另一套本项目部署，不会把历史写回微信等第三方 App。导入保留原始标识；目标必须无业务数据。同一包重复导入会被拒绝。超过 64 MiB 时导出停止，不截断内容。"));
  const node10=document.createElement("p");
  node10.setAttribute("id","pc-transfer-status");
  node10.setAttribute("role","status");
  transfer.append(node10);
  }
  navFooter.append(transfer);
  async function pcTransfer(importing){
    const password=byId('pc-transfer-password').value,status=byId('pc-transfer-status'),token=currentAccessToken;
    if(!token){status.textContent='请先登录';return;}if(password.length<12){status.textContent='迁移密码至少 12 个字符';return;}
    const headers={Authorization:`Bearer ${token}`};let body;
    if(importing){const file=byId('pc-transfer-file').files[0];if(!file){status.textContent='请选择迁移包';return;}
      if(!confirm('导入当前空白账号？目标有业务数据时不会覆盖。'))return;
      body=new FormData();body.append('password',password);body.append('file',file);
    }else{headers['Content-Type']='application/json';body=JSON.stringify({password});}
    byId('pc-export').disabled=true;byId('pc-import').disabled=true;status.textContent='正在处理，请勿重复操作…';
    try{const response=await fetch(`/api/v1/account-transfer/${importing?'import':'export'}`,{method:'POST',headers,body});
      if(!response.ok){const result=await response.json();throw new Error(typeof result.detail==='string'?result.detail:'数据迁移失败');}
      if(currentAccessToken!==token)return;
      if(importing){status.textContent='完整导入成功，请刷新人物列表。模型 API 需在本账号单独配置。';await loadPersons();}
      else{const blob=await response.blob();if(currentAccessToken!==token)return;const url=URL.createObjectURL(blob),link=document.createElement('a');link.href=url;link.download='junshi-account.jsa';link.click();setTimeout(()=>URL.revokeObjectURL(url),30000);status.textContent='已生成完整加密迁移包，请确认浏览器下载完成并妥善保管密码。';}
    }catch(e){if(token===currentAccessToken)status.textContent=e.message;}
    finally{byId('pc-transfer-password').value='';byId('pc-export').disabled=false;byId('pc-import').disabled=false;}
  }
  byId('pc-export').addEventListener('click',()=>pcTransfer(false));byId('pc-import').addEventListener('click',()=>pcTransfer(true));
'''
