// ZipbabBot Chrome Extension - Dashboard Bridge
(function() {
  function markActive() {
    try {
      if (document.documentElement) {
        document.documentElement.setAttribute('data-zipbabbot-extension', 'true');
        document.documentElement.setAttribute('data-zipbabbot-installed', 'true');
        document.documentElement.setAttribute('data-zipbabbot-version', '1.0.0');
      }
      if (document.body) {
        document.body.setAttribute('data-zipbabbot-extension', 'true');
        document.body.setAttribute('data-zipbabbot-installed', 'true');
      }
      window.__ZIPBABBOT_EXTENSION_ACTIVE__ = true;
      window.hasZipbabBotExtension = true;
      try {
        localStorage.setItem('zipbabbot_extension_installed', 'true');
        sessionStorage.setItem('zipbabbot_extension_installed', 'true');
      } catch(e) {}

      // Inject script into main world so page JS can directly read window property
      try {
        const script = document.createElement('script');
        script.textContent = `
          window.__ZIPBABBOT_EXTENSION_ACTIVE__ = true;
          window.hasZipbabBotExtension = true;
          try {
            localStorage.setItem('zipbabbot_extension_installed', 'true');
            sessionStorage.setItem('zipbabbot_extension_installed', 'true');
          } catch(e) {}
        `;
        (document.head || document.documentElement || document.body).appendChild(script);
        script.remove();
      } catch(e) {}

      window.postMessage({ type: 'ZIPBABBOT_EXTENSION_READY', version: '1.0.0' }, '*');
      window.dispatchEvent(new CustomEvent('zipbabbot-extension-ready', { detail: { version: '1.0.0' } }));
    } catch(e) {}
  }

  // 1. Mark DOM attribute immediately and on DOM load
  markActive();
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', markActive);
  }
  window.addEventListener('load', markActive);

  // 2. Listen for messages from webpage
  window.addEventListener('message', function(event) {
    if (event.source !== window || !event.data) return;
    
    if (event.data.type === 'ZIPBABBOT_PING_EXTENSION') {
      markActive();
      window.postMessage({ type: 'ZIPBABBOT_PONG_EXTENSION', version: '1.0.0' }, '*');
    } else if (event.data.type === 'ZIPBABBOT_START_BATCH') {
      const items = event.data.items || [];
      chrome.runtime.sendMessage({
        action: 'START_BATCH_ADD',
        items: items
      });
    } else if (event.data.type === 'ZIPBABBOT_STOP_BATCH') {
      chrome.runtime.sendMessage({
        action: 'STOP_BATCH_ADD'
      });
    }
  });

  // 3. Relay messages from extension background to webpage
  chrome.runtime.onMessage.addListener(function(msg, sender, sendResponse) {
    if (msg && msg.type && msg.type.startsWith('ZIPBABBOT_')) {
      window.postMessage(msg, '*');
    }
  });
})();
