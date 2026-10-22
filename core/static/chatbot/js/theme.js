(() => {
  const root = document.documentElement;
  const button = document.querySelector('[data-theme-toggle]');
  if (!button) return;
  const onlineState = document.querySelector('.topbar-actions .online-state');
  onlineState?.insertAdjacentElement('afterend', button);

  const updateButton = () => {
    const dark = root.dataset.theme === 'dark';
    document.querySelector('meta[name="theme-color"]')?.setAttribute('content', dark ? '#111713' : '#f7f7f4');
    button.setAttribute('aria-pressed', String(dark));
    button.setAttribute('aria-label', dark ? 'فعال‌کردن تم روشن' : 'فعال‌کردن تم تاریک');
    button.title = dark ? 'تغییر به تم روشن' : 'تغییر به تم تاریک';
  };

  updateButton();
  button.addEventListener('click', () => {
    const theme = root.dataset.theme === 'dark' ? 'light' : 'dark';
    root.dataset.theme = theme;
    try { localStorage.setItem('chatbot-theme', theme); } catch (_) {}
    updateButton();
  });
})();
