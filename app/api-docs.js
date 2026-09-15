'use strict';
(async () => {
  const status = document.getElementById('docsStatus');
  const element = (tag, text) => { const e=document.createElement(tag);e.textContent=text;return e; };
  try {
    const response=await fetch('/openapi.json', {credentials:'same-origin'});
    if(!response.ok)throw new Error('Đăng nhập tại /cockpit trước khi đọc API.');
    const schema=await response.json();
    status.textContent='Ứng dụng '+schema.info.version+' · Tài liệu phục vụ cục bộ, không dùng CDN.';
    for(const [path, methods] of Object.entries(schema.paths)){
      for(const [method, operation] of Object.entries(methods)){
        const section=element('section','');section.className='card';
        section.append(element('h2',method.toUpperCase()+' '+path),element('p',operation.summary||''));
        const details=element('details','');details.append(element('summary','Parameters, request và response'),element('pre',JSON.stringify(operation,null,2)));
        section.append(details);document.getElementById('endpoints').append(section);
      }
    }
    for(const [name,definition] of Object.entries(schema.components?.schemas||{})){
      const details=element('details','');details.className='card';
      details.append(element('summary',name),element('pre',JSON.stringify(definition,null,2)));
      document.getElementById('schemas').append(details);
    }
  } catch(error){status.textContent=error.message;status.className='error';}
})();
