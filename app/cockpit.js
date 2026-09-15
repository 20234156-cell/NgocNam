'use strict';
const $ = id => document.getElementById(id);
const state = {user:null, config:null, queue:[], selected:new Set(), assessment:null, decision:null,
  signature:null, decisionKey:null, coreKey:null, busy:new Set(), generation:0, sessionGeneration:0, stressGeneration:0};
const money = value => Number(value).toLocaleString('vi-VN') + ' ₫';
const amountDigits = ['không','một','hai','ba','bốn','năm','sáu','bảy','tám','chín'];
function amountInWords(value){
  if(value===0)return 'Không đồng';
  const absolute=Math.abs(value);
  const decimal=new Intl.NumberFormat('en-US',{useGrouping:false,maximumFractionDigits:20}).format(absolute).split('.')[1];
  let whole=Math.trunc(absolute);
  const groups=[];
  while(whole>0){groups.push(whole%1000);whole=Math.floor(whole/1000);}
  const units=['','nghìn','triệu','tỷ','nghìn tỷ','triệu tỷ'];
  const words=[];
  for(let i=groups.length-1;i>=0;i--){
    if(!groups[i])continue;
    const hundred=Math.floor(groups[i]/100),ten=Math.floor(groups[i]%100/10),one=groups[i]%10;
    const full=i<groups.length-1;
    if(hundred||full)words.push(amountDigits[hundred],'trăm');
    if(ten>1)words.push(amountDigits[ten],'mươi');
    else if(ten===1)words.push('mười');
    else if(one&&(hundred||full))words.push('lẻ');
    if(one)words.push(one===1&&ten>1?'mốt':one===5&&ten>0?'lăm':amountDigits[one]);
    if(units[i])words.push(units[i]);
  }
  if(!groups.length)words.push('không');
  if(decimal)words.push('phẩy',...decimal.split('').map(d=>amountDigits[Number(d)]));
  if(value<0)words.unshift('âm');
  const text=words.join(' ')+' đồng';
  return text.charAt(0).toUpperCase()+text.slice(1);
}
function updateAmountHint(input){
  const hint=$(input.id+'-amount-hint');
  if(!hint)return;
  hint.replaceChildren();hint.className='amount-hint';
  if(input.value===''&&!input.validity.badInput){hint.hidden=true;return;}
  hint.hidden=false;
  const value=Number(input.value);
  if(input.validity.badInput||!Number.isFinite(value)||Math.abs(value)>Number.MAX_SAFE_INTEGER){
    hint.textContent='Vui lòng nhập số tiền hợp lệ.';hint.classList.add('error');return;
  }
  hint.append(node('strong',value.toLocaleString('vi-VN',{maximumFractionDigits:20})+' VNĐ'),node('span',amountInWords(value)));
  if(input.validity.rangeUnderflow||input.validity.rangeOverflow){
    hint.classList.add('error');
    hint.append(node('span',`Ngoài khoảng cho phép: ${Number(input.min).toLocaleString('vi-VN')} – ${Number(input.max).toLocaleString('vi-VN')} VNĐ.`));
  }
}
function refreshAmountHints(){
  document.querySelectorAll('#applicationFields input[name$="_vnd"]').forEach(updateAmountHint);
}
const percent = value => Number(value).toFixed(2) + '%';
const roleName = role => ({'Loan Officer':'Thẩm định viên','Risk Manager':'Quản trị rủi ro','Committee Chair':'Chủ tịch hội đồng'}[role] || role);
function node(tag, text, className) { const e = document.createElement(tag); if(text !== undefined)e.textContent=text; if(className)e.className=className; return e; }
function message(text, error=false){$('notification').textContent=text;$('notification').className=error?'error':'';$('notification').hidden=false;}
function showLogin(){
  state.sessionGeneration++;
  state.generation++; state.user=null;state.assessment=null;state.decision=null;state.signature=null;state.decisionKey=null;state.coreKey=null;
  $('applicationForm').reset();$('committeeForm').reset();$('coreForm').reset();$('lookupForm').reset();
  ['auditRows','batchRows','shapRows','waterfall','stressOutput','caseRows','historyRows'].forEach(id=>$(id).replaceChildren());
  savedView.generation++;savedView.historyGeneration++;savedView.offset=0;savedView.caseId=null;
  $('caseSearch').value='';$('caseSummary').textContent='';$('caseHistory').hidden=true;
  ['resultCard','shapCard','savedDecision','coreCard','batchResults','notification'].forEach(id=>$(id).hidden=true);
  $('workspace').hidden=true;$('loginView').hidden=false;$('logoutButton').hidden=true;
  $('currentUser').textContent='';$('connectionStatus').textContent='Chưa đăng nhập';$('emptyResult').hidden=false;
}
async function api(path, body, method){
  const session=state.sessionGeneration;
  const options={method:method || (body===undefined?'GET':'POST'), credentials:'same-origin', headers:{'X-Credit-Client':'cockpit'}};
  if(body!==undefined){options.headers['Content-Type']='application/json';options.body=JSON.stringify(body);}
  const response=await fetch(path,options);
  if(session!==state.sessionGeneration)throw new Error('Phiên làm việc đã thay đổi. Hãy thực hiện lại thao tác.');
  if(!response.ok){
    const data=await response.json().catch(()=>({}));
    if(response.status===401 && path!=='/auth/login')showLogin();
    throw new Error(data.message || (typeof data.detail==='string'?data.detail:'Yêu cầu không hợp lệ. Kiểm tra lại các trường dữ liệu.'));
  }
  return response;
}
async function json(path,body){return (await api(path,body)).json();}
async function action(id,fn){
  if(state.busy.has(id))return;
  state.busy.add(id);$(id).disabled=true;
  try{await fn();}catch(error){message(error.message || 'Không kết nối được máy chủ. Chưa có kết quả được xác nhận.',true);}
  finally{state.busy.delete(id);$(id).disabled=false;syncPermissions();}
}
function syncPermissions(){
  if(!state.user)return;
  const role=state.user.role;
  document.querySelectorAll('[data-role="risk"]').forEach(e=>e.hidden=role!=='Risk Manager');
  document.querySelectorAll('[data-role="audit"]').forEach(e=>e.hidden=role==='Loan Officer');
  let menuNumber=0;
  document.querySelectorAll('nav [data-panel]').forEach(e=>{
    if(!e.hidden)e.firstChild.textContent=String(++menuNumber).padStart(2,'0')+' ';
  });
  $('thresholdPolicy').disabled=role!=='Risk Manager';
  $('saveDecision').disabled=role!=='Committee Chair'||!state.assessment||!!state.decision||state.busy.has('saveDecision');
  $('simulateCore').disabled=role!=='Committee Chair'||!state.decision||state.decision.final_decision!=='PHÊ DUYỆT'||state.busy.has('simulateCore');
}
function panel(name){
  if(name==='stress' && state.user?.role!=='Risk Manager')return;
  if(name==='audit' && state.user?.role==='Loan Officer')return;
  document.querySelectorAll('.panel').forEach(e=>e.hidden=e.id!=='panel-'+name);
  document.querySelectorAll('[data-panel]').forEach(e=>e.classList.toggle('active',e.dataset.panel===name));
  if(name==='audit')loadAudit();
  if(name==='cases')loadCases().catch(e=>message(e.message,true));
}
function buildFields(){
  const container=$('applicationFields');container.replaceChildren();
  const groups=[['Khách hàng',['tuoi','gioi_tinh','tinh_trang_hon_nhan','so_nguoi_phu_thuoc','trinh_do_hoc_van','loai_hinh_nghe_nghiep','khu_vuc_sinh_song']],
    ['Năng lực tài chính',['thu_nhap_thang_vnd','thu_nhap_nguoi_dong_vay_vnd','gia_tri_tai_san_dam_bao_vnd','so_tien_vay_vnd','thoi_han_vay_thang','muc_dich_vay']],
    ['Lịch sử tín dụng',['diem_tin_dung_cic','nhom_no_cic','so_lan_tre_han_2_nam','so_khoan_vay_hien_tai','lich_su_no_xau','ty_le_dti']]];
  groups.forEach(([title,keys])=>{
    const section=node('fieldset');section.append(node('legend',title));const grid=node('div',undefined,'fields');
    keys.forEach(key=>{
      const cfg=state.config.fields[key];const label=node('label',cfg.description);
      const input=node(cfg.options?'select':'input');input.id=key;input.name=key;input.required=true;
      if(cfg.options){input.append(new Option('Chọn…',''));cfg.options.forEach(v=>input.append(new Option(v,v)));}
      else{input.type='number';input.min=cfg.min;input.max=cfg.max;input.step=Number.isInteger(cfg.default)&&!key.includes('vnd')&&key!=='ty_le_dti'?'1':'any';input.placeholder=cfg.min+' – '+cfg.max;}
      label.append(input);
      if(key.endsWith('_vnd')){
        input.placeholder=Number(cfg.min).toLocaleString('vi-VN')+' – '+Number(cfg.max).toLocaleString('vi-VN');
        const hint=node('span',undefined,'amount-hint');hint.id=key+'-amount-hint';hint.hidden=true;
        hint.setAttribute('aria-live','polite');hint.setAttribute('aria-atomic','true');
        input.setAttribute('aria-describedby',hint.id);input.addEventListener('input',()=>updateAmountHint(input));
        label.append(hint);
      }
      grid.append(label);
    });section.append(grid);container.append(section);
  });
  $('thresholdPolicy').options[0].textContent=`Chính thức (${state.config.optimal_threshold})`;
  $('thresholdPolicy').options[1].textContent=`So sánh (${state.config.default_threshold})`;
}
function application(){
  const payload={ma_ho_so:$('ma_ho_so').value.trim(),ho_ten:$('ho_ten').value.trim()};
  Object.entries(state.config.fields).forEach(([key,cfg])=>{const v=$(key).value;payload[key]=cfg.options?v:(v===''?null:Number(v));});
  return payload;
}
function signature(){return JSON.stringify({application:application(),threshold:$('thresholdPolicy').value});}
function invalidate(){
  state.generation++;state.assessment=null;state.decision=null;state.signature=null;state.decisionKey=null;state.coreKey=null;
  state.stressGeneration++;$('stressOutput').hidden=true;
  $('resultCard').hidden=true;$('shapCard').hidden=true;$('emptyResult').hidden=false;$('savedDecision').hidden=true;$('coreCard').hidden=true;
  $('dirtyNotice').textContent='Dữ liệu đã thay đổi. Cần chạy thẩm định để nhận kết quả mới.';
  $('committeeContext').textContent='Chưa có kết quả hiện hành. Hãy thẩm định hoặc tra cứu hồ sơ đã lưu.';
  $('finalDecision').value='';$('approvedLimit').value='';syncPermissions();
}
function fillProfile(profile){
  invalidate();$('applicationForm').reset();
  for(const key of ['ma_ho_so','ho_ten',...Object.keys(state.config.fields)])if($(key))$(key).value=profile[key] ?? '';
  $('thresholdPolicy').value='optimal';$('lookupCase').value=profile.ma_ho_so||'';
  refreshAmountHints();
}
function renderResult(result){
  state.assessment=result;state.signature=signature();state.decision=null;state.decisionKey=null;state.coreKey=null;
  $('emptyResult').hidden=true;$('resultCard').hidden=false;$('shapCard').hidden=false;
  $('decisionLabel').textContent=result.ket_qua;$('decisionLabel').className='decision '+(result.ma_ket_qua?'good':'error');
  $('probability').textContent=percent(result.xac_suat_phe_duyet);$('appliedThreshold').textContent=result.nguong_quyet_dinh.toFixed(2);
  $('riskTier').textContent=result.muc_do_rui_ro;$('recommendation').textContent=result.khuyen_nghi_nghiep_vu;
  $('policyReason').hidden=!result.hard_rule_violated;$('policyReason').textContent=result.policy_reason||'';
  $('runBadge').textContent=`Run #${result.run_number}${result.is_cached_run?' · kết quả đã lưu':''}`;
  $('requestId').textContent=result.request_id;$('assessmentTime').textContent=new Date(result.assessed_at).toLocaleString('vi-VN');
  $('dirtyNotice').textContent='Kết quả khớp với hồ sơ đang hiển thị.';
  $('committeeContext').textContent=`${result.ma_ho_so} · Run #${result.run_number} · ${result.ket_qua} · Ngưỡng ${result.nguong_quyet_dinh}`;
  $('approvedLimit').max=result.so_tien_vay_vnd;$('approvedLimit').value='';$('finalDecision').value='';
  $('finalDecision').querySelector('option[value="PHÊ DUYỆT"]').disabled=!!result.hard_rule_violated||!result.ma_ket_qua||result.nguong_quyet_dinh!==state.config.optimal_threshold;
  $('lookupCase').value=result.ma_ho_so;renderShap(result);syncPermissions();
}
function renderShap(result){
  const factors=result.shap_factors;
  const base=result.shap_base_value,total=result.fx_log_odds;
  const sum=factors.reduce((v,f)=>v+f.shap_value,base);
  if(Math.abs(sum-total)>1e-4||Math.abs(1/(1+Math.exp(-total))-result.prob_from_log_odds)>1e-5){
    $('waterfall').replaceChildren(node('p','Giải thích chưa khớp dữ liệu model. Không hiển thị biểu đồ.','error'));return;
  }
  $('shapMath').textContent=`f(x) = ${base.toFixed(6)} + ${(total-base).toFixed(6)} = ${total.toFixed(6)} log-odds. P = sigmoid(f(x)) = ${percent(result.prob_from_log_odds*100)}.`;
  const tbody=$('shapRows');tbody.replaceChildren();
  factors.forEach(f=>{const row=node('tr');row.append(node('td',f.dac_trung),node('td',(f.shap_value>=0?'+':'')+f.shap_value.toFixed(6),f.shap_value>=0?'good':'error'));tbody.append(row);});
  const top=factors.slice(0,8).map(f=>({name:f.dac_trung,value:f.shap_value}));
  const other=factors.slice(8).reduce((sum,f)=>sum+f.shap_value,0);if(factors.length>8)top.push({name:`${factors.length-8} yếu tố còn lại`,value:other});
  let running=base;const bars=[{name:'Giá trị nền E[f(X)]',start:0,end:base,total:true}];
  top.forEach(f=>{bars.push({name:f.name,start:running,end:running+f.value,value:f.value});running+=f.value;});
  bars.push({name:'Tổng f(x)',start:0,end:total,total:true});
  const min=Math.min(0,...bars.flatMap(b=>[b.start,b.end])),max=Math.max(0,...bars.flatMap(b=>[b.start,b.end]));
  const scale=v=>205+(v-min)/(max-min||1)*220;const ns='http://www.w3.org/2000/svg';
  const svg=document.createElementNS(ns,'svg');svg.setAttribute('viewBox',`0 0 520 ${bars.length*32+18}`);svg.setAttribute('role','img');svg.setAttribute('aria-label','Biểu đồ Waterfall SHAP: cộng dồn đóng góp từ giá trị nền đến tổng log-odds');
  function shape(tag,attrs,text){const e=document.createElementNS(ns,tag);Object.entries(attrs).forEach(([k,v])=>e.setAttribute(k,v));if(text!==undefined)e.textContent=text;svg.append(e);return e;}
  bars.forEach((b,i)=>{const y=i*32+8;const title=b.name.length>27?b.name.slice(0,25)+'…':b.name;shape('text',{x:0,y:y+14},title);
    const rect=shape('rect',{x:scale(Math.min(b.start,b.end)),y,width:Math.max(.5,Math.abs(scale(b.end)-scale(b.start))),height:21,rx:2,class:b.total?'total':b.value>=0?'positive':'negative'});
    const tooltip=document.createElementNS(ns,'title');tooltip.textContent=b.name;rect.append(tooltip);
    shape('text',{x:440,y:y+14},(b.total?b.end:b.value).toFixed(3));
    if(i<bars.length-1)shape('line',{x1:scale(b.end),x2:scale(b.end),y1:y+21,y2:y+32,class:'connector'});
  });$('waterfall').replaceChildren(svg);
}
async function initialize(user){
  state.sessionGeneration++;
  state.user=user;state.config=await json('/config');state.queue=await json('/queue');state.selected.clear();
  buildFields();$('currentUser').textContent=`${user.username} · ${roleName(user.role)}`;$('modelName').textContent=`XGBoost-CreditRisk-v${state.config.model_version}`;
  $('connectionStatus').textContent=state.config.model_loaded?'Model đã xác minh':'Model chưa sẵn sàng';
  $('loginView').hidden=true;$('workspace').hidden=false;$('logoutButton').hidden=false;
  $('password').value='';renderQueue();syncPermissions();panel('assessment');
}
function renderQueue(){
  const q=$('queueSearch').value.toLocaleLowerCase('vi-VN');
  const visible=state.queue.filter(p=>(p.ma_ho_so+' '+p.ho_ten).toLocaleLowerCase('vi-VN').includes(q));
  const tbody=$('queueRows');tbody.replaceChildren();
  visible.forEach(p=>{
    const row=node('tr'),select=node('input');select.type='checkbox';select.checked=state.selected.has(p.ma_ho_so);select.setAttribute('aria-label','Chọn '+p.ma_ho_so);
    select.addEventListener('change',()=>{if(select.checked)state.selected.add(p.ma_ho_so);else state.selected.delete(p.ma_ho_so);renderQueue();});
    const check=node('td');check.append(select);const identity=node('td');identity.append(node('strong',p.ma_ho_so),node('small',p.ho_ten));
    const open=node('button','Mở','quiet');open.addEventListener('click',()=>{fillProfile(p);panel('assessment');});const controls=node('td');controls.append(open);
    row.append(check,identity,node('td',money(p.so_tien_vay_vnd)),node('td',p.diem_tin_dung_cic+' · '+p.nhom_no_cic),controls);tbody.append(row);
  });
  $('selectAll').checked=visible.length>0&&visible.every(p=>state.selected.has(p.ma_ho_so));
  $('selectAll').indeterminate=visible.some(p=>state.selected.has(p.ma_ho_so))&&!$('selectAll').checked;
  $('batchButton').textContent=`Thẩm định hồ sơ đã chọn (${state.selected.size})`;
}
const savedView={offset:0, generation:0, historyGeneration:0, caseId:null, historyOffset:0};
async function loadCases(){
  const generation=++savedView.generation;
  const data=await json('/cases?'+new URLSearchParams({q:$('caseSearch').value.trim(),offset:savedView.offset}));
  if(generation!==savedView.generation||!state.user)return;
  $('caseSummary').textContent=data.total?`${data.total} hồ sơ · Hiển thị ${data.offset+1}–${Math.min(data.offset+data.limit,data.total)}`:'Chưa có hồ sơ phù hợp.';
  $('casesPrev').disabled=data.offset===0;$('casesNext').disabled=data.offset+data.limit>=data.total;
  const body=$('caseRows');body.replaceChildren();
  data.items.forEach(item=>{
    const row=node('tr'),controls=node('td');
    const history=node('button','Lịch sử / Chi tiết','quiet');
    history.addEventListener('click',()=>{savedView.caseId=item.ma_ho_so;savedView.historyOffset=0;loadHistory().catch(e=>message(e.message,true));});
    const open=node('button','Mở kết quả mới nhất','quiet');
    open.addEventListener('click',()=>{$('lookupCase').value=item.ma_ho_so;panel('committee');$('lookupForm').requestSubmit($('lookupForm').querySelector('button'));});
    controls.append(history,open);
    row.append(node('td',item.ma_ho_so),node('td',item.run_number),node('td',new Date(item.assessed_at).toLocaleString('vi-VN')),node('td',money(item.so_tien_vay_vnd)),node('td',percent(item.xac_suat_phe_duyet)),node('td',item.ket_qua),node('td',item.committee_decision||'Chưa có quyết định'),controls);body.append(row);
  });
}
async function loadHistory(){
  const generation=++savedView.historyGeneration,caseId=savedView.caseId;
  $('caseHistory').hidden=true;
  const data=await json('/cases/'+encodeURIComponent(caseId)+'/history?offset='+savedView.historyOffset);
  if(generation!==savedView.historyGeneration||!state.user)return;
  $('historyTitle').textContent=`${caseId} · ${data.total} lần thẩm định`;
  $('historyPrev').disabled=data.offset===0;$('historyNext').disabled=data.offset+data.limit>=data.total;
  const body=$('historyRows');body.replaceChildren();
  data.items.forEach(({assessment:a,committee:c})=>{
    const details=node('details'),summary=node('summary',`Lần ${a.run_number} · ${new Date(a.assessed_at).toLocaleString('vi-VN')} · ${a.ket_qua} · ${percent(a.xac_suat_phe_duyet)}`);
    details.append(summary,node('p',`Người thẩm định: ${a.created_by} · Model ${a.model_version} · Ngưỡng ${a.nguong_quyet_dinh}`),node('p',c?`Hội đồng: ${c.final_decision} · ${c.officer_id} · ${money(c.approved_limit_vnd)}`:'Chưa có quyết định hội đồng cho lần này.'));
    const table=node('table'),tbody=node('tbody');
    Object.entries(a.application_snapshot||{}).forEach(([key,value])=>{const row=node('tr');row.append(node('th',state.config.fields[key]?.description||key),node('td',key.endsWith('_vnd')?money(value):String(value)));tbody.append(row);});
    table.append(tbody);const wrap=node('div',undefined,'table-scroll');wrap.append(table);details.append(wrap);
    details.append(node('p',a.policy_reason||a.khuyen_nghi_nghiep_vu));
    const factors=node('ul');(a.shap_factors||[]).forEach(f=>factors.append(node('li',`${f.dac_trung}: ${f.shap_value.toFixed(6)} log-odds`)));
    const explanation=node('details');explanation.append(node('summary','Xem đóng góp SHAP'),factors);details.append(explanation);body.append(details);
  });
  $('caseHistory').hidden=false;
}
$('caseSearchForm').addEventListener('submit',e=>{e.preventDefault();savedView.offset=0;savedView.historyGeneration++;$('caseHistory').hidden=true;loadCases().catch(e=>message(e.message,true));});
for(const [id,delta] of [['casesPrev',-20],['casesNext',20]])$(id).addEventListener('click',()=>{savedView.offset=Math.max(0,savedView.offset+delta);loadCases().catch(e=>message(e.message,true));});
for(const [id,delta] of [['historyPrev',-20],['historyNext',20]])$(id).addEventListener('click',()=>{savedView.historyOffset=Math.max(0,savedView.historyOffset+delta);loadHistory().catch(e=>message(e.message,true));});
async function loadAudit(){
  try{const records=await json('/audit-logs?limit=100');const tbody=$('auditRows');tbody.replaceChildren();
    records.forEach(r=>{const row=node('tr');row.append(node('td',new Date(r.timestamp).toLocaleString('vi-VN')),node('td',r.ma_ho_so),node('td',r.event_type||'Lịch sử'),node('td',r.decision),node('td',r.extra_metadata?.officer_id||'—'),node('td',r.is_official?'Có':'Không'));tbody.append(row);});
    if(!records.length){const row=node('tr'),cell=node('td','Chưa có bản ghi.');cell.colSpan=6;row.append(cell);tbody.append(row);}
  }catch(e){message(e.message,true);}
}
function showDecision(saved){
  state.decision=saved;$('savedDecision').hidden=false;
  $('savedDecisionText').textContent=`Hồ sơ: ${saved.ma_ho_so}\nQuyết định: ${saved.final_decision}\nHạn mức: ${money(saved.approved_limit_vnd)}\nLãi suất ghi nhận: ${saved.interest_rate_pct}%/năm\nNgười ghi nhận: ${saved.officer_id}\nThời điểm: ${new Date(saved.timestamp).toLocaleString('vi-VN')}\nMã quyết định: ${saved.decision_id}\nTham chiếu thẩm định: ${saved.assessment_id}\nBản ghi nội bộ — chưa ký số bằng chứng thư.`;
  $('coreCard').hidden=saved.final_decision!=='PHÊ DUYỆT'||state.user.role!=='Committee Chair';$('coreResult').textContent='';syncPermissions();
}
function stressInputs(){return {income_drop_pct:Number($('stressIncome').value),rate_hike_pct:Number($('stressRate').value),collateral_drop_pct:Number($('stressCollateral').value),cic_drop_pts:Number($('stressCic').value)};}
function stressTable(rows){
  const table=node('table'),head=node('thead'),header=node('tr');['Hồ sơ','Trước cú sốc','Sau cú sốc','Chênh lệch','Kết quả sau cú sốc'].forEach(x=>header.append(node('th',x)));head.append(header);table.append(head);const body=node('tbody');
  rows.forEach(r=>{const tr=node('tr');tr.append(node('td',r.ma_ho_so||state.assessment?.ma_ho_so||'Hồ sơ đang nhập'),node('td',percent(r.baseline.xac_suat)),node('td',percent(r.stressed.xac_suat)),node('td',r.prob_delta.toFixed(2)+' điểm %'),node('td',r.stressed.ket_qua,r.stressed.ma_ket_qua?'good':'error'));body.append(tr);});table.append(body);const wrap=node('div',undefined,'table-scroll');wrap.append(table);return wrap;
}
$('loginForm').addEventListener('submit',async e=>{e.preventDefault();const button=e.submitter;button.disabled=true;$('loginError').textContent='';try{const user=await json('/auth/login',{username:$('username').value.trim(),password:$('password').value});await initialize(user);}catch(error){$('loginError').textContent=error.message;}finally{button.disabled=false;}});
$('logoutButton').addEventListener('click',()=>action('logoutButton',async()=>{await json('/auth/logout',{});showLogin();}));
document.querySelectorAll('[data-panel]').forEach(e=>e.addEventListener('click',()=>panel(e.dataset.panel)));
$('applicationForm').addEventListener('input',invalidate);
$('applicationForm').addEventListener('change',invalidate);
$('applicationForm').addEventListener('reset',()=>queueMicrotask(refreshAmountHints));
$('resetForm').addEventListener('click',()=>{invalidate();$('applicationForm').reset();});
$('loadSample').addEventListener('click',()=>fillProfile(state.queue[0]));
$('toCommittee').addEventListener('click',()=>panel('committee'));
$('applicationForm').addEventListener('submit',e=>{e.preventDefault();action('assessButton',async()=>{
  invalidate();$('dirtyNotice').textContent='Đang thẩm định và chờ xác nhận từ máy chủ…';
  const payload=application(),captured=signature(),generation=state.generation;
  const result=await json('/predict?use_optimal_threshold='+($('thresholdPolicy').value==='optimal'),payload);
  if(!state.user||generation!==state.generation||captured!==signature()){message('Hồ sơ đã đổi trong khi xử lý. Kết quả cũ được lưu nhưng không áp dụng cho dữ liệu mới.',true);return;}
  renderResult(result);message(result.is_cached_run?'Đã nhận lại cùng kết quả; không tạo thêm bản ghi.':'Đã thẩm định và lưu kết quả thành công.');
});});
$('queueSearch').addEventListener('input',renderQueue);
$('selectAll').addEventListener('change',()=>{const q=$('queueSearch').value.toLocaleLowerCase('vi-VN');state.queue.filter(p=>(p.ma_ho_so+' '+p.ho_ten).toLocaleLowerCase('vi-VN').includes(q)).forEach(p=>{$('selectAll').checked?state.selected.add(p.ma_ho_so):state.selected.delete(p.ma_ho_so);});renderQueue();});
$('batchButton').addEventListener('click',()=>action('batchButton',async()=>{
  if(!state.selected.size)throw new Error('Chọn ít nhất một hồ sơ.');
  $('batchResults').hidden=true;const applications=state.queue.filter(p=>state.selected.has(p.ma_ho_so)).map(({trang_thai_so_bo,...p})=>p);
  const data=await json('/queue/batch-assess',{applications,use_optimal_threshold:true});const s=data.summary;
  $('batchSummary').textContent=`${s.so_luong_thanh_cong}/${s.tong_so_ho_so} hồ sơ hoàn tất · ${s.so_luong_duyet} đạt · ${s.so_luong_tu_choi} không đạt · ${s.so_luong_loi} lỗi. Tỷ lệ đạt trên hồ sơ hoàn tất: ${percent(s.ty_le_duyet_pct)}.`;
  const body=$('batchRows');body.replaceChildren();
  data.results.forEach(r=>{const row=node('tr');row.append(node('td',r.ma_ho_so),node('td',percent(r.xac_suat_phe_duyet)),node('td',r.ket_qua),node('td','Đã lưu'));body.append(row);});
  data.errors.forEach(r=>{const row=node('tr');row.append(node('td',r.ma_ho_so),node('td','—'),node('td',r.message),node('td','Lỗi','error'));body.append(row);});$('batchResults').hidden=false;
  // Batch may supersede an assessment currently open in the cockpit.
  if(state.assessment&&applications.some(p=>p.ma_ho_so===state.assessment.ma_ho_so))invalidate();
}));
$('exportQueue').addEventListener('click',()=>action('exportQueue',async()=>{const response=await api('/export/excel/queue');const blob=await response.blob(),url=URL.createObjectURL(blob),link=node('a');link.href=url;link.download='ho_so_mo_phong.xlsx';document.body.append(link);link.click();link.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);}));
$('stressForm').addEventListener('submit',e=>{e.preventDefault();action('stressOne',async()=>{
  if(!$('applicationForm').checkValidity()){panel('assessment');$('applicationForm').reportValidity();throw new Error('Điền đầy đủ hồ sơ trước khi phân tích.');}
  $('stressOutput').hidden=true;const captured=signature(),generation=state.generation,stressGeneration=++state.stressGeneration;
  const data=await json('/simulate-stress',{application:application(),...stressInputs()});
  if(generation!==state.generation||captured!==signature()||stressGeneration!==state.stressGeneration)throw new Error('Hồ sơ hoặc kịch bản đã thay đổi; hãy chạy lại phân tích.');
  $('stressOutput').replaceChildren(stressTable([{ma_ho_so:$('ma_ho_so').value,...data,prob_delta:data.delta_prob}]),node('p',data.khuyen_nghi_chieu_tai,'fine'));$('stressOutput').hidden=false;
});});
$('stressPortfolio').addEventListener('click',()=>action('stressPortfolio',async()=>{
  if(!$('stressForm').reportValidity())return;$('stressOutput').hidden=true;const p=stressInputs(),stressGeneration=++state.stressGeneration;
  const data=await json('/simulate-stress/portfolio',{case_ids:['all_queue'],income_shock_pct:-p.income_drop_pct,interest_shock_pct:p.rate_hike_pct,collateral_shock_pct:-p.collateral_drop_pct,cic_shock_points:-p.cic_drop_pts});
  if(stressGeneration!==state.stressGeneration)throw new Error('Kịch bản đã thay đổi; hãy chạy lại phân tích.');
  const s=data.summary;$('stressOutput').replaceChildren(node('p',`${s.total_cases} hồ sơ · Số hồ sơ đạt: ${s.baseline_approved_count} → ${s.stressed_approved_count} · ${s.migrated_higher_risk_count} hồ sơ chuyển tầng rủi ro cao hơn.`),stressTable(data.details),node('p',s.policy_note,'fine'));$('stressOutput').hidden=false;
}));
$('lookupForm').addEventListener('submit',e=>{e.preventDefault();const button=e.submitter;button.disabled=true;
  invalidate();const generation=state.generation;
  json('/cases/'+encodeURIComponent($('lookupCase').value.trim())+'/latest').then(data=>{
    if(generation!==state.generation)throw new Error('Hồ sơ đã thay đổi trong lúc tra cứu.');
    const a=data.assessment;fillProfile({ma_ho_so:a.ma_ho_so,...a.application_snapshot});$('thresholdPolicy').value=a.nguong_quyet_dinh===state.config.optimal_threshold?'optimal':'default';renderResult(a);if(data.committee)showDecision(data.committee);message('Đã nạp kết quả đã lưu. Họ tên không được lưu trong nhật ký nghiệp vụ.');
  }).catch(e=>message(e.message,true)).finally(()=>button.disabled=false);
});
$('finalDecision').addEventListener('change',()=>{$('approvedLimit').value=$('finalDecision').value==='PHÊ DUYỆT'?(state.assessment?.so_tien_vay_vnd||''):0;});
$('committeeForm').addEventListener('input',()=>{state.decisionKey=null;});
$('committeeForm').addEventListener('submit',e=>{e.preventDefault();action('saveDecision',async()=>{
  if(!state.assessment||signature()!==state.signature)throw new Error('Cần thẩm định hồ sơ hiện tại trước.');
  const assessmentId=state.assessment.request_id,generation=state.generation;state.decisionKey ||= crypto.randomUUID();
  const saved=await json('/audit/committee-decision',{assessment_id:assessmentId,idempotency_key:state.decisionKey,final_decision:$('finalDecision').value,approved_limit_vnd:Number($('approvedLimit').value),interest_rate_pct:Number($('interestRate').value)});
  if(generation!==state.generation||state.assessment?.request_id!==assessmentId){message('Quyết định đã lưu cho hồ sơ trước. Tra cứu để xem lại.');return;}
  showDecision(saved);message('Máy chủ đã lưu quyết định và bản ghi kiểm toán.');
});});
$('coreForm').addEventListener('input',()=>{state.coreKey=null;});
$('coreForm').addEventListener('submit',e=>{e.preventDefault();action('simulateCore',async()=>{
  if(!state.decision)throw new Error('Chưa có quyết định được lưu.');state.coreKey ||= crypto.randomUUID();
  const decisionId=state.decision.decision_id;const data=await json('/integration/core-banking/disburse',{decision_id:decisionId,account_number:$('accountNumber').value,idempotency_key:state.coreKey});
  if(state.decision?.decision_id!==decisionId)return;
  $('coreResult').textContent=`${data.message} Mã: ${data.simulation_id}. Tài khoản: ${data.account_masked}. Giá trị mô phỏng: ${money(data.simulated_amount_vnd)}.`;
});});
$('printDecision').addEventListener('click',()=>{if(state.decision)window.print();});
$('refreshAudit').addEventListener('click',()=>action('refreshAudit',loadAudit));
$('stressForm').addEventListener('input',()=>{state.stressGeneration++;$('stressOutput').hidden=true;});
(async()=>{try{await initialize(await json('/auth/me'));}catch(e){showLogin();if(location.protocol==='file:')$('loginError').textContent='Mở giao diện qua máy chủ nội bộ để đăng nhập và thẩm định.';}})();
