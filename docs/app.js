const pageLanguage = document.documentElement.lang.startsWith('zh') ? 'zh' : 'en';
const address = new URL(window.location.href);
const explicitLanguage = address.searchParams.get('lang');
let rememberedLanguage;
try { rememberedLanguage = window.localStorage.getItem('phoenix.language'); } catch { /* Storage is optional. */ }
const supported = value => value === 'zh' || value === 'en';
const directChineseLink = address.pathname.endsWith('/zh.html');
const preferredLanguage = supported(explicitLanguage) ? explicitLanguage
 : directChineseLink ? 'zh'
 : supported(rememberedLanguage) ? rememberedLanguage
 : (navigator.language || '').toLowerCase().startsWith('zh') ? 'zh' : 'en';
if (supported(explicitLanguage)) {
 try { window.localStorage.setItem('phoenix.language', explicitLanguage); } catch { /* Storage is optional. */ }
}
if (preferredLanguage !== pageLanguage) {
 const target = new URL(preferredLanguage === 'zh' ? 'zh.html' : 'index.html', address);
 target.searchParams.set('lang', preferredLanguage);
 target.hash = address.hash;
 window.location.replace(target.href);
}
document.querySelectorAll('[data-language]').forEach(link => {
 const target = new URL(link.getAttribute('href'), address);
 target.hash = address.hash;
 link.href = target.href;
 link.addEventListener('click', () => { target.hash = window.location.hash; link.href = target.href; });
});
const englishExamples = [
 {kicker:'01 — RECORD A SUCCESSFUL RUN',title:'A result you can place.',execution:'SUCCEEDED',freshness:'MATCH',verdict:'PASS',output:'$ record -- … your test command\nCommand completed with exit code 0.\nTracked-file snapshot still matches.',explanation:'The recorded command succeeded, and its snapshot still matches the current repository. This does not prove code correctness.'},
 {kicker:'02 — INSPECT THE OLD RECORD',title:'Same result. New context.',execution:'SUCCEEDED',freshness:'CHANGED',verdict:'BLOCK',output:'$ inspect -- … your old record\nHEAD changed: commit A → commit B\nCONTENT_CHANGED: "arithmetic.py"',explanation:'SUCCEEDED belongs to the old run. The code has changed since then. No new tests run during inspection, so this does not tell you whether the new code passes.'},
 {kicker:'03 — EXPLICITLY RUN TESTS AGAIN',title:'Now the test really fails.',execution:'FAILED',freshness:'MATCH',verdict:'BLOCK',output:'$ record -- … your test command\nCommand completed with a nonzero exit code.\nNew record matches the changed snapshot.',explanation:'This time a new test command actually failed. MATCH describes the snapshot, not a successful test. The two are deliberately kept separate.'},
 {kicker:'04 — REPAIR AND MAKE A NEW RECORD',title:'Fresh evidence. Clear context.',execution:'SUCCEEDED',freshness:'MATCH',verdict:'PASS',output:'$ record -- … your test command\nCommand completed with exit code 0.\nNew record saved. Previous record preserved.',explanation:'After repairing the sample, a new successful run matches the current snapshot. PASS remains a limited check, not permission to deploy or merge.'}
];
const chineseExamples = [
 {kicker:'01 — 记录一次成功运行',title:'有结果，也有对应版本。',execution:'SUCCEEDED',freshness:'MATCH',verdict:'PASS',output:'$ record -- … 你的测试命令\n命令完成，退出码为 0。\n跟踪文件快照仍与当前仓库匹配。',explanation:'记录中的命令运行成功，且快照仍与当前仓库匹配。这不证明代码一定正确。'},
 {kicker:'02 — 检查旧记录',title:'结果没变，上下文变了。',execution:'SUCCEEDED',freshness:'CHANGED',verdict:'BLOCK',output:'$ inspect -- … 你的旧记录\nHEAD 已改变：提交 A → 提交 B\nCONTENT_CHANGED: "arithmetic.py"',explanation:'SUCCEEDED 描述的是旧运行。代码此后已经变化。检查时没有重新执行测试，因此无法据此判断新代码是否通过。'},
 {kicker:'03 — 明确重新执行测试',title:'这一次，测试真的失败了。',execution:'FAILED',freshness:'MATCH',verdict:'BLOCK',output:'$ record -- … 你的测试命令\n命令完成，退出码非 0。\n新记录与改变后的快照匹配。',explanation:'这次真正执行了新测试，而且测试失败了。MATCH 仅表示快照匹配，不表示测试通过。两种信息分别显示。'},
 {kicker:'04 — 修复并生成新记录',title:'新证据，对应新上下文。',execution:'SUCCEEDED',freshness:'MATCH',verdict:'PASS',output:'$ record -- … 你的测试命令\n命令完成，退出码为 0。\n已保存新记录，并保留旧记录。',explanation:'修复示例后，新一次成功运行与当前快照匹配。PASS 仍只表示有限检查通过，不是部署或合并的许可。'}
];
const examples = pageLanguage === 'zh' ? chineseExamples : englishExamples;
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
 try{await navigator.clipboard.writeText(document.getElementById('command').textContent);status.textContent=pageLanguage === 'zh' ? '已复制。请在解压后的 Phoenix 文件夹中运行。' : 'Copied. Run it inside the extracted Phoenix folder.';}
 catch{status.textContent=pageLanguage === 'zh' ? '无法访问剪贴板，请选中并复制上方命令。' : 'Clipboard unavailable. Select and copy the command above.';}
});

