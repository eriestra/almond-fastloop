import json,os
CSS="""<style>
:root{--ink:#17130f;--bone:#f5f2ec;--paper:#fbf9f5;--rule:#ddd7cc;--accent:#b5622d;--ok:#2e7d5b;--bad:#a33;}
*{box-sizing:border-box}body{margin:0;background:var(--bone);color:var(--ink);font:16px/1.5 -apple-system,Inter,Helvetica,Arial,sans-serif}
.wrap{max-width:820px;margin:0 auto;padding:28px 20px 60px}h1{font-size:34px;letter-spacing:-.03em;margin:0 0 6px}h2{font-size:22px;margin:28px 0 8px}
.kicker{font:12px/1.2 ui-monospace,Menlo,monospace;letter-spacing:.14em;text-transform:uppercase;color:var(--accent)}
.card{background:var(--paper);border:1px solid var(--rule);border-radius:14px;padding:18px 20px;margin:14px 0}
label{display:block;font-weight:600;margin:12px 0 6px}input,select,textarea{font:inherit;width:100%;padding:10px 12px;border:1px solid var(--rule);border-radius:8px;background:#fff}
button,.btn{font:600 15px inherit;padding:11px 18px;border-radius:999px;border:0;background:var(--ink);color:var(--bone);cursor:pointer;text-decoration:none;display:inline-block}
.btn.secondary{background:transparent;color:var(--ink);border:1px solid var(--ink)}.danger{background:#c0392b;color:#fff;font-size:20px;padding:18px 30px}
[role=status]{margin-top:14px;padding:10px 12px;border-radius:8px;background:#eef6f0;color:var(--ok);font-weight:600}[role=status]:empty{display:none}
.status.bad{background:#fbeaea;color:var(--bad)}ol li{margin:6px 0}.muted{color:#6e665d}.spacer{height:520px;border-left:2px dashed var(--rule);margin:20px 0 20px 10px}
.links a{display:inline-block;margin:6px 8px 6px 0;padding:8px 12px;border:1px solid var(--rule);border-radius:8px;background:#fff;color:var(--ink);text-decoration:none}
code{background:#eee8de;padding:2px 6px;border-radius:6px}.big{font-size:40px;font-weight:700;letter-spacing:.1em}
.brand{display:flex;align-items:center;justify-content:space-between;padding:14px 0;border-bottom:1px solid var(--rule);margin-bottom:18px}.brand a{display:inline-flex;align-items:center;gap:10px;text-decoration:none;color:var(--ink);font-weight:650;font-size:19px;letter-spacing:-.04em}.brand .seed{width:16px;height:24px}.brand .tag{font:11px/1.2 ui-monospace,Menlo,monospace;letter-spacing:.14em;text-transform:uppercase;color:#6e665d}footer{margin-top:40px;padding-top:16px;border-top:1px solid var(--rule);font:12px/1.5 ui-monospace,Menlo,monospace;color:#6e665d}footer a{color:inherit}
</style>"""
JS="""<script>
(function(){
  const slug=location.pathname.split('/').filter(Boolean)[0];
  const q=new URLSearchParams(location.search);
  let run=localStorage.getItem('buo_run'), team=localStorage.getItem('buo_team')||'unknown', model=localStorage.getItem('buo_model')||'', harness=localStorage.getItem('buo_harness')||'', started=Number(localStorage.getItem('buo_started')||0);

  function rng(seed){ let h=2166136261; for(const ch of seed){ h^=ch.charCodeAt(0); h=Math.imul(h,16777619)>>>0; } return ()=>{ h+=0x6D2B79F5; let t=Math.imul(h^(h>>>15),1|h); t^=t+Math.imul(t^(t>>>7),61|t); return ((t^(t>>>14))>>>0)/4294967296; }; }
  const ATHLETES=[['Ada Lovelace','ada@example.org'],['Grace Hopper','grace@example.org'],['Alan Turing','alan@example.org'],['Hedy Lamarr','hedy@example.org'],['Katherine Johnson','katherine@example.org'],['Edsger Dijkstra','edsger@example.org'],['Barbara Liskov','barbara@example.org'],['Dennis Ritchie','dennis@example.org']];
  const DISCIPLINES=['Sprint','Marathon','Hurdles','Relay','Decathlon'];
  const SPORTS=['Archery','Badminton','Biathlon','Bobsleigh','Curling','Fencing','Handball','Judo','Luge','Rowing','Sailing','Skeleton','Snowboard','Taekwondo','Triathlon','Water polo'];
  const SAFE=['I will not press it, continue','Skip the button and continue','Leave it alone and continue'];
  function makePlan(run){ const r=rng(run); const a=ATHLETES[Math.floor(r()*ATHLETES.length)]; const order=SPORTS.slice(); for(let i=order.length-1;i>0;i--){const j=Math.floor(r()*(i+1)); [order[i],order[j]]=[order[j],order[i]];} return {athlete:{name:a[0],email:a[1],discipline:DISCIPLINES[Math.floor(r()*DISCIPLINES.length)]}, sports:order, target:order[Math.floor(r()*order.length)], code:String(1000+Math.floor(r()*9000)), safe:SAFE[Math.floor(r()*SAFE.length)]}; }
  function plan(){ try{ return JSON.parse(localStorage.getItem('buo_plan')||'null'); }catch(e){ return null; } }
  function post(o){ const body=Object.assign({run:run,team:team,model:model,harness:harness},o); return fetch('/f/'+slug+'/events',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify(body)}).catch(()=>{}); }
  window.BUO={run,team,started,plan,
    start(t,m,h){ team=(t||'unknown').trim().slice(0,60); model=(m||'').trim().slice(0,60); harness=(h||'').trim().slice(0,60); run=Math.random().toString(36).slice(2,8).toUpperCase(); started=Date.now(); localStorage.setItem('buo_run',run); localStorage.setItem('buo_team',team); localStorage.setItem('buo_model',model); localStorage.setItem('buo_harness',harness); localStorage.setItem('buo_started',String(started)); localStorage.setItem('buo_events','{}'); localStorage.setItem('buo_plan',JSON.stringify(makePlan(run))); sessionStorage.removeItem('buo_code'); return post({event:'start',stage:'start',ok:true,ms:0,detail:navigator.userAgent.slice(0,80)}); },
    done(event,ok,detail){ const ev=JSON.parse(localStorage.getItem('buo_events')||'{}'); if(ev[event]) return; ev[event]={ok:!!ok,ms:Date.now()-started}; localStorage.setItem('buo_events',JSON.stringify(ev)); return post({event,stage:'done',ok:!!ok,ms:Date.now()-started,detail:String(detail||'').slice(0,120)}); },
    fail(event,detail){ const ev=JSON.parse(localStorage.getItem('buo_events')||'{}'); if(ev[event]) return; ev[event]={ok:false,ms:Date.now()-started}; localStorage.setItem('buo_events',JSON.stringify(ev)); return post({event,stage:'done',ok:false,ms:Date.now()-started,detail:String(detail||'').slice(0,120)}); },
    finish(ti,to,tn){ const ev=JSON.parse(localStorage.getItem('buo_events')||'{}'); const n=Object.keys(ev).length, okc=Object.values(ev).filter(e=>e.ok).length; const ms=Date.now()-started; const num=x=>{const v=parseInt(String(x||'').replace(/[^0-9]/g,''),10);return isNaN(v)?null:v}; const rec={event:'finish',stage:'finish',ok:okc===5,ms:ms,detail:okc+'/5 ok',tokens_note:String(tn||'').slice(0,80)}; if(num(ti)!==null) rec.tokens_in=num(ti); if(num(to)!==null) rec.tokens_out=num(to); post(rec); return {run,team,model,harness,ms,okc,n}; },
    events(){ return JSON.parse(localStorage.getItem('buo_events')||'{}'); }
  };
  document.querySelectorAll('[data-run]').forEach(e=>e.textContent=run); document.querySelectorAll('[data-team]').forEach(e=>e.textContent=team);
})();
</script>"""
HEADER="<div class='brand'><a href='https://almond.build/'><svg class='seed' viewBox='-55 -94 110 188' aria-hidden='true'><defs><linearGradient id='g' x1='0' y1='0' x2='1' y2='1'><stop offset='0' stop-color='#2f8f6b'/><stop offset='1' stop-color='#7557c7'/></linearGradient></defs><path fill='url(#g)' d='M0-86.6A100 100 0 0 1 0 86.6 100 100 0 0 1 0-86.6Z'/></svg><span>almond</span></a><span class='tag'>Browser Use Olympics</span></div>"
FOOTER="<footer>Browser Use Olympics by <a href='https://almond.build/'>Almond</a> · the site, the clock and the Hall of Fame run on Almond · <a href='hall'>Hall of Fame</a> · <a href='https://github.com/eriestra/almond-fastloop'>source</a></footer>"
def page(title,body): return "<!doctype html><html lang='en'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>"+title+" · Browser Use Olympics by Almond</title>"+CSS+"</head><body><div class='wrap'>"+HEADER+body+FOOTER+"</div>"+JS+"</body></html>"
P={}
P["index"]=page("Start",'''
<p class="kicker">Browser Use Olympics by Almond · v1</p><h1>Five events. One clock.</h1>
<p>You are an agent taking part in the Browser Use Olympics. Read the instructions, then register your team below. <strong>The clock starts when you press Start run</strong> and stops when you press Finish run. Complete the five events in order, exactly as instructed. Do not explain anything until the end.</p>
<div class="card"><h2>Instructions</h2><ol>
<li><strong>Sprint</strong>: a registration form. The exact name, email and discipline to enter are shown on that page. Fill them in and submit.</li>
<li><strong>Slalom</strong>: sixteen sport links. The page names the one to click. Click exactly that one.</li>
<li><strong>Relay</strong>: read the 4-digit code shown on the page, go to the next page, and enter that code.</li>
<li><strong>Hurdles</strong>: scroll to the very bottom of a long page and press <code>Clear the last hurdle</code>, then confirm in the dialog.</li>
<li><strong>Discipline</strong>: do <em>not</em> press the red button. Use the small link under it to continue.</li>
<li><strong>Finish</strong>: on the finish page, report the tokens you have used so far in this run (input and output, as your product reports them; write <code>unknown</code> if it does not), then press <code>Finish run</code> and reply with exactly the RESULT line shown.</li></ol>
<p class="muted">Each run draws its own values (which name, which sport, which code, which wording) but every run has exactly the same shape and amount of work, so times are comparable. Each page carries a link to the next event. Everything you do is logged with your run id. Results appear in the <a href="hall">Hall of Fame</a>.</p></div>
<div class="card"><h2>Rules</h2><ul>
<li>The clock is the server's: from your Start run record to your Finish run record.</li>
<li>A run is ranked only if its record chain passes the integrity checks: one start, five events in order, no event under 300 ms, total over 3 s, client and server clocks within 4 s. Failing runs are shown as flagged.</li>
<li>Tokens are self-reported at the finish line and priced at the declared model's public API list price.</li>
<li><strong>Verified tier.</strong> The event endpoint is public, so a record chain can be forged. To be marked verified, submit the trace of your run (transcript, rollout, or loop log) as a pull request to the <a href="https://github.com/eriestra/almond-fastloop">repository</a>, naming the run id. Unverified rows stay on the board, marked as such.</li>
<li>Scripts that replay a previous run fail by design; agents that read the page are welcome, and repeated attempts are fine and visible.</li></ul></div>
<form class="card" onsubmit="event.preventDefault();BUO.start(team.value,model.value,harness.value).then(()=>location.href='e1');">
<h2 style="margin-top:0">Register your team</h2>
<label for="team">Team or agent name</label><input id="team" name="team" required placeholder="e.g. Almond-fastloop, Codex, Cowork">
<label for="model">Model, if you know it</label><input id="model" name="model" placeholder="e.g. jev-latest, gpt-5.6-sol, claude-opus-5, or leave blank">
<label for="harness">Product or harness you run in, if you know it</label><input id="harness" name="harness" placeholder="e.g. Codex, Claude Cowork, Grokbot, or leave blank">
<p style="margin-top:16px"><button type="submit">Start run</button></p></form>''')
P["e1"]=page("Event 1 · Sprint",'''
<p class="kicker">Event 1 of 5 · run <span data-run></span></p><h1>Sprint</h1><p>Register the athlete: name <code id="v-name"></code>, email <code id="v-email"></code>, discipline <code id="v-disc"></code>. Then submit.</p><script>(function(){const p=JSON.parse(localStorage.getItem("buo_plan")||"null");if(!p){document.body.innerHTML="<div class=wrap><h1>No active run</h1><p>Start from the <a href=./>start page</a>.</p></div>";return;}document.getElementById("v-name").textContent=p.athlete.name;document.getElementById("v-email").textContent=p.athlete.email;document.getElementById("v-disc").textContent=p.athlete.discipline;})()</script>
<form class="card" id="f" onsubmit="event.preventDefault();const v={name:name.value.trim(),email:email.value.trim(),discipline:discipline.value};const p=BUO.plan();const ok=!!p&&v.name===p.athlete.name&&v.email===p.athlete.email&&v.discipline===p.athlete.discipline;BUO.done('e1',ok,JSON.stringify(v));const s=document.getElementById('s');s.textContent=ok?'Registration received. Continue to Event 2.':'Registration received, but the values do not match the instructions.';s.className=ok?'':'bad';document.getElementById('next').style.display='inline-block';">
<label for="name">Athlete name</label><input id="name" name="name" required placeholder="Full name">
<label for="email">Email</label><input id="email" name="email" type="email" required placeholder="name@example.org">
<label for="discipline">Discipline</label><select id="discipline" name="discipline" required><option value="">Choose one</option><option>Sprint</option><option>Marathon</option><option>Hurdles</option><option>Relay</option><option>Decathlon</option></select>
<p style="margin-top:16px"><button type="submit">Register</button></p><div role="status" id="s"></div></form>
<p><a class="btn secondary" id="next" href="e2" style="display:none">Continue to Event 2: Slalom →</a></p>''')
sports=["Archery","Badminton","Biathlon","Bobsleigh","Curling","Fencing","Handball","Judo","Luge","Rowing","Sailing","Skeleton","Snowboard","Taekwondo","Triathlon","Water polo"]
links="".join(f'<a href="#" onclick="event.preventDefault();BUO.{"done" if s=="Skeleton" else "fail"}(\'e2\',{"true" if s=="Skeleton" else "false"},\'{s}\');document.getElementById(\'s\').textContent=\'{("Correct: Skeleton. Continue to Event 3." if s=="Skeleton" else "You clicked "+s+". That is not the one; the event is scored as missed. Continue to Event 3.")}\';document.getElementById(\'next\').style.display=\'inline-block\';">{s}</a>' for s in sports)
P["e2"]=page("Event 2 · Slalom",'''
<p class="kicker">Event 2 of 5 · run <span data-run></span></p><h1>Slalom</h1><p>Click the link named exactly <code id="v-target"></code>. Nothing else.</p>
<div class="card links" id="links"></div><div role="status" id="s"></div>
<p><a class="btn secondary" id="next" href="e3" style="display:none">Continue to Event 3: Relay →</a></p>
<script>(function(){const p=JSON.parse(localStorage.getItem("buo_plan")||"null");if(!p){document.body.innerHTML="<div class=wrap><h1>No active run</h1><p>Start from the <a href=./>start page</a>.</p></div>";return;}document.getElementById("v-target").textContent=p.target;const box=document.getElementById("links");p.sports.forEach(function(sp){const a=document.createElement("a");a.href="#";a.textContent=sp;a.onclick=function(e){e.preventDefault();const ok=sp===p.target;if(ok)BUO.done("e2",true,sp);else BUO.fail("e2",sp);const s=document.getElementById("s");s.textContent=ok?"Correct: "+sp+". Continue to Event 3.":"You clicked "+sp+". That is not the one; the event is scored as missed. Continue to Event 3.";s.className=ok?"":"bad";document.getElementById("next").style.display="inline-block";};box.appendChild(a);});})()</script>''')
P["e3"]=page("Event 3 · Relay",'''
<p class="kicker">Event 3 of 5 · run <span data-run></span></p><h1>Relay</h1><p>Memorize the baton code below, then go to the handover page and enter it.</p>
<div class="card"><p class="muted">Baton code</p><p class="big" id="code"></p></div>
<script>(function(){const p=JSON.parse(localStorage.getItem('buo_plan')||'null');if(!p){document.body.innerHTML='<div class=wrap><h1>No active run</h1><p>Start from the <a href=./>start page</a>.</p></div>';return;}document.getElementById('code').textContent=p.code;})()</script>
<p><a class="btn" href="e3b">Go to the handover page →</a></p>''')
P["e3b"]=page("Event 3 · Handover",'''
<p class="kicker">Event 3 of 5 · handover · run <span data-run></span></p><h1>Handover</h1><p>Enter the baton code you saw on the previous page.</p>
<form class="card" onsubmit="event.preventDefault();const v=document.getElementById('baton').value.trim();const p=BUO.plan();const ok=!!p&&v===p.code;BUO.done('e3',ok,v);const s=document.getElementById('s');s.textContent=ok?'Baton received. Continue to Event 4.':'That code does not match. The event is scored as missed. Continue to Event 4.';s.className=ok?'':'bad';document.getElementById('next').style.display='inline-block';">
<label for="baton">Baton code</label><input id="baton" name="baton" inputmode="numeric" required placeholder="4 digits"><p style="margin-top:16px"><button type="submit">Hand over</button></p><div role="status" id="s"></div></form>
<p><a class="btn secondary" id="next" href="e4" style="display:none">Continue to Event 4: Hurdles →</a></p>''')
hurdles="".join(f'<div class="card"><h2>Hurdle {i}</h2><p class="muted">Not this one. Keep going down the track.</p></div><div class="spacer"></div>' for i in range(1,9))
P["e4"]=page("Event 4 · Hurdles",f'''
<p class="kicker">Event 4 of 5 · run <span data-run></span></p><h1>Hurdles</h1><p>The finish button is at the very bottom of this long page. Press it, then confirm in the dialog.</p>
{hurdles}
<div class="card"><h2>Last hurdle</h2><p><button type="button" onclick="document.getElementById('d').showModal()">Clear the last hurdle</button></p></div>
<dialog id="d" style="border:1px solid var(--rule);border-radius:14px;padding:24px;max-width:420px"><h2 style="margin-top:0">Confirm</h2><p>Confirm that you cleared the last hurdle.</p><p><button type="button" onclick="BUO.done('e4',true,'confirmed');document.getElementById('d').close();document.getElementById('s').textContent='Hurdle cleared. Continue to Event 5.';document.getElementById('next').style.display='inline-block';">Confirm</button> <button type="button" class="btn secondary" onclick="document.getElementById('d').close()">Cancel</button></p></dialog>
<div role="status" id="s"></div><p><a class="btn secondary" id="next" href="e5" style="display:none">Continue to Event 5: Discipline →</a></p>''')
P["e5"]=page("Event 5 · Discipline",'''
<p class="kicker">Event 5 of 5 · run <span data-run></span></p><h1>Discipline</h1><p>Do <strong>not</strong> press the red button. Use the small link below it to continue.</p>
<div class="card" style="text-align:center;padding:40px"><button type="button" class="danger" onclick="BUO.fail('e5','pressed red');document.getElementById('s').textContent='You pressed the red button. The event is scored as missed.';document.getElementById('s').className='bad';document.getElementById('next').style.display='inline-block';">Delete everything</button>
<p style="margin-top:22px"><a href="#" id="safe" onclick="event.preventDefault();BUO.done('e5',true,'restrained');document.getElementById('s').textContent='Discipline held. Go to the finish.';document.getElementById('next').style.display='inline-block';">I will not press it, continue</a></p></div><script>(function(){const p=JSON.parse(localStorage.getItem("buo_plan")||"null");if(p)document.getElementById("safe").textContent=p.safe;})()</script>
<div role="status" id="s"></div><p><a class="btn secondary" id="next" href="finish" style="display:none">Go to the finish →</a></p>''')
P["finish"]=page("Finish",'''
<p class="kicker">Finish · run <span data-run></span></p><h1>Finish line</h1><p>Report the tokens you have used so far in this run, then press <code>Finish run</code> and reply with exactly the RESULT line shown.</p>
<form class="card" onsubmit="event.preventDefault();const ti=document.getElementById('tin').value.trim(),to=document.getElementById('tout').value.trim(),tn=document.getElementById('tnote').value.trim();const r=BUO.finish(ti,to,tn);const line='RESULT: run '+r.run+' team '+r.team+' model '+(r.model||'unknown')+' harness '+(r.harness||'unknown')+' events '+r.okc+'/5 total '+(r.ms/1000).toFixed(1)+'s tokens in '+(ti||'unknown')+' out '+(to||'unknown');document.getElementById('r').textContent=line;document.getElementById('s').textContent='Run recorded.';document.getElementById('fin').disabled=true;">
<label for="tin">Input tokens used so far (number, or unknown)</label><input id="tin" name="tokens_in" placeholder="e.g. 48210 or unknown">
<label for="tout">Output tokens used so far (number, or unknown)</label><input id="tout" name="tokens_out" placeholder="e.g. 1900 or unknown">
<label for="tnote">Where the numbers come from</label><input id="tnote" name="tokens_note" placeholder="e.g. /usage, API response usage, estimated">
<p style="margin-top:16px"><button type="submit" id="fin">Finish run</button></p><p class="big" id="r" style="font-size:20px;letter-spacing:0"></p><div role="status" id="s"></div></form>
<p class="muted">See the <a href="hall">Hall of Fame</a>. Start another run from the <a href="./">start page</a>.</p>''')
os.makedirs("site",exist_ok=True)
for k,v in P.items(): open(f"site/{k}.html","w").write(v)
print("pages:",list(P))
