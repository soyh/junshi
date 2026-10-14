EMAIL_ACCOUNT_HTML = r'''
<style>
#email-account-center{box-sizing:border-box;width:min(960px,94vw);max-height:88vh;overflow:auto;border:1px solid #c9e0f1;border-radius:22px;padding:24px;background:linear-gradient(140deg,#fff,#f1f8ff);color:#23415b;box-shadow:0 24px 80px #16395240}
#email-account-center::backdrop{background:#18375066;backdrop-filter:blur(5px)}
#email-account-center h2{margin:0 0 16px}#email-account-center p{color:#607b91;font-size:14px;line-height:1.6}
#email-account-center label{display:block;margin-top:14px;font-weight:600}
#email-account-center input,#email-account-center select{box-sizing:border-box;width:100%;min-height:44px;margin:6px 0;padding:10px 12px;border:1px solid #c9dfee;border-radius:12px;background:#fff;color:#23415b;font:inherit}
#email-account-center button,.email-account-launch{min-height:42px;margin:6px 6px 6px 0;padding:10px 16px;border:1px solid #bfdcf0;border-radius:12px;background:linear-gradient(#fff,#eaf5ff);color:#287bc1;box-shadow:0 3px 8px #287bc114;font:inherit;cursor:pointer}
#email-account-center #email-submit,#email-account-center #email-send-code{background:#287bc1;color:white;border-color:#287bc1}
#email-account-center #email-admin-delete{color:#b33f4d;background:#fff0f2;border-color:#efc6cc}
#email-account-center button:hover{filter:brightness(.96);transform:translateY(-1px)}
#email-account-center button:disabled{opacity:.5;cursor:default;transform:none}
#email-account-center :focus-visible,.email-account-launch:focus-visible{outline:3px solid #72baf0;outline-offset:2px}
#email-admin-panel{border-top:1px solid #c9e0f1;margin-top:24px;padding-top:12px}
.email-table-wrap{overflow:auto;max-height:360px;border:1px solid #c9e0f1;border-radius:12px;background:white}
#email-user-table{border-collapse:collapse;width:100%;min-width:630px;font-size:14px}#email-user-table th,#email-user-table td{padding:10px;text-align:left;border-bottom:1px solid #e2edf5;overflow-wrap:anywhere;max-width:230px}
#email-user-table th{position:sticky;top:0;background:#eaf5ff;z-index:1}#email-user-table tr[aria-selected=true]{background:#e2f2ff}
#email-admin-target{display:block;padding:12px;border-radius:12px;background:#eaf5ff;overflow-wrap:anywhere}
#email-admin-result{white-space:pre-wrap;overflow-wrap:anywhere;max-height:280px;overflow:auto;background:#f4f9fe;border-radius:12px;padding:12px}
#client-footer .email-footer-link{font:inherit;color:inherit;background:transparent;border:0;box-shadow:none;padding:8px;margin:0;cursor:pointer}
@media(max-width:600px){#email-account-center{padding:16px}#email-account-center button{font-size:14px;padding:10px 12px}}
</style>
<dialog id="email-account-center" aria-labelledby="email-center-title">
<h2 id="email-center-title">邮箱与账号管理</h2><button id="email-center-close" type="button">关闭</button>
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
<label for="email-user-search">选择用户（支持账号、邮箱或 ID 搜索）</label>
<input id="email-user-search" type="search" maxlength="100" placeholder="输入搜索内容，再点击查询用户或按回车">
<div class="email-table-wrap"><table id="email-user-table"><caption>用户目录</caption><thead><tr><th>账号</th><th>邮箱</th><th>用户 ID</th><th>状态</th><th>操作</th></tr></thead><tbody id="email-user-rows"></tbody></table></div>
<button id="email-users-prev" type="button" disabled>上一页</button><span id="email-users-page" role="status">尚未查询</span><button id="email-users-next" type="button" disabled>下一页</button>
<label for="email-admin-target">已选择用户</label><output id="email-admin-target">请从表格选择用户</output>
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
    try{await action();}catch(error){emailStatus.textContent=error.message;}finally{button.disabled=false;if(typeof refreshAdminActions==='function')refreshAdminActions();if(id==='email-users-prev')button.disabled=usersOffset===0;if(id==='email-users-next')button.disabled=usersOffset+20>=usersTotal;}
  });
  const emailValue=id=>byId(id).value;
  const centerOpen=document.createElement('button');centerOpen.type='button';centerOpen.className='email-account-launch';centerOpen.textContent='邮箱注册 / 找回密码 / 账号管理';
  byId('account').appendChild(centerOpen);
  queueMicrotask(()=>{
    const footer=byId('client-footer');
    if(footer){const link=document.createElement('button');link.type='button';link.className='email-footer-link';link.textContent='邮箱与账号管理';link.addEventListener('click',()=>centerOpen.click());footer.appendChild(link);}
  });
  centerOpen.addEventListener('click',async()=>{
    byId('email-account-center').showModal();byId('email-admin-panel').hidden=true;
    if(currentAccessToken){try{const own=await api('/api/v1/auth/email/identity');byId('email-address').value=own.email||'';byId('email-admin-panel').hidden=!own.administrator;if(own.administrator){usersQuery='';byId('email-user-search').value='';await loadUserDirectory(0);}}catch(e){emailStatus.textContent=e.message;}}
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
  let selectedAdminUser=null,usersOffset=0,usersTotal=0,usersQuery='',directoryGeneration=0;
  const adminActions=['email-admin-view','email-admin-disable','email-admin-enable','email-admin-delete'];
  const refreshAdminActions=()=>adminActions.forEach(id=>byId(id).disabled=!selectedAdminUser);
  const adminTarget=()=>{if(!selectedAdminUser)throw new Error('请先从用户表格选择用户');return encodeURIComponent(selectedAdminUser.id);};
  const selectAdminUser=user=>{selectedAdminUser=user;byId('email-admin-target').textContent=(user.username||'本地用户')+' · '+user.id;byId('email-admin-result').textContent='';byId('email-admin-offset').value='0';refreshAdminActions();};
  const loadUserDirectory=async(offset=0)=>{
    const generation=++directoryGeneration;
    byId('email-users-prev').disabled=true;byId('email-users-next').disabled=true;
    byId('email-user-rows').replaceChildren();byId('email-users-page').textContent='正在查询…';
    try{
      const data=await api('/api/v1/admin/accounts/directory?limit=20&offset='+offset+'&q='+encodeURIComponent(usersQuery));
      if(generation!==directoryGeneration)return;
      usersOffset=data.offset;usersTotal=data.total;
      for(const user of data.items){
        const row=document.createElement('tr');row.dataset.userId=user.id;
        row.setAttribute('aria-selected',String(selectedAdminUser?.id===user.id));
        for(const value of [user.username||'本地用户',user.email||'未绑定',user.id,(user.disabled?'已禁用':'正常')+(user.administrator?' / 管理员':'')]){const cell=document.createElement('td');cell.textContent=value;row.appendChild(cell);}
        const cell=document.createElement('td'),button=document.createElement('button');button.type='button';button.textContent='选择';button.setAttribute('aria-label','选择用户 '+(user.username||user.id));
        button.addEventListener('click',()=>{selectAdminUser(user);for(const item of byId('email-user-rows').children)item.setAttribute('aria-selected',String(item.dataset.userId===user.id));});
        cell.appendChild(button);row.appendChild(cell);byId('email-user-rows').appendChild(row);
      }
      byId('email-users-page').textContent=usersTotal?'第 '+(Math.floor(usersOffset/20)+1)+' 页 / 共 '+Math.ceil(usersTotal/20)+' 页，'+usersTotal+' 位用户':'没有匹配用户';
      byId('email-users-prev').disabled=usersOffset===0;byId('email-users-next').disabled=usersOffset+20>=usersTotal;
    }catch(error){if(generation===directoryGeneration)byId('email-users-page').textContent='查询失败，请重试';throw error;}
  };
  refreshAdminActions();
  byId('email-account-center').addEventListener('close',()=>{directoryGeneration++;selectedAdminUser=null;refreshAdminActions();byId('email-user-rows').replaceChildren();byId('email-admin-target').textContent='请从表格选择用户';byId('email-admin-panel').hidden=true;['email-current-password','email-new-password','email-code','email-delete-confirm'].forEach(id=>byId(id).value='');byId('email-admin-result').textContent='';emailChallenge=null;});
  const adminShow=data=>byId('email-admin-result').textContent=JSON.stringify(data,null,2);
  const adminOffset=()=>String(Math.max(0,Number(emailValue('email-admin-offset'))||0));
  emailRun('email-admin-list',async()=>{usersQuery=emailValue('email-user-search').trim();await loadUserDirectory(0);});
  emailRun('email-users-prev',async()=>loadUserDirectory(Math.max(0,usersOffset-20)));
  emailRun('email-users-next',async()=>loadUserDirectory(usersOffset+20));
  byId('email-user-search').addEventListener('keydown',event=>{if(event.key==='Enter'){event.preventDefault();byId('email-admin-list').click();}});
  emailRun('email-admin-audit',async()=>adminShow(await api('/api/v1/admin/accounts/audit/history?offset='+adminOffset())));
  emailRun('email-admin-view',async()=>adminShow(await api('/api/v1/admin/accounts/'+adminTarget()+'/data/'+emailValue('email-admin-kind')+'?offset='+adminOffset()+'&reason='+encodeURIComponent(emailValue('email-admin-reason')))));
  for(const [id,disabled] of [['email-admin-disable',true],['email-admin-enable',false]])emailRun(id,async()=>adminShow(await api('/api/v1/admin/accounts/'+adminTarget()+'/state',{method:'PATCH',body:JSON.stringify({disabled,reason:emailValue('email-admin-reason')})})));
  emailRun('email-admin-delete',async()=>{
    const target=adminTarget();if(prompt('永久删除 '+byId('email-admin-target').textContent+'：输入 DELETE 确认')!=='DELETE')return;
    adminShow(await api('/api/v1/admin/accounts/'+target+'/delete',{method:'POST',body:JSON.stringify({confirmation:'DELETE',reason:emailValue('email-admin-reason')})}));selectedAdminUser=null;refreshAdminActions();byId('email-admin-target').textContent='请从表格选择用户';await loadUserDirectory(usersOffset);
  });
'''
