(($) => {
  const stage = document.querySelector('.chat-stage');
  const form = document.querySelector('#chat-form');
  const input = document.querySelector('#prompt-input');
  const formType = document.querySelector("#form-type");
  const csrf_token = document.querySelector("#csrf-token");
  const messages = document.querySelector('#messages');
  if (!stage || !form || !input || !messages) return;
  const conversationId = document.querySelector('.main-panel')?.dataset.conversationId;
  let socket = null;
  let pendingReply = null;
  let isWaitingForReply = false;
  const sendButton = form.querySelector('button[type="submit"]');

  const setComposerLocked = (locked) => {
    isWaitingForReply = locked;
    input.disabled = locked;
    if (sendButton) sendButton.disabled = locked;
    form.setAttribute('aria-busy', String(locked));
  };

  const clearPendingReply = () => {
    pendingReply?.remove();
    pendingReply = null;
    setComposerLocked(false);
  };

  const scrollMessagesToBottom = () => {
    messages.scrollTop = messages.scrollHeight;
  };

  if (conversationId) {
    const actions = document.querySelector('.topbar-actions');
    const socketState = document.createElement('span');
    socketState.className = 'socket-state';
    socketState.setAttribute('role', 'status');
    socketState.setAttribute('aria-live', 'polite');
    socketState.innerHTML = '<i></i><span>در حال اتصال…</span>';
    actions?.prepend(socketState);

    const scheme = window.location.protocol === 'https:' ? 'wss://' : 'ws://';
    const socketUrl = scheme + window.location.host + '/ws/chat/' + encodeURIComponent(conversationId) + '/';
    socket = new WebSocket(socketUrl);
    const setSocketState = (state, label) => {
      socketState.classList.toggle('is-connected', state === 'connected');
      socketState.classList.toggle('is-disconnected', state === 'disconnected');
      socketState.querySelector('span').textContent = label;
    };

    socket.addEventListener('open', () => setSocketState('connected', 'متصل'));
    socket.addEventListener('close', () => {
      setSocketState('disconnected', 'ارتباط قطع شد');
      clearPendingReply();
    });
    socket.addEventListener('error', () => {
      setSocketState('disconnected', 'خطا در اتصال');
      clearPendingReply();
    });
    socket.addEventListener('message', (event) => {
      clearPendingReply();
      let content = event.data;
      try {
        const payload = JSON.parse(event.data);
        content = payload.content ?? payload.message ?? payload.response ?? payload.text ?? event.data;
      } catch (_) {
        // Current consumer responds with plain text; JSON responses are also supported.
      }
      appendMessage('assistant', String(content));
      scrollMessagesToBottom();
    });
  }

  const appendMessage = (role, content) => {
    const template = document.querySelector(`#${role}-message-template`);
    const message = template?.content.firstElementChild?.cloneNode(true);
    if (!message) return;
    const body = message.querySelector('[data-message-content]');
    if (window.ChatMarkdown) window.ChatMarkdown.render(body, content);
    else body.textContent = content;
    messages.append(message);
    return message;
  };

  document.querySelectorAll('#messages [data-message-content]').forEach((body) => {
    if (window.ChatMarkdown) window.ChatMarkdown.render(body, body.textContent);
  });

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
    if (!prompt || isWaitingForReply) return;
    if (!socket || socket.readyState !== WebSocket.OPEN) {
      const state = document.querySelector('.socket-state span');
      if (state) state.textContent = 'اتصال آماده نیست';
      return;
    }
    stage.classList.add('has-messages');
    try {
      socket.send(prompt);
      appendMessage('user', prompt);
      pendingReply = appendLoading('در حال دریافت پاسخ');
      cleareInput();
      setComposerLocked(true);
      scrollMessagesToBottom();
    } catch (_) {
      clearPendingReply();
      appendMessage('assistant', 'ارسال پیام انجام نشد. اتصال را بررسی کنید و دوباره تلاش کنید.');
    }
  };

  form.addEventListener('submit', (event) => {
    event.preventDefault();
    if (isWaitingForReply) return;

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
    //   stage.classList.remove('has-messages');
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
  if (conversationId) requestAnimationFrame(scrollMessagesToBottom);
})($);
