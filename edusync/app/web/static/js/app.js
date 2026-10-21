/* EduSynC portal - shared helpers. */
(function () {
  'use strict';

  const TOKEN_KEY = 'edusync_token';

  function token() {
    try {
      return localStorage.getItem(TOKEN_KEY) || '';
    } catch (error) {
      return '';
    }
  }

  function setToken(value) {
    try {
      localStorage.setItem(TOKEN_KEY, value);
    } catch (error) {
      /* storage unavailable - the session simply will not persist */
    }
  }

  function clearToken() {
    try {
      localStorage.removeItem(TOKEN_KEY);
      localStorage.removeItem(TOKEN_KEY + '_refresh');
    } catch (error) {
      /* ignore */
    }
  }

  function role() {
    try {
      return localStorage.getItem('edusync_role') || '';
    } catch (error) {
      return '';
    }
  }

  async function api(path, options) {
    const settings = Object.assign({ headers: {} }, options || {});
    settings.headers = Object.assign({}, settings.headers);
    const bearer = token();
    if (bearer) {
      settings.headers['Authorization'] = 'Bearer ' + bearer;
    }
    if (settings.body && !(settings.body instanceof FormData)) {
      settings.headers['Content-Type'] = 'application/json';
    }
    const response = await fetch(path, settings);
    if (response.status === 401) {
      clearToken();
    }
    return response;
  }

  function escapeHtml(value) {
    return String(value === null || value === undefined ? '' : value)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }

  function formatNumber(value) {
    return Number(value || 0).toLocaleString('en-IN');
  }

  function element(tag, className, text) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined && text !== null) node.textContent = text;
    return node;
  }

  window.EduSync = {
    token: token,
    setToken: setToken,
    clearToken: clearToken,
    role: role,
    api: api,
    escapeHtml: escapeHtml,
    formatNumber: formatNumber,
    element: element
  };
})();
