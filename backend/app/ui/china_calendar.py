CHINA_CALENDAR_SCRIPT = r'''
  function installChinaCalendar(id) {
    const input = byId(id);
    if (!input || input.dataset.chinaCalendar) return;
    input.dataset.chinaCalendar = '1';
    if (!input.value) input.value = chinaTimeInputNow();
    const note = document.createElement('small');
    note.textContent = '北京时间 · 24小时制 · 年/月/日 时:分:秒，可直接修改或展开日历。';
    note.style.display = 'block'; input.after(note);
    const picker = document.createElement('details');
    const label = document.createElement('summary'); label.textContent = '选择日期和时间';
    const row = document.createElement('div');
    row.style.cssText = 'display:flex;flex-wrap:wrap;gap:6px;align-items:center;max-width:100%';
    const date = document.createElement('input'); date.type = 'date'; date.setAttribute('aria-label','北京时间日期');
    date.style.cssText = 'width:160px;max-width:100%';
    const parts = [23,59,59].map((max,index) => {
      const select = document.createElement('select');
      select.setAttribute('aria-label',['小时（24小时制）','分钟','秒'][index]); select.style.width = '70px';
      for(let value=0;value<=max;value++) {
        const option=document.createElement('option');option.value=String(value).padStart(2,'0');option.textContent=option.value;select.append(option);
      }
      return select;
    });
    const sync = () => {try {
      const iso=chinaTimeIso(input.value); const local=chinaTimeText(iso).replace(/年|月/g,'-').replace('日 ','T').replace('（北京时间）','');
      date.value=local.slice(0,10);parts.forEach((part,i)=>part.value=local.slice(11+i*3,13+i*3));
    } catch(_) {}};
    const update = () => {
      if(input.disabled || !date.value) return;
      input.value=chinaTimeText(chinaTimeIso(date.value+'T'+parts.map(x=>x.value).join(':'))).replace('（北京时间）','');
      input.dispatchEvent(new Event('input',{bubbles:true}));
    };
    const current=document.createElement('button');current.type='button';current.textContent='设为现在';
    current.addEventListener('click',()=>{if(!input.disabled){input.value=chinaTimeInputNow();sync();}});
    row.append(date,...parts,current);picker.append(label,row);note.after(picker);
    date.addEventListener('change',update);parts.forEach(x=>x.addEventListener('change',update));
    input.addEventListener('change',sync);picker.addEventListener('toggle',sync);sync();
  }
  installChinaCalendar('message-sent-at');
  installChinaCalendar('client-media-sent-at');
'''
