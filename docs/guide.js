let noticeTimer;
document.querySelectorAll('[data-copy]').forEach(button => {
 button.addEventListener('click', async () => {
  const target = document.getElementById(button.dataset.copy);
  const notice = document.getElementById('guide-copy-status');
  try {
   await navigator.clipboard.writeText(target.textContent);
   notice.textContent = document.body.dataset.copySuccess;
  } catch {
   notice.textContent = document.body.dataset.copyFailure;
  }
  clearTimeout(noticeTimer);
  noticeTimer = setTimeout(() => { notice.textContent = ''; }, 7000);
 });
});
