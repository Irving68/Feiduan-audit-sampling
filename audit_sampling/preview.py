"""生成无需服务端、可直接双击打开的本地高亮结果页。"""
from __future__ import annotations

import html
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any
from urllib.parse import quote


def _safe_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False).replace("</", "<\\/")


def _write_link_entry(root: Path, kind: str, value: str) -> None:
    """生成不依赖 Excel 传递查询参数的本地深链接入口。"""

    links_dir = root / "links"
    links_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{kind}-{value}.html"
    target = f"../preview.html?{kind}={quote(value)}"
    entry = (
        '<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">'
        f'<meta http-equiv="refresh" content="0;url={html.escape(target, quote=True)}">'
        '<title>正在打开高亮结果</title></head><body>'
        f'<script>location.replace({json.dumps(target, ensure_ascii=False)});</script>'
        f'<a href="{html.escape(target, quote=True)}">打开高亮结果</a>'
        '</body></html>'
    )
    (links_dir / filename).write_text(entry, encoding="utf-8")


def render_preview(manifest: dict[str, Any], job_dir: str | Path) -> Path:
    root = Path(job_dir)
    pages = manifest.get("pages", [])
    payload = {
        "files": manifest.get("files", []),
        "pages": pages,
        "fields": manifest.get("fields", []),
        "job": manifest.get("job", {}),
    }
    blocks_html = "".join(
        f'<div class="page-stage" id="stage-{html.escape(p["page_id"])}" '
        f'data-page-id="{html.escape(p["page_id"])}" style="width:{int(p.get("width", 1) or 1)}px;height:{int(p.get("height", 1) or 1)}px">'
        f'<img src="{html.escape(p["image"])}" alt="{html.escape(p.get("filename", p["page_id"]))}">'
        '<div class="marks"></div></div>'
        for p in pages
    )
    template = r'''<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>王二审计抽凭 v1.2.0-beta - 结果预览</title>
<style>
*{box-sizing:border-box}html,body{height:100%;margin:0}body{font-family:Arial,"Microsoft YaHei",sans-serif;background:#eef1f5;color:#222;overflow:hidden}
.top{height:56px;padding:0 18px;background:#17365d;color:#fff;display:flex;align-items:center;gap:18px}.top strong{font-size:17px}.summary{font-size:13px;opacity:.9}.top-spacer{flex:1}.page-context{font-size:12px;opacity:.85;max-width:42vw;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.layout{display:flex;height:calc(100vh - 56px)}.sidebar{width:360px;min-width:240px;max-width:65vw;background:#fff;display:flex;flex-direction:column}.divider{width:5px;cursor:col-resize;background:#d7dce3;flex:none}.divider:hover,.divider.dragging{background:#2f75b5}
.tools{padding:10px;border-bottom:1px solid #e5e7eb}.stats{font-size:12px;color:#666;margin-bottom:8px}.search{display:flex;gap:6px}.search input{min-width:0;flex:1;padding:7px 9px;border:1px solid #ccd2da;border-radius:5px}.search button,.actions button,.page-tools button,.zoom-tools button{border:1px solid #ccd2da;background:#fff;border-radius:5px;cursor:pointer;color:#445;padding:6px 9px}.search button:hover,.actions button:hover,.page-tools button:hover,.zoom-tools button:hover{border-color:#2f75b5;color:#2f75b5}.actions{display:flex;gap:6px;margin-top:7px}.actions button{flex:1;font-size:11px}
.field-list{padding:9px;overflow:auto;flex:1}.empty{color:#777;padding:30px 12px;text-align:center}.file-block{margin-bottom:12px}.file-title{font-size:13px;font-weight:700;color:#34495e;padding:6px 4px;word-break:break-all}.file-range{font-size:11px;color:#999;font-weight:400;margin-left:5px}
.doc-group{border:1px solid #e1e5ea;border-radius:7px;margin-bottom:7px;overflow:hidden}.doc-header{background:#f5f7fb;padding:8px 10px;display:flex;justify-content:space-between;align-items:center;font-size:13px;font-weight:700;cursor:pointer}.doc-header:hover{background:#eef4fb}.arrow{font-size:10px;color:#8993a0;transition:transform .15s}.doc-group.open .arrow{transform:rotate(90deg)}.doc-body{display:none}.doc-group.open .doc-body{display:block}
.field{padding:8px 10px 8px 13px;border-top:1px solid #f0f1f3;cursor:pointer;border-left:3px solid transparent}.field:hover{background:#f5f9ff}.field.active{background:#eaf4ff;border-left-color:#2f75b5}.field.unlocated{cursor:help}.field-main{display:flex;gap:8px;align-items:flex-start}.field-name{font-size:12px;color:#555;flex:0 0 84px}.field-value{font-size:12px;font-weight:700;word-break:break-all;flex:1;text-align:right}.field-meta{display:flex;justify-content:flex-end;gap:5px;margin-top:5px;font-size:10px;color:#888}.badge{border-radius:3px;padding:1px 5px;background:#edf0f3}.badge.review{background:#fff2b8;color:#7a5b00}.badge.current{background:#ddebff;color:#185aa5}.detail{font-size:10px;color:#707985;margin-top:4px;text-align:right;word-break:break-all}
.viewer{min-width:0;flex:1;display:flex;flex-direction:column}.viewer-tools{height:48px;padding:7px 12px;background:#f8fafc;border-bottom:1px solid #dfe3e8;display:flex;align-items:center;gap:12px}.page-tools,.zoom-tools{display:flex;align-items:center;gap:6px}.page-tools span{font-size:12px;color:#555;min-width:64px;text-align:center}.zoom-tools{margin-left:auto}.zoom-label{font-size:11px;color:#667;min-width:42px;text-align:center}.status{display:none;padding:6px 10px;background:#fff5cc;border:1px solid #f0d675;border-radius:5px;font-size:12px;color:#715600;max-width:48vw;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.viewport{position:relative;flex:1;overflow:hidden;cursor:grab;background:#dfe3e8}.viewport.grabbing{cursor:grabbing}.page-stage{display:none;position:absolute;left:0;top:0;transform-origin:0 0;background:#fff;box-shadow:0 3px 14px rgba(0,0,0,.22);line-height:0}.page-stage.active{display:block}.page-stage img{display:block;width:100%;height:100%;user-select:none;-webkit-user-drag:none}.marks{position:absolute;inset:0;pointer-events:none}.mark{position:absolute;border:3px solid #f2c500;background:rgba(255,235,80,.4);box-sizing:border-box}.no-results{padding:30px;text-align:center;color:#888}
@media(max-width:760px){.sidebar{width:300px}.field-name{flex-basis:70px}.page-context{display:none}}
</style></head>
<body><header class="top"><strong>王二审计抽凭 v1.2.0-beta</strong><span class="summary" id="summary"></span><span class="top-spacer"></span><span class="page-context" id="page-context"></span></header>
<div class="layout"><aside class="sidebar" id="sidebar"><div class="tools"><div class="stats" id="stats"></div><div class="search"><input id="search" placeholder="搜索字段名或字段值"><button id="clear-search">清空</button></div><div class="actions"><button id="expand-all">展开全部</button><button id="collapse-all">折叠全部</button></div></div><div class="field-list" id="field-list"></div></aside><div class="divider" id="divider"></div>
<main class="viewer"><div class="viewer-tools"><div class="page-tools"><button id="prev-page">上一页</button><span id="page-info">- / -</span><button id="next-page">下一页</button></div><div class="status" id="status"></div><div class="zoom-tools"><button id="fit-width">适应宽度</button><button id="zoom-out">−</button><span class="zoom-label" id="zoom-label">100%</span><button id="zoom-in">+</button></div></div><div class="viewport" id="viewport">__PAGE_BLOCKS__</div></main></div>
<script>
const DATA=__DATA__;
const pages=DATA.pages||[],fields=DATA.fields||[],files=DATA.files||[];
const pageMap=new Map(pages.map((p,i)=>[p.page_id,{...p,index:i}]));
const fileOrder=new Map(files.map((f,i)=>[f.file_id||f.name,i]));
const fileMeta=new Map(files.map(f=>[f.file_id||f.name,f]));
const nameCounts=files.reduce((m,f)=>(m.set(f.name,(m.get(f.name)||0)+1),m),new Map()),nameSeen=new Map(),fileLabels=new Map();
files.forEach(f=>{nameSeen.set(f.name,(nameSeen.get(f.name)||0)+1);fileLabels.set(f.file_id||f.name,(nameCounts.get(f.name)||0)>1?`${f.name}（${nameSeen.get(f.name)}）`:f.name)});
let currentPageIndex=0,activeField=null,scale=1,tx=0,ty=0,dragging=false,dragStart=null;
const list=document.getElementById('field-list'),viewport=document.getElementById('viewport'),statusBox=document.getElementById('status');
function esc(s){return String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));}
function needsReview(f){return (f.review_reasons||[]).length>0||Number(f.confidence||0)<.9;}
function reviewText(f){return (f.review_reasons||[]).join('、');}
function fileKeyFor(f){if(f.file_id)return f.file_id;const p=pageMap.get(f.page_id);return p?(p.file_id||p.filename):(f.file||'未归属文件');}
function fileNameFor(f){const key=fileKeyFor(f),meta=fileMeta.get(key);return fileLabels.get(key)||(meta?meta.name:(f.file||key));}
function pageRange(key){const indexes=pages.map((p,i)=>(p.file_id||p.filename)===key?i+1:null).filter(Boolean);return indexes.length?`（任务页 ${indexes[0]}-${indexes[indexes.length-1]}）`:'';}
function groupedFields(query=''){
  const q=query.trim().toLowerCase(),byFile=new Map();
  fields.forEach((f,index)=>{const hay=(String(f.name||'')+' '+String(f.value||'')).toLowerCase();if(q&&!hay.includes(q))return;const fileKey=fileKeyFor(f),key=String(f.document_type||'未知资料')+'\u0000'+String(f.group_id||'default');if(!byFile.has(fileKey))byFile.set(fileKey,new Map());const groups=byFile.get(fileKey);if(!groups.has(key))groups.set(key,{type:f.document_type||'未知资料',fields:[]});groups.get(key).fields.push({...f,_index:index});});
  return [...byFile.entries()].sort((a,b)=>(fileOrder.get(a[0])??9999)-(fileOrder.get(b[0])??9999));
}
function renderList(query=''){
  const grouped=groupedFields(query);if(!grouped.length){list.innerHTML='<div class="no-results">没有匹配字段</div>';updateStats(0);return;}
  let shown=0,out='';grouped.forEach(([fileKey,groupMap],fileIndex)=>{const groups=[...groupMap.values()],typeCounts={},typeSeen={};groups.forEach(g=>typeCounts[g.type]=(typeCounts[g.type]||0)+1);out+=`<div class="file-block"><div class="file-title">${esc(fileLabels.get(fileKey)||fileKey)}<span class="file-range">${esc(pageRange(fileKey))}</span></div>`;groups.forEach((g,groupIndex)=>{typeSeen[g.type]=(typeSeen[g.type]||0)+1;const label=typeCounts[g.type]>1?`${g.type} ${typeSeen[g.type]}`:g.type;const isOpen=g.fields.some(f=>activeField&&activeField._index===f._index)||!!query;out+=`<div class="doc-group ${isOpen?'open':''}"><div class="doc-header"><span>${esc(label)}</span><span class="arrow">▶</span></div><div class="doc-body">`;g.fields.forEach(f=>{shown++;const review=needsReview(f),reason=reviewText(f),located=!!f.page_id&&pageMap.has(f.page_id),current=pages[currentPageIndex]&&f.page_id===pages[currentPageIndex].page_id;const source=f.raw_value&&String(f.raw_value)!==String(f.value)?`<div class="detail">来源 OCR：${esc(f.raw_value)}</div>`:'';const correction=f.correction?`<div class="detail">Agent 复核：${esc(f.correction)}</div>`:'';const reviewDetail=reason?`<div class="detail">复核原因：${esc(reason)}</div>`:'';out+=`<div class="field ${located?'':'unlocated'} ${activeField&&activeField._index===f._index?'active':''}" data-field-index="${f._index}"><div class="field-main"><span class="field-name">${esc(f.name)}</span><span class="field-value">${esc(f.value)}</span></div><div class="field-meta"><span class="badge ${current?'current':''}">第${esc(f.page??'-')}页</span><span class="badge ${review?'review':''}">${review?'需人工复核':'已定位'}</span></div>${source}${correction}${reviewDetail}</div>`;});out+='</div></div>';});out+='</div>';});list.innerHTML=out;list.querySelectorAll('.doc-header').forEach(el=>el.onclick=()=>el.parentElement.classList.toggle('open'));list.querySelectorAll('.field').forEach(el=>el.onclick=()=>selectField(Number(el.dataset.fieldIndex)));updateStats(shown);
}
function updateStats(shown=fields.length){const fileCount=new Set(fields.map(fileKeyFor)).size,groupCount=new Set(fields.map(f=>fileKeyFor(f)+'\u0000'+(f.document_type||'')+'\u0000'+(f.group_id||''))).size;document.getElementById('stats').textContent=`${fileCount} 文件 · ${groupCount} 资料 · ${shown} / ${fields.length} 字段`;document.getElementById('summary').textContent=`字段 ${fields.length} · 需人工复核 ${fields.filter(needsReview).length}`;}
function currentStage(){const p=pages[currentPageIndex];return p?document.getElementById('stage-'+p.page_id):null;}
function applyTransform(){const stage=currentStage();if(stage)stage.style.transform=`translate(${tx}px,${ty}px) scale(${scale})`;document.getElementById('zoom-label').textContent=Math.round(scale*100)+'%';}
function fitWidth(){const p=pages[currentPageIndex];if(!p)return;const pad=36;scale=Math.min(1,(viewport.clientWidth-pad)/Math.max(Number(p.width||1),1));tx=Math.max(pad/2,(viewport.clientWidth-Number(p.width||1)*scale)/2);ty=18;applyTransform();}
function clearMarks(){document.querySelectorAll('.marks').forEach(m=>m.innerHTML='');}
function showStatus(text){statusBox.textContent=text;statusBox.style.display='block';}function hideStatus(){statusBox.textContent='';statusBox.style.display='none';}
function paintField(f){clearMarks();if(!f||!f.page_id||!pageMap.has(f.page_id)){showStatus('该字段暂时无法定位原文，请人工复核。');return;}const marks=document.querySelector('#stage-'+f.page_id+' .marks');(f.bboxes||[]).forEach(b=>{const m=document.createElement('div');m.className='mark';m.style.left=b.left+'px';m.style.top=b.top+'px';m.style.width=b.width+'px';m.style.height=b.height+'px';marks.appendChild(m);});const reason=reviewText(f);if(!(f.bboxes||[]).length)showStatus(`已找到来源页，但无法精确定位原文${reason?'：'+reason:''}。`);else if(reason)showStatus(`需人工复核：${reason}`);else hideStatus();}
function showPage(index,autoSelect=false){if(!pages.length)return;currentPageIndex=Math.max(0,Math.min(index,pages.length-1));document.querySelectorAll('.page-stage').forEach(s=>s.classList.toggle('active',s.dataset.pageId===pages[currentPageIndex].page_id));document.getElementById('page-info').textContent=`${currentPageIndex+1} / ${pages.length}`;document.getElementById('prev-page').disabled=currentPageIndex===0;document.getElementById('next-page').disabled=currentPageIndex===pages.length-1;document.getElementById('page-context').textContent=`${pages[currentPageIndex].filename||''} · 文件第 ${pages[currentPageIndex].source_page||'-'} 页`;fitWidth();if(autoSelect){const first=fields.map((f,i)=>({...f,_index:i})).find(f=>f.page_id===pages[currentPageIndex].page_id);if(first){activeField=first;paintField(first);}else{activeField=null;clearMarks();hideStatus();}}else if(activeField&&activeField.page_id===pages[currentPageIndex].page_id)paintField(activeField);else{clearMarks();hideStatus();}renderList(document.getElementById('search').value);}
function selectField(index,updateUrl=true){const f={...fields[index],_index:index};activeField=f;if(updateUrl&&f.field_id)history.replaceState(null,'','?field='+encodeURIComponent(f.field_id));if(!f.page_id||!pageMap.has(f.page_id)){paintField(f);renderList(document.getElementById('search').value);return;}const target=pageMap.get(f.page_id).index;if(target!==currentPageIndex)showPage(target,false);paintField(f);renderList(document.getElementById('search').value);const el=list.querySelector(`[data-field-index="${index}"]`);if(el)el.scrollIntoView({block:'nearest'});}
function selectLinkTarget(){let params=new URLSearchParams(location.search);if(!params.get('field')&&!params.get('file'))params=new URLSearchParams(location.hash.replace(/^#/,''));const fieldId=params.get('field'),fileId=params.get('file');let index=-1;if(fieldId)index=fields.findIndex(f=>String(f.field_id)===fieldId);else if(fileId)index=fields.findIndex(f=>String(f.file_id||'')===fileId);if(index>=0){selectField(index,false);return true;}return false;}
document.getElementById('prev-page').onclick=()=>showPage(currentPageIndex-1,true);document.getElementById('next-page').onclick=()=>showPage(currentPageIndex+1,true);document.getElementById('fit-width').onclick=fitWidth;document.getElementById('zoom-in').onclick=()=>{scale=Math.min(3,scale+.15);applyTransform()};document.getElementById('zoom-out').onclick=()=>{scale=Math.max(.1,scale-.15);applyTransform()};
document.getElementById('search').oninput=e=>renderList(e.target.value);document.getElementById('clear-search').onclick=()=>{document.getElementById('search').value='';renderList()};document.getElementById('expand-all').onclick=()=>list.querySelectorAll('.doc-group').forEach(g=>g.classList.add('open'));document.getElementById('collapse-all').onclick=()=>list.querySelectorAll('.doc-group').forEach(g=>g.classList.remove('open'));
viewport.onwheel=e=>{e.preventDefault();const rect=viewport.getBoundingClientRect(),cx=e.clientX-rect.left,cy=e.clientY-rect.top,old=scale;scale=Math.max(.1,Math.min(3,scale+(e.deltaY<0?.1:-.1)));const ratio=scale/old;tx=cx-ratio*(cx-tx);ty=cy-ratio*(cy-ty);applyTransform()};viewport.onmousedown=e=>{dragging=true;dragStart={x:e.clientX,y:e.clientY,tx,ty};viewport.classList.add('grabbing')};window.onmousemove=e=>{if(!dragging)return;tx=dragStart.tx+e.clientX-dragStart.x;ty=dragStart.ty+e.clientY-dragStart.y;applyTransform()};window.onmouseup=()=>{dragging=false;viewport.classList.remove('grabbing')};
document.addEventListener('keydown',e=>{if(e.target.tagName==='INPUT')return;if(e.key==='ArrowLeft')showPage(currentPageIndex-1,true);if(e.key==='ArrowRight')showPage(currentPageIndex+1,true)});
(()=>{const divider=document.getElementById('divider'),sidebar=document.getElementById('sidebar');let resizing=false;divider.onmousedown=e=>{resizing=true;divider.classList.add('dragging');e.preventDefault()};window.addEventListener('mousemove',e=>{if(!resizing)return;sidebar.style.width=Math.max(240,Math.min(window.innerWidth*.65,e.clientX))+'px';fitWidth()});window.addEventListener('mouseup',()=>{resizing=false;divider.classList.remove('dragging')})})();
renderList();if(pages.length){showPage(0,false);selectLinkTarget();}else{viewport.innerHTML='<div class="empty">没有可展示页面</div>';document.getElementById('page-info').textContent='0 / 0';}window.addEventListener('hashchange',selectLinkTarget);window.addEventListener('popstate',selectLinkTarget);
</script></body></html>'''
    output = template.replace("__PAGE_BLOCKS__", blocks_html).replace("__DATA__", _safe_json(payload))
    target = root / "preview.html"
    target.write_text(output, encoding="utf-8")
    for field in manifest.get("fields", []):
        field_id = str(field.get("field_id", "") or "")
        if field_id:
            _write_link_entry(root, "field", field_id)
    for file in manifest.get("files", []):
        file_id = str(file.get("file_id", "") or "")
        if file_id:
            _write_link_entry(root, "file", file_id)
    bat = root / "open-preview.bat"
    bat.write_text('@echo off\nstart "" "%~dp0preview.html"\n', encoding="utf-8")
    return target


def open_preview(path: str | Path) -> None:
    target = Path(path).resolve()
    if sys.platform.startswith("win"):
        os.startfile(str(target))  # type: ignore[attr-defined]
    elif sys.platform == "darwin":
        subprocess.Popen(["open", str(target)])
    else:
        subprocess.Popen(["xdg-open", str(target)])
