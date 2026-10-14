EMAIL_ACCOUNT_HTML = r'''
<dialog id="email-account-center" style="width:min(760px,90vw);max-height:85vh;overflow:auto;border:1px solid #b7d9ed;border-radius:18px;padding:20px">
<h2>邮箱与账号管理</h2><button id="email-center-close" type="button">关闭</button>
<p>邮箱验证码有效期 10 分钟。管理员可按需查看用户业务数据，查看及删除操作会留下记录。</p>
<label for="email-address">邮箱地址</label><input id="email-address" type="email" autocomplete="email">
<label for="email-purpose">操作</label><select id="email-purpose"><option value="register">邮箱验证注册</option><option value="bind">绑定邮箱</option><option value="reset">重置密码</option><option value="delete">注销账号</option></select>
<label for="email-current-password">当前密码（绑定或注销时填写）</label><input id="email-current-password" type="password" autocomplete="current-password">
<button id="email-send-code" type="button">发送验证码</button>
<label for="email-code">六位验证码</label><input id="email-code" inputmode="numeric" autocomplete="one-time-code">
<label for="email-new-password">新密码（注册使用登录框密码，重置时填写这里）</label><input id="email-new-password" type="password" autocomplete="new-password">
<p>密码 12–256 个字符，无强制特殊符号要求。</p>
<label for="email-delete-confirm">注销不可撤销：输入 DELETE 确认</label><input id="email-delete-confirm" autocomplete="off">
<p>注销会删除人物、聊天、附件、档案和模型配置。历史备份按服务器保留周期清除。</p>
<button id="email-submit" type="button">确认操作</button>
<div id="email-center-status" role="status" style="white-space:pre-wrap;overflow-wrap:anywhere"></div>
<section id="email-admin-panel" hidden><h3>管理员后台</h3>
<button id="email-admin-list" type="button">查询用户</button><button id="email-admin-audit" type="button">查看操作记录</button>
<label for="email-admin-target">目标用户 ID</label><input id="email-admin-target">
<label for="email-admin-reason">查看或修改原因</label><input id="email-admin-reason">
<select id="email-admin-kind"><option value="persons">人物资料</option><option value="conversations">会话</option><option value="messages">聊天内容</option><option value="relationships">关系状态</option><option value="person_memories">长期档案</option><option value="person_update_events">档案更新记录</option><option value="model_references">参考资料与 Skills</option><option value="person_platform_accounts">平台账号</option><option value="media_attachments">附件及分析结果</option></select>
<label for="email-admin-offset">分页起始位置（每页 50 条）</label><input id="email-admin-offset" type="number" min="0" value="0">
<button id="email-admin-view" type="button">查看数据</button><button id="email-admin-disable" type="button">禁用</button><button id="email-admin-enable" type="button">恢复</button><button id="email-admin-delete" type="button">永久删除用户</button>
<pre id="email-admin-result" style="white-space:pre-wrap;overflow-wrap:anywhere;max-height:280px;overflow:auto"></pre></section>
</dialog>
'''

EMAIL_ACCOUNT_SCRIPT = r'''
  let emailChallenge=null;
  const emailStatus=byId('email-center-status');
  const emailRun=(id,action)=>byId(id).addEventListener('click',async()=>{
    const button=byId(id);button.disabled=true;
    try{await action();}catch(error){emailStatus.textContent=error.message;}finally{button.disabled=false;}
  });
  const emailValue=id=>byId(id).value;
  const centerOpen=document.createElement('button');centerOpen.type='button';centerOpen.textContent='邮箱注册 / 找回密码 / 账号管理';
  byId('account').appendChild(centerOpen);
  queueMicrotask(()=>{
    const footer=byId('client-footer');
    if(footer){const link=document.createElement('button');link.type='button';link.textContent='邮箱与账号管理';link.addEventListener('click',()=>centerOpen.click());footer.appendChild(link);}
  });
  centerOpen.addEventListener('click',async()=>{
    byId('email-account-center').showModal();byId('email-admin-panel').hidden=true;
    if(currentAccessToken){try{const own=await api('/api/v1/auth/email/identity');byId('email-address').value=own.email||'';byId('email-admin-panel').hidden=!own.administrator;}catch(e){emailStatus.textContent=e.message;}}
  });
  byId('email-center-close').addEventListener('click',()=>{
    byId('email-account-center').close();emailChallenge=null;
    ['email-current-password','email-new-password','email-code','email-delete-confirm'].forEach(id=>byId(id).value='');
    byId('email-admin-result').textContent='';
  });
  emailRun('email-send-code',async()=>{
    const purpose=emailValue('email-purpose'),email=emailValue('email-address').trim();
    const data=await api('/api/v1/auth/email/code',{method:'POST',body:JSON.stringify({email,purpose,current_password:emailValue('email-current-password')||null})},purpose==='bind'||purpose==='delete');
    emailChallenge={id:data.challenge_id,email,purpose};emailStatus.textContent=data.message;
  });
  emailRun('email-submit',async()=>{
    const purpose=emailValue('email-purpose'),email=emailValue('email-address').trim();
    if(!emailChallenge||emailChallenge.email!==email||emailChallenge.purpose!==purpose)throw new Error('请先为本次操作发送验证码');
    const body={email,challenge_id:emailChallenge.id,code:emailValue('email-code')};
    let result;
    if(purpose==='register'){
      body.username=byId('username').value.trim();body.password=byId('password').value;
      result=await api('/api/v1/auth/email/register',{method:'POST',body:JSON.stringify(body)},false);
      establishSession(result,'邮箱注册成功。');await loadWorkspace();
    }else if(purpose==='reset'){
      body.new_password=emailValue('email-new-password');await api('/api/v1/auth/email/reset-password',{method:'POST',body:JSON.stringify(body)},false);clearSession('密码已重置，请重新登录。');
    }else if(purpose==='bind'){
      body.current_password=emailValue('email-current-password');await api('/api/v1/auth/email/binding',{method:'PUT',body:JSON.stringify(body)});
    }else{
      body.current_password=emailValue('email-current-password');body.confirmation=emailValue('email-delete-confirm');
      if(body.confirmation!=='DELETE'||!confirm('永久删除当前账号及全部业务数据？'))return;
      result=await api('/api/v1/auth/email/delete-account',{method:'POST',body:JSON.stringify(body)});clearSession('账号已注销。');
    }
    emailChallenge=null;['email-current-password','email-new-password','email-code','email-delete-confirm'].forEach(id=>byId(id).value='');
    emailStatus.textContent=result&&result.cleanup_pending?'账号已删除，附件清理任务待管理员重试。':'操作完成。';
  });
  const adminTarget=()=>encodeURIComponent(emailValue('email-admin-target').trim());
  const adminShow=data=>byId('email-admin-result').textContent=JSON.stringify(data,null,2);
  const adminOffset=()=>String(Math.max(0,Number(emailValue('email-admin-offset'))||0));
  emailRun('email-admin-list',async()=>adminShow(await api('/api/v1/admin/accounts?offset='+adminOffset())));
  emailRun('email-admin-audit',async()=>adminShow(await api('/api/v1/admin/accounts/audit/history?offset='+adminOffset())));
  emailRun('email-admin-view',async()=>adminShow(await api('/api/v1/admin/accounts/'+adminTarget()+'/data/'+emailValue('email-admin-kind')+'?offset='+adminOffset()+'&reason='+encodeURIComponent(emailValue('email-admin-reason')))));
  for(const [id,disabled] of [['email-admin-disable',true],['email-admin-enable',false]])emailRun(id,async()=>adminShow(await api('/api/v1/admin/accounts/'+adminTarget()+'/state',{method:'PATCH',body:JSON.stringify({disabled,reason:emailValue('email-admin-reason')})})));
  emailRun('email-admin-delete',async()=>{
    if(prompt('永久删除目标用户：输入 DELETE 确认')!=='DELETE')return;
    adminShow(await api('/api/v1/admin/accounts/'+adminTarget()+'/delete',{method:'POST',body:JSON.stringify({confirmation:'DELETE',reason:emailValue('email-admin-reason')})}));
  });
'''
