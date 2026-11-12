const examples = [
 {kicker:'01 — RECORD A SUCCESSFUL RUN',title:'A result you can place.',execution:'SUCCEEDED',freshness:'MATCH',verdict:'PASS',output:'$ record -- … your test command\nCommand completed with exit code 0.\nTracked-file snapshot still matches.',explanation:'The recorded command succeeded, and its snapshot still matches the current repository. This does not prove code correctness.'},
 {kicker:'02 — INSPECT THE OLD RECORD',title:'Same result. New context.',execution:'SUCCEEDED',freshness:'CHANGED',verdict:'BLOCK',output:'$ inspect -- … your old record\nHEAD changed: commit A → commit B\nCONTENT_CHANGED: "arithmetic.py"',explanation:'SUCCEEDED belongs to the old run. The code has changed since then. No new tests run during inspection, so this does not tell you whether the new code passes.'},
 {kicker:'03 — EXPLICITLY RUN TESTS AGAIN',title:'Now the test really fails.',execution:'FAILED',freshness:'MATCH',verdict:'BLOCK',output:'$ record -- … your test command\nCommand completed with a nonzero exit code.\nNew record matches the changed snapshot.',explanation:'This time a new test command actually failed. MATCH describes the snapshot, not a successful test. The two are deliberately kept separate.'},
 {kicker:'04 — REPAIR AND MAKE A NEW RECORD',title:'Fresh evidence. Clear context.',execution:'SUCCEEDED',freshness:'MATCH',verdict:'PASS',output:'$ record -- … your test command\nCommand completed with exit code 0.\nNew record saved. Previous record preserved.',explanation:'After repairing the sample, a new successful run matches the current snapshot. PASS remains a limited check, not permission to deploy or merge.'}
];
const buttons = [...document.querySelectorAll('.step')];
function selectStep(index){
 const step=examples[index];
 for (const [id,key] of [['demo-kicker','kicker'],['demo-title','title'],['execution','execution'],['freshness','freshness'],['demo-verdict','verdict'],['demo-output','output'],['demo-explanation','explanation']]) document.getElementById(id).textContent=step[key];
 document.getElementById('demo-verdict').className='pill '+(step.verdict==='PASS'?'pass':'block');
 buttons.forEach((button,i)=>{button.classList.toggle('active',i===index);button.setAttribute('aria-pressed',String(i===index));});
}
buttons.forEach((button,index)=>button.addEventListener('click',()=>selectStep(index)));
document.getElementById('copy-command').addEventListener('click',async()=>{
 const status=document.getElementById('copy-status');
 try{await navigator.clipboard.writeText(document.getElementById('command').textContent);status.textContent='Copied. Run it inside the extracted Phoenix folder.';}
 catch{status.textContent='Clipboard unavailable. Select and copy the command above.';}
});

