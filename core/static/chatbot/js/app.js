(($) => {
  const stage = document.querySelector('.chat-stage');
  const form = document.querySelector('#chat-form');
  const input = document.querySelector('#prompt-input');
  const formType = document.querySelector("#form-type");
  const csrf_token = document.querySelector("#csrf-token");
  const messages = document.querySelector('#messages');
  if (!stage || !form || !input || !messages) return;

  const appendMessage = (role, content) => {
    const template = document.querySelector(`#${role}-message-template`);
    const message = template?.content.firstElementChild?.cloneNode(true);
    if (!message) return;
    message.querySelector('[data-message-content]').textContent = content;
    messages.append(message);
    return message;
  };

  const appendLoading = (label = 'در حال بارگذاری', fullscreen = false) => {
    const template = document.querySelector(fullscreen ? '#fullscreen-loading-template' : '#loading-template');
    const loading = template?.content.firstElementChild?.cloneNode(true);
    if (!loading) return null;
    loading.setAttribute('aria-label', label);
    (fullscreen ? document.body : messages).append(loading);
    return loading;
  };

  const cleareInput = () => {
    input.value = '';
    input.style.height = 'auto';
    input.focus();
  }

  const createChat = (first_message) =>{
    const promt = first_message.trim()

    if (!promt) return;

    const loading = appendLoading('در حال ساخت گفت‌وگو', true);
    form.querySelector('button[type="submit"]')?.setAttribute('disabled', 'disabled');
    $.ajax({
        method : 'POST',
        url : '/chat/api/v1/conversation/',
        data : {
            message : input.value,
            csrfmiddlewaretoken : csrf_token.value
        },
        success : function(res){
            window.location.href = `/chat/${res.converstation_id}/`;
        },
        error: function(){
            loading?.remove();
            form.querySelector('button[type="submit"]')?.removeAttribute('disabled');
        }
    })

    cleareInput();
  }

  const submitPrompt = (value) => {
    const prompt = value.trim();
    if (!prompt) return;
    stage.classList.add('has-messages');
    appendMessage('user', prompt);
    appendMessage('assistant', 'پیامت ثبت شد. با اتصال سرویس گفت‌وگو، پاسخ هوشمند اینجا نمایش داده می‌شود.');
    cleareInput();
  };

  form.addEventListener('submit', (event) => {
    event.preventDefault();

    formType.value == 'create' ? createChat(input.value) : submitPrompt(input.value);
    
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
      formType.value = 'create';
      input.value = '';
      input.focus();
      document.querySelector('#sidebar')?.classList.remove('is-open');
    });
  });
  document.querySelector('[data-menu-toggle]')?.addEventListener('click', () => {
    document.querySelector('#sidebar')?.classList.toggle('is-open');
  });
  document.querySelector('[data-sidebar-close]')?.addEventListener('click', () => {
    document.querySelector('#sidebar')?.classList.remove('is-open');
  });
  document.addEventListener('keydown', (event) => {
    if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'k') {
      event.preventDefault();
      messages.replaceChildren();
      stage.classList.remove('has-messages');
      input.focus();
    }
  });
})($);
