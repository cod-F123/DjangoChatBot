(() => {
  const allowedTags = [
    'a', 'blockquote', 'br', 'code', 'del', 'em', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
    'hr', 'li', 'ol', 'p', 'pre', 'strong', 'table', 'tbody', 'td', 'th', 'thead', 'tr', 'ul'
  ];
  const allowedAttributes = ['href', 'title', 'class'];
  const mathPattern = /(\$\$[\s\S]+?\$\$|\$[^$\n]+\$|\\\[[\s\S]+?\\\]|\\\([\s\S]+?\\\))/g;

  const maskMath = (source) => {
    const expressions = [];
    const masked = source.replace(mathPattern, (expression) => {
      const token = `KATEXMATHPLACEHOLDER${expressions.length}END`;
      expressions.push(expression);
      return token;
    });
    return { masked, expressions };
  };

  const restoreMath = (container, expressions) => {
    if (!expressions.length) return;
    const walker = document.createTreeWalker(container, NodeFilter.SHOW_TEXT);
    const textNodes = [];
    while (walker.nextNode()) textNodes.push(walker.currentNode);
    const tokenPattern = /KATEXMATHPLACEHOLDER(\d+)END/g;

    textNodes.forEach((node) => {
      if (!tokenPattern.test(node.nodeValue)) return;
      tokenPattern.lastIndex = 0;
      const fragment = document.createDocumentFragment();
      let start = 0;
      let match;
      while ((match = tokenPattern.exec(node.nodeValue))) {
        fragment.append(document.createTextNode(node.nodeValue.slice(start, match.index)));
        fragment.append(document.createTextNode(expressions[Number(match[1])]));
        start = match.index + match[0].length;
      }
      fragment.append(document.createTextNode(node.nodeValue.slice(start)));
      node.replaceWith(fragment);
    });
  };

  const render = (container, markdown) => {
    const source = String(markdown ?? '');
    if (!window.marked || !window.DOMPurify) {
      container.textContent = source;
      return;
    }

    const { masked, expressions } = maskMath(source);
    const html = window.marked.parse(masked, { gfm: true, breaks: true });
    container.innerHTML = window.DOMPurify.sanitize(html, {
      ALLOWED_TAGS: allowedTags,
      ALLOWED_ATTR: allowedAttributes,
      FORBID_ATTR: ['style'],
      RETURN_TRUSTED_TYPE: false
    });
    container.classList.add('markdown-body');
    restoreMath(container, expressions);
    if (window.renderMathInElement) {
      window.renderMathInElement(container, {
        delimiters: [
          { left: '$$', right: '$$', display: true },
          { left: '\\[', right: '\\]', display: true },
          { left: '\\(', right: '\\)', display: false },
          { left: '$', right: '$', display: false }
        ],
        throwOnError: false,
        trust: false
      });
    }
  };

  window.ChatMarkdown = { render };
})();
