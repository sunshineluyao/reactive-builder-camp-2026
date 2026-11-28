// SPDX-License-Identifier: MIT
// Screen text only. Receipt JSON, transaction data and wallet state keep their original format.
(() => {
  'use strict';
  const query = new URLSearchParams(location.search);
  const requested = query.get('lang') || navigator.language || 'en';
  const lang = /^zh(?:-|$)/i.test(requested) ? 'zh' : 'en';
  const target = lang === 'en' ? 0 : 1;
  const pairs = window.PegPulseMessages || [];
  const labels = new Map();
  const templates = [];
  for (const pair of pairs) {
    const source = pair[1 - target];
    const translated = pair[target];
    labels.set(source, translated);
    if (/\{\d+\}/.test(source)) {
      const indexes = [];
      const pattern = source.split(/(\{\d+\})/).map(part => {
        if (!/^\{\d+\}$/.test(part)) return part.replace(/[.*+?^$(){}|[\]\\]/g, '\\$&');
        indexes.push(Number(part.slice(1, -1)));
        return '(.+?)';
      }).join('');
      templates.push([new RegExp('^' + pattern + '$', 's'), translated, indexes]);
    }
  }
  function text(value) {
    if (typeof value !== 'string' || !value.trim()) return value;
    const key = value.trim();
    let result = labels.get(key);
    if (result === undefined) {
      for (const [pattern, replacement, indexes] of templates) {
        const match = pattern.exec(key);
        if (!match) continue;
        result = replacement.replace(/\{(\d+)\}/g, (_, i) => {
          const argument = match[indexes.indexOf(Number(i)) + 1];
          return labels.get(argument) ?? argument;
        });
        break;
      }
    }
    return result === undefined ? value : value.replace(key, () => result);
  }
  function url(href, selected = lang) {
    const dest = new URL(href, location.href);
    dest.searchParams.set('lang', selected);
    return dest.href;
  }
  window.PegPulseLocale = {lang, text, url};
  document.documentElement.lang = lang === 'en' ? 'en' : 'zh-CN';
  document.title = text(document.title);
  const tree = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  for (let node = tree.nextNode(); node; node = tree.nextNode()) {
    if (!node.parentElement.closest('script, style, [data-language-switch]')) node.data = text(node.data);
  }
  for (const attr of ['aria-label', 'aria-valuetext', 'placeholder', 'title']) {
    for (const el of document.querySelectorAll('[' + attr + ']')) el.setAttribute(attr, text(el.getAttribute(attr)));
  }
  for (const a of document.querySelectorAll('a[href]')) {
    if (a.dataset.language) {
      const selected = a.dataset.language;
      a.href = url(location.href, selected);
      if (lang === selected) a.setAttribute('aria-current', 'page');
    } else if (/^(?:\.\/$|\.\.\/(?:site|visual|review|video)\/(?:[?#].*)?$)/.test(a.getAttribute('href'))) {
      a.href = url(a.href);
    } else if (a.dataset.projectGuide) {
      a.href = a.href.replace('/tree/main/track3', '/blob/main/track3/README' + (lang === 'en' ? '.en' : '') + '.md');
    }
  }
  for (const duplicate of document.querySelectorAll('[data-parallel-caption]')) {
    if (lang === 'zh') duplicate.style.display = 'none';
  }
})();
