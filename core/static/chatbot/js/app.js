(() => {
  const stage = document.querySelector('.chat-stage');
  const form = document.querySelector('#chat-form');
  const input = document.querySelector('#prompt-input');
  const messages = document.querySelector('#messages');
  if (!stage || !form || !input || !messages) return;

  const appendMessage = (role, content) => {
    const template = document.querySelector(`#${role}-message-template`);
    const message = template?.content.firstElementChild?.cloneNode(true);
    if (!message) return;
    message.querySelector('[data-message-content]').textContent = content;
    messages.append(message);
  };

  const submitPrompt = (value) => {
    const prompt = value.trim();
    if (!prompt) return;
    stage.classList.add('has-messages');
    appendMessage('user', prompt);
    appendMessage('assistant', 'پیامت ثبت شد. با اتصال سرویس گفت‌وگو، پاسخ هوشمند اینجا نمایش داده می‌شود.');
    input.value = '';
    input.style.height = 'auto';
    input.focus();
  };

  form.addEventListener('submit', (event) => {
    event.preventDefault();
    submitPrompt(input.value);
  });
  input.addEventListener('input', () => {
    input.style.height = 'auto';
    input.style.height = `${Math.min(input.scrollHeight, 150)}px`;
  });
  input.addEventListener('keydown', (event) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      form.requestSubmit();
    }
  });
  document.querySelectorAll('[data-prompt]').forEach((button) => {
    button.addEventListener('click', () => {
      input.value = button.dataset.prompt || '';
      form.requestSubmit();
    });
  });
  document.querySelectorAll('[data-new-chat]').forEach((button) => {
    button.addEventListener('click', () => {
      messages.replaceChildren();
      stage.classList.remove('has-messages');
      input.value = '';
      input.focus();
      document.querySelector('#sidebar')?.classList.remove('is-open');
    });
  });
  document.querySelector('[data-menu-toggle]')?.addEventListener('click', () => {
    document.querySelector('#sidebar')?.classList.toggle('is-open');
  });
  document.addEventListener('keydown', (event) => {
    if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'k') {
      event.preventDefault();
      messages.replaceChildren();
      stage.classList.remove('has-messages');
      input.focus();
    }
  });
})();
