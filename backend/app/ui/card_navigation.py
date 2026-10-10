CARD_NAVIGATION_STYLE = r'''
  body[data-client-view]>.grid,body[data-client-view] #guided-workflow,body[data-client-view] #client-experience-shell,body[data-client-view] #client-person-stage{min-width:0!important;max-width:100%;box-sizing:border-box}
  body[data-client-view] {max-width:1480px!important;margin:0 auto!important;min-height:100dvh;padding:24px 24px 0!important}
  body[data-client-view="auth"],body[data-client-view="people"] {background:radial-gradient(ellipse at 50% 38%,#1b3548 0,#111e2c 48%,#0a121e 100%)!important;color:#eef5fa}
  body[data-client-view="auth"]>.grid,body:not([data-client-view="auth"])>#client-auth-screen{display:none!important}
  #client-auth-screen{max-width:440px;margin:10vh auto 40px;padding:28px;border:1px solid #426073;border-radius:24px;background:#f8fbff;color:#182d42;box-shadow:0 24px 90px #0005}
  #client-auth-screen h1{font-size:28px;margin:8px 0}#client-auth-screen .auth-intro{color:#5e7181;line-height:1.7}
  #client-auth-screen #account{border:0;padding:0;background:transparent;box-shadow:none;display:block!important}
  #client-auth-screen #account>.note,#client-auth-screen #account>legend{display:none}
  #client-auth-screen #login{background:#126976;color:white;border:0;border-radius:10px;min-width:120px}
  #client-auth-screen #register{background:transparent;color:#176979;border:1px solid #90b5bf;border-radius:10px}
  body[data-client-view="people"] #client-conversation-stage,body[data-client-view="people"] #client-results-stage,
  body[data-client-view="people"] #person-memory-panel,body[data-client-view="people"] #client-workbar{display:none!important}
  body[data-client-view="people"] .client-topbar{justify-content:center;text-align:center;padding-top:36px}
  body[data-client-view="people"] .client-brand h1{color:#e1f7f6;letter-spacing:.12em;font-size:24px}
  body[data-client-view="people"] .client-brand p{color:#90aebc;margin-top:12px}
  body[data-client-view="people"] #client-person-stage{background:transparent;border:0;box-shadow:none;backdrop-filter:none;padding:20px 0;margin-top:35px}
  body[data-client-view="people"] #client-person-stage::before{display:none}
  body[data-client-view="people"] #client-person-stage>.client-stage-header{display:none}
  body[data-client-view="people"] #client-person-deck{display:flex!important;align-items:center;gap:24px;overflow-x:auto;scroll-snap-type:x mandatory;padding:28px 24px 42px;min-height:390px;scrollbar-width:thin}
  body[data-client-view="people"] .client-person-card{flex:0 0 250px;min-height:350px;scroll-snap-align:center;animation:none;transition:transform .3s}
  body[data-client-view="people"] .client-person-card:first-child{margin-left:auto}
  body[data-client-view="people"] .client-person-card:last-child{margin-right:auto}
  body[data-client-view="people"] .client-person-card.is-selected{transform:translateY(-12px)}
  body[data-client-view="people"] .client-person-card.is-flipped{flex-basis:min(540px,85vw);min-height:650px}
  body[data-client-view="people"] .client-card-front{border-radius:18px;background:linear-gradient(150deg,#203b4d,#142334)!important;border-color:#416474!important;box-shadow:0 14px 28px #0004;color:#e4f6f9!important}
  body[data-client-view="people"] .is-selected .client-card-front{border-color:#76dcd3!important;box-shadow:0 0 25px #48cec326}
  body[data-client-view="people"] .client-card-name{color:#e4f6f9;font-size:20px;overflow-wrap:anywhere}
  body[data-client-view="people"] .client-card-subtitle{color:#a6bac8}
  body[data-client-view="people"] .client-card-avatar{background:linear-gradient(135deg,#2b7e86,#253e63);border:1px solid #70b8bc;border-radius:18px}
  body[data-client-view="people"] .client-card-rarity{background:#10232c;color:#8dc9c9;border-color:#416474}
  #client-deck-controls{display:flex;justify-content:center;align-items:center;gap:20px;color:#91aeba}
  #client-deck-controls button{margin:0;border:1px solid #4d9198;color:#b3e5e3;background:transparent;border-radius:8px;padding:10px 20px}
  #client-navigation-status{text-align:center;min-height:24px;color:#bde1df;overflow-wrap:anywhere}
  .client-person-card.is-entering .client-card-inner{transform:rotateY(180deg)!important}
  #client-footer{display:flex;justify-content:center;align-items:center;flex-wrap:wrap;gap:14px;margin:48px 0 0;padding:22px 0;color:#91a7b4;font-size:13px}
  #client-footer > #logout,#client-footer #guided-settings>summary{font-size:13px!important;background:transparent!important;box-shadow:none!important;border:0!important;color:inherit!important;margin:0;padding:8px!important}
  #client-footer #client-settings-host{color:inherit}
  #client-footer #guided-settings-content{color:#183149}
  #client-workbar{display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:12px;margin:0 0 8px}
  #client-workbar h2{margin:0;font-size:22px;overflow-wrap:anywhere}
  body[data-client-view="person"] .client-topbar,body[data-client-view="person"] #client-deck-controls{display:none!important}
  body[data-client-view="person"] #client-person-stage>.client-stage-header{display:none}
  body[data-client-view="person"] #client-person-deck{display:none!important}
  body[data-client-view="person"][data-profile-edit="true"] #client-person-deck{display:block!important}
  body[data-client-view="person"] .client-person-card{display:none;animation:none!important;min-height:0!important}
  body[data-client-view="person"] .client-person-card.is-selected{display:block}
  body[data-client-view="person"] .client-card-inner,body[data-client-view="person"] .client-card-back{position:static;transform:none!important}
  body[data-client-view="person"] .client-card-front{display:none!important}
  body[data-client-view="person"] #client-navigation-status{color:#536879}
  #client-back-people:focus-visible,#client-footer button:focus-visible,.client-card-front:focus-visible{outline:3px solid #4cbac4;outline-offset:4px}
  @media(max-width:600px){body[data-client-view]{padding:14px 12px 0!important}#client-auth-screen{margin:5vh auto;padding:22px}body[data-client-view="people"] .client-topbar{padding-top:20px}body[data-client-view="people"] #client-person-stage{margin-top:0}body[data-client-view="people"] #client-person-deck{padding:22px 18px 30px;gap:16px}body[data-client-view="people"] .client-person-card{flex-basis:78vw;min-height:330px}#client-footer{margin-top:20px}#client-workbar h2{font-size:18px}}
  @media(prefers-reduced-motion:reduce){.client-person-card,.client-card-inner{transition:none!important;animation:none!important}}
'''

CARD_NAVIGATION_SCRIPT = r'''
  const navShell=byId('client-experience-shell'),navDeck=byId('client-person-deck');
  const navAuth=document.createElement('section');navAuth.id='client-auth-screen';
  const navTitle=clientEl('h1','','AI 恋爱军师'),navIntro=clientEl('p','auth-intro','从一段真实的对话开始。登录或注册，进入你的人物卡组。');
  navAuth.append(navTitle,navIntro,byId('account'));document.body.prepend(navAuth);
  const navFooter=clientEl('footer');navFooter.id='client-footer';
  navFooter.append(byId('client-settings-host'),byId('logout'));navShell.append(navFooter);
  const navSettings=byId('guided-settings');
  navSettings.querySelector('summary').textContent='设置 · 账号安全 / 模型设置 / 参考资料';
  // Account entry now lives on the authentication screen. Rebuild the small
  // tab navigation so keyboard traversal cannot select its former empty panel.
  const navTabs=Array.from(byId('guided-settings-tabs').children).filter(tab=>{
    if(tab.getAttribute('aria-controls')==='account'){tab.remove();return false;}return true;
  }).map(tab=>{const replacement=tab.cloneNode(true);tab.replaceWith(replacement);return replacement;});
  function navActivateSettings(index){navTabs.forEach((tab,i)=>{tab.setAttribute('aria-selected',String(i===index));tab.tabIndex=i===index?0:-1;byId(tab.getAttribute('aria-controls')).hidden=i!==index;});}
  navTabs.forEach((tab,index)=>{
    tab.addEventListener('click',()=>navActivateSettings(index));
    tab.addEventListener('keydown',event=>{
      if(!['ArrowLeft','ArrowRight','Home','End'].includes(event.key))return;
      event.preventDefault();const next=event.key==='Home'?0:event.key==='End'?navTabs.length-1:(index+(event.key==='ArrowLeft'?-1:1)+navTabs.length)%navTabs.length;
      navActivateSettings(next);navTabs[next].focus();
    });
  });
  navActivateSettings(Math.max(0,navTabs.findIndex(tab=>tab.textContent==='账号安全')));
  const navControls=clientEl('div');navControls.id='client-deck-controls';
  const navPrev=clientEl('button','','← 上一个'),navNext=clientEl('button','','下一个 →'),navCount=clientEl('span');
  navPrev.type=navNext.type='button';navControls.append(navPrev,navCount,navNext);byId('client-person-stage').append(navControls);
  const navStatus=clientEl('p');navStatus.id='client-navigation-status';navStatus.setAttribute('role','status');
  byId('client-person-stage').append(navStatus);
  const navWorkbar=clientEl('div');navWorkbar.id='client-workbar';
  const navBack=clientEl('button','','← 返回人物卡组');navBack.id='client-back-people';navBack.type='button';
  const navName=clientEl('h2');navName.tabIndex=-1;
  const navEdit=clientEl('button','','人物资料与关系');navEdit.type='button';
  navWorkbar.append(navBack,navName,navEdit);navShell.prepend(navWorkbar);
  document.querySelector('.client-brand p').textContent='选择一位人物，继续你们的故事。';
  let navEpoch=0,navEntering=false;
  function navShow(view,push=false){
    if(!currentAccessToken)view='auth';
    if(view==='person' && !selectedPersonId)view='people';
    document.body.dataset.clientView=view;document.body.dataset.profileEdit='false';
    navSettings.open=false;navStatus.textContent='';
    navName.textContent=byId('person-select').selectedOptions[0]?.textContent || '人物工作区';
    if(push)history.pushState({clientView:view},'',view==='person'?'#person':'#people');
    if(view==='person')navName.focus({preventScroll:true});
    window.scrollTo({top:0,behavior:'instant'});
  }
  function navDecorate(){
    const cards=Array.from(navDeck.querySelectorAll('.client-person-card'));
    navCount.textContent=`${cards.filter(c=>c.dataset.personId).length} 位人物`;
    cards.forEach(card=>{const subtitle=card.querySelector('.client-card-subtitle');if(card.dataset.personId && subtitle)subtitle.textContent='点击翻转，进入人物工作区';});
  }
  const navBaseSelect=clientSelectPerson;
  clientSelectPerson=async function(id){await navBaseSelect(id);if(!navEntering && currentAccessToken)navShow('person',true);};
  navDeck.addEventListener('click',async event=>{
    const front=event.target.closest('.client-card-front'),card=front?.closest('[data-person-id]');
    if(!card)return;event.preventDefault();event.stopImmediatePropagation();
    if(navEntering || !currentAccessToken)return;
    const epoch=++navEpoch;navEntering=true;const id=card.dataset.personId;
    navStatus.textContent='正在进入人物…';card.classList.add('is-entering');
    try{
      await clientSelectPerson(id);
      await Promise.all([clientPopulatePersonBack(card,id),new Promise(resolve=>setTimeout(resolve,matchMedia('(prefers-reduced-motion: reduce)').matches?0:480))]);
      if(epoch!==navEpoch || !currentAccessToken)return;
      navShow('person',true);
    }catch(_){if(epoch===navEpoch)navStatus.textContent='人物暂时无法打开，请重试。';}
    finally{card.classList.remove('is-entering');if(epoch===navEpoch)navEntering=false;}
  },true);
  navBack.addEventListener('click',()=>{navEpoch++;navEntering=false;navShow('people',true);navDeck.querySelector('.is-selected .client-card-front')?.focus({preventScroll:true});});
  navEdit.addEventListener('click',async()=>{
    const show=document.body.dataset.profileEdit!=='true';document.body.dataset.profileEdit=String(show);
    if(show){const card=Array.from(navDeck.children).find(c=>c.dataset.personId===selectedPersonId);if(card)await clientPopulatePersonBack(card,selectedPersonId);}
  });
  navPrev.addEventListener('click',()=>navDeck.scrollBy({left:-280,behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'instant':'smooth'}));
  navNext.addEventListener('click',()=>navDeck.scrollBy({left:280,behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'instant':'smooth'}));
  new MutationObserver(navDecorate).observe(navDeck,{childList:true});navDecorate();
  const navBaseEstablish=establishSession;
  establishSession=function(...args){navBaseEstablish(...args);navEpoch++;navEntering=false;navShow('people');history.replaceState({clientView:'people'},'','#people');};
  const navBaseClear=clearSession;
  clearSession=function(...args){navEpoch++;navEntering=false;navBaseClear(...args);navShow('auth');history.replaceState(null,'',location.pathname);};
  window.addEventListener('popstate',event=>{navEpoch++;navEntering=false;navShow(event.state?.clientView || 'people');});
  byId('person-select').addEventListener('change',()=>{if(document.body.dataset.clientView==='person')navName.textContent=byId('person-select').selectedOptions[0]?.textContent || '人物工作区';});
  byId('password').addEventListener('keydown',event=>{if(event.key==='Enter'){event.preventDefault();byId('login').click();}});
  navShow('auth');
'''
