(($) => {
  const stage = document.querySelector('.chat-stage');
  const form = document.querySelector('#chat-form');
  const input = document.querySelector('#prompt-input');
  const formType = document.querySelector("#form-type");
  const csrf_token = document.querySelector("#csrf-token");
  const messages = document.querySelector('#messages');
  const fileInput = document.querySelector('#file-input');
  const filePicker = document.querySelector('.composer .tool-button');
  const fileAttachments = document.querySelector('#file-attachments');
  const fileList = document.querySelector('#file-attachments-list');
  if (!stage || !form || !input || !messages) return;
  const mainPanel = document.querySelector('.main-panel');
  let conversationId = mainPanel?.dataset.conversationId || '';
  let conversationPk = mainPanel?.dataset.conversationPk || '';
  let socket = null;
  let socketState = null;
  let pendingReply = null;
  let isWaitingForReply = false;
  let isUploadingFiles = false;
  const selectedFiles = [];
  const sendButton = form.querySelector('button[type="submit"]');
  const fileUploadEndpoint = fileInput?.dataset.uploadEndpoint;
  if (fileUploadEndpoint && filePicker) {
    filePicker.setAttribute('aria-label', 'انتخاب چند فایل');
    filePicker.title = 'انتخاب چند فایل';
  }

  const setComposerLocked = (locked) => {
    input.disabled = locked;
    if (sendButton) sendButton.disabled = locked;
    if (filePicker) filePicker.disabled = locked;
    form.setAttribute('aria-busy', String(locked));
  };

  const clearPendingReply = () => {
    pendingReply?.remove();
    pendingReply = null;
    isWaitingForReply = false;
    setComposerLocked(isUploadingFiles);
  };

  const scrollMessagesToBottom = () => {
    messages.scrollTop = messages.scrollHeight;
  };

  const formatFileSize = (bytes) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  const renderSelectedFiles = () => {
    if (!fileList || !fileAttachments) return;
    fileList.replaceChildren();
    fileAttachments.hidden = selectedFiles.length === 0;

    selectedFiles.forEach((entry, index) => {
      const file = entry.file;
      const item = document.createElement('div');
      item.className = `file-attachment is-${entry.status}`;

      const badge = document.createElement('span');
      badge.className = 'file-attachment-icon';
      badge.setAttribute('aria-hidden', 'true');
      const extension = file.name.includes('.') ? file.name.split('.').pop() : '';
      badge.textContent = (extension || 'FILE').slice(0, 4).toUpperCase();

      const details = document.createElement('span');
      details.className = 'file-attachment-details';
      const name = document.createElement('strong');
      name.textContent = file.name;
      const size = document.createElement('small');
      size.textContent = entry.status === 'uploaded' ? 'ذخیره شد' :
        entry.status === 'uploading' ? 'در حال آپلود…' :
          entry.status === 'error' ? (entry.error || 'آپلود ناموفق') : formatFileSize(file.size);
      size.className = 'file-attachment-status';
      details.append(name, size);
      item.append(badge, details);

      if (entry.status !== 'uploaded' && entry.status !== 'uploading') {
        const remove = document.createElement('button');
        remove.type = 'button';
        remove.className = 'file-attachment-remove';
        remove.dataset.removeFile = String(index);
        remove.setAttribute('aria-label', `حذف فایل ${file.name} از انتخاب`);
        remove.textContent = '×';
        item.append(remove);
      }
      fileList.append(item);
    });
  };

  if (fileInput && filePicker) {
    filePicker.addEventListener('click', () => fileInput.click());
    fileInput.addEventListener('change', () => {
      Array.from(fileInput.files || []).forEach((file) => {
        const alreadySelected = selectedFiles.some((selected) =>
          selected.file.name === file.name && selected.file.size === file.size && selected.file.lastModified === file.lastModified
        );
        if (!alreadySelected) selectedFiles.push({ file, status: 'queued', error: '' });
      });
      fileInput.value = '';
      renderSelectedFiles();
    });
    fileList?.addEventListener('click', (event) => {
      const removeButton = event.target.closest('[data-remove-file]');
      if (!removeButton) return;
      selectedFiles.splice(Number(removeButton.dataset.removeFile), 1);
      renderSelectedFiles();
      filePicker.focus();
    });
  }

  const setSocketState = (state, label) => {
    if (!socketState) return;
    socketState.classList.toggle('is-connected', state === 'connected');
    socketState.classList.toggle('is-disconnected', state === 'disconnected');
    socketState.querySelector('span').textContent = label;
  };

  const connectSocket = () => {
    if (!conversationId || (socket && socket.readyState < WebSocket.CLOSING)) return;
    const actions = document.querySelector('.topbar-actions');
    if (!socketState) {
      socketState = document.createElement('span');
      socketState.className = 'socket-state';
      socketState.setAttribute('role', 'status');
      socketState.setAttribute('aria-live', 'polite');
      socketState.innerHTML = '<i></i><span>در حال اتصال…</span>';
      actions?.prepend(socketState);
    }

    const scheme = window.location.protocol === 'https:' ? 'wss://' : 'ws://';
    const socketUrl = scheme + window.location.host + '/ws/chat/' + encodeURIComponent(conversationId) + '/';
    socket = new WebSocket(socketUrl);
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
  };
  if (conversationId) connectSocket();

  const appendMessage = (role, content, attachments = []) => {
    const template = document.querySelector(`#${role}-message-template`);
    const message = template?.content.firstElementChild?.cloneNode(true);
    if (!message) return;
    const body = message.querySelector('[data-message-content]');
    if (window.ChatMarkdown) window.ChatMarkdown.render(body, content);
    else body.textContent = content;
    if (attachments.length) {
      const attachmentList = document.createElement('div');
      attachmentList.className = 'message-attachments';
      attachmentList.setAttribute('aria-label', 'فایل‌های پیوست‌شده');
      attachments.forEach((attachment) => {
        const item = document.createElement('div');
        item.className = 'file-attachment is-uploaded';
        if (attachment.id) item.dataset.fileId = String(attachment.id);
        const badge = document.createElement('span');
        badge.className = 'file-attachment-icon';
        badge.setAttribute('aria-hidden', 'true');
        const name = attachment.original_name || attachment.name || attachment.file?.name || 'فایل';
        const extension = name.includes('.') ? name.split('.').pop() : '';
        badge.textContent = (extension || 'FILE').slice(0, 4).toUpperCase();
        const details = document.createElement('span');
        details.className = 'file-attachment-details';
        const title = document.createElement('strong');
        title.textContent = name;
        const size = document.createElement('small');
        size.className = 'file-attachment-status';
        size.textContent = formatFileSize(Number(attachment.size ?? attachment.file?.size) || 0);
        details.append(title, size);
        item.append(badge, details);
        attachmentList.append(item);
      });
      message.append(attachmentList);
    }
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

  const uploadPendingFiles = async (conversationPkValue) => {
    if (!fileUploadEndpoint || !conversationPkValue) return false;
    let success = true;
    for (const entry of selectedFiles) {
      if (entry.status === 'uploaded') continue;
      entry.status = 'uploading';
      entry.error = '';
      renderSelectedFiles();
      const data = new FormData();
      data.append('conversation', String(conversationPkValue));
      data.append('file', entry.file, entry.file.name);
      data.append('original_name', entry.file.name);
      data.append('mime_type', entry.file.type || 'application/octet-stream');
      data.append('size', String(entry.file.size));
      try {
        const response = await fetch(fileUploadEndpoint, {
          method: 'POST', body: data, credentials: 'same-origin',
          headers: { 'X-CSRFToken': csrf_token.value }
        });
        if (!response.ok) {
          const payload = await response.json().catch(() => ({}));
          const detail = payload.detail || Object.values(payload).flat().join(' ');
          throw new Error(detail || 'آپلود ناموفق بود');
        }
        const uploadedFile = await response.json();
        entry.id = uploadedFile.id;
        entry.status = 'uploaded';
      } catch (error) {
        entry.status = 'error';
        entry.error = error.message || 'آپلود ناموفق بود';
        success = false;
      }
      renderSelectedFiles();
    }
    return success;
  };

  const setUploadLock = (locked) => {
    isUploadingFiles = locked;
    setComposerLocked(locked || isWaitingForReply);
  };

  const createChat = (firstMessage) => {
    const prompt = firstMessage.trim();
    if (!prompt && !selectedFiles.length) return;
    const loading = appendLoading('در حال ساخت گفت‌وگو', true);
    setUploadLock(true);
    const data = { csrfmiddlewaretoken: csrf_token.value };
    if (prompt) data.message = prompt;
    $.ajax({
      method: 'POST', url: '/chat/api/v1/conversation/', data,
      success: async (res) => {
        conversationId = res.converstation_id;
        conversationPk = res.id;
        mainPanel.dataset.conversationId = conversationId;
        mainPanel.dataset.conversationPk = conversationPk;
        if (selectedFiles.length) {
          const uploaded = await uploadPendingFiles(conversationPk);
          if (!uploaded) {
            loading?.remove();
            formType.value = 'append';
            stage.classList.add('has-messages');
            if (prompt) appendMessage('user', prompt, selectedFiles.filter((item) => item.status === 'uploaded'));
            appendMessage('assistant', 'گفت‌وگو ساخته شد، اما آپلود بعضی فایل‌ها ناموفق بود. فایل‌های ناموفق را دوباره تلاش کنید.');
            cleareInput();
            connectSocket();
            setUploadLock(false);
            return;
          }
        }
        window.location.href = `/chat/${conversationId}/`;
      },
      error: () => {
        loading?.remove();
        setUploadLock(false);
        appendMessage('assistant', 'ساخت گفت‌وگو انجام نشد. دوباره تلاش کنید.');
      }
    });
  };

  const submitPrompt = async (value) => {
    const prompt = value.trim();
    if ((!prompt && !selectedFiles.length) || isWaitingForReply || isUploadingFiles) return;
    if (selectedFiles.length) {
      setUploadLock(true);
      const uploaded = await uploadPendingFiles(conversationPk);
      setUploadLock(false);
      if (!uploaded) {
        appendMessage('assistant', 'آپلود بعضی فایل‌ها ناموفق بود. فایل‌های ناموفق را دوباره تلاش کنید.');
        return;
      }
    }
    stage.classList.add('has-messages');
    if (!prompt) {
      const data = JSON.stringify({"text" : prompt, "attachments" : selectedFiles.map(item=>item.id)})
      socket.send(data);
      appendMessage('user', '', selectedFiles.filter((item) => item.status === 'uploaded').map((item) => ({
        id: item.id, name: item.file.name, size: item.file.size
      })));
      selectedFiles.splice(0);
      renderSelectedFiles();
      scrollMessagesToBottom();
      pendingReply = appendLoading('در حال دریافت پاسخ');
      cleareInput();
      isWaitingForReply = true;
      setComposerLocked(true);
      scrollMessagesToBottom();
      return;
    }
    if (!socket || socket.readyState !== WebSocket.OPEN) {
      setSocketState('disconnected', 'اتصال آماده نیست');
      return;
    }
    try {
      const data = JSON.stringify({"text" : prompt, "attachments" : selectedFiles.map(item=>item.id)})
      socket.send(data);
      const uploadedNames = selectedFiles.filter((item) => item.status === 'uploaded').map((item) => item.file.name);
      appendMessage('user', prompt, selectedFiles.filter((item) => item.status === 'uploaded').map((item) => ({
        id: item.id, name: item.file.name, size: item.file.size
      })));
      selectedFiles.splice(0);
      renderSelectedFiles();
      pendingReply = appendLoading('در حال دریافت پاسخ');
      cleareInput();
      isWaitingForReply = true;
      setComposerLocked(true);
      scrollMessagesToBottom();
    } catch (_) {
      clearPendingReply();
      appendMessage('assistant', 'ارسال پیام انجام نشد. اتصال را بررسی کنید و دوباره تلاش کنید.');
    }
  };

  form.addEventListener('submit', (event) => {
    event.preventDefault();
    if (isWaitingForReply || isUploadingFiles) return;
    formType.value === 'create' ? createChat(input.value) : submitPrompt(input.value);
    
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
