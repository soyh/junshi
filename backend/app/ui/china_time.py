CHINA_TIME_SCRIPT = r'''
  // Display in Beijing time, independently of the device timezone/locale.
  function chinaTimeText(value, precision = 'second') {
    if (!value) return '时间未知';
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return '时间无效';
    const parts = new Intl.DateTimeFormat('en-CA', {
      timeZone: 'Asia/Shanghai', year: 'numeric', month: '2-digit', day: '2-digit',
      hour: '2-digit', minute: '2-digit', second: '2-digit', hourCycle: 'h23',
    }).formatToParts(date);
    const fields = Object.fromEntries(parts.map(part => [part.type, part.value]));
    return `${fields.year}年${fields.month}月${fields.day}日 ${fields.hour}:${fields.minute}`
      + (precision === 'minute' ? '' : `:${fields.second}`) + '（北京时间）';
  }

  function chinaTimeIso(value) {
    const text = String(value || '').trim().replace('（北京时间）', '')
      .replace(/年|月/g, '-').replace(/日\s*/, 'T').replace(/\s+/, 'T');
    const match = text.match(/^(\d{4})-(\d{1,2})-(\d{1,2})T(\d{1,2}):(\d{2})(?::(\d{2})(\.\d{1,3})?)?(Z|[+-]\d{2}:\d{2})?$/i);
    if (!match) throw new Error('时间格式无效，请使用 YYYY年MM月DD日 HH:mm:ss（24小时制）');
    const pad = v => String(v).padStart(2, '0');
    const wall = `${match[1]}-${pad(match[2])}-${pad(match[3])}T${pad(match[4])}:${match[5]}:${match[6] || '00'}`;
    const check = new Date(wall + 'Z');
    if (Number.isNaN(check.getTime()) || check.toISOString().slice(0,19) !== wall) {
      throw new Error('日期或时间不存在，请检查年月日和24小时制时间');
    }
    const result = wall + (match[7] || '') + (match[8] || '+08:00');
    if (Number.isNaN(new Date(result).getTime())) throw new Error('时区格式无效');
    return result;
  }

  function chinaTimeInputNow() {
    return chinaTimeText(new Date().toISOString()).replace('（北京时间）', '');
  }
'''
