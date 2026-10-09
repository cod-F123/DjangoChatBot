(() => {
  const allowedTags = [
    'a', 'blockquote', 'br', 'code', 'del', 'em', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
    'hr', 'li', 'ol', 'p', 'pre', 'strong', 'table', 'tbody', 'td', 'th', 'thead', 'tr', 'ul'
  ];
  const allowedAttributes = ['href', 'title', 'class'];

  const render = (container, markdown) => {
    const source = String(markdown ?? '');
    if (!window.marked || !window.DOMPurify) {
      container.textContent = source;
      return;
    }

    const html = window.marked.parse(source, { gfm: true, breaks: true });
    container.innerHTML = window.DOMPurify.sanitize(html, {
      ALLOWED_TAGS: allowedTags,
      ALLOWED_ATTR: allowedAttributes,
      FORBID_ATTR: ['style'],
      RETURN_TRUSTED_TYPE: false
    });
    container.classList.add('markdown-body');
  };

  window.ChatMarkdown = { render };
})();
