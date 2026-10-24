// ZipbabBot Chrome Extension - Background Service Worker
let isRunning = false;
let autoTabId = null;

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.action === 'START_BATCH_ADD') {
    if (isRunning) return;
    isRunning = true;
    runBatchAdd(message.items, sender.tab ? sender.tab.id : null);
  } else if (message.action === 'STOP_BATCH_ADD') {
    isRunning = false;
  }
});

async function runBatchAdd(items, sourceTabId) {
  if (!items || items.length === 0) {
    isRunning = false;
    return;
  }

  autoTabId = null;

  for (let i = 0; i < items.length; i++) {
    if (!isRunning) break;
    const item = items[i];

    // 1. Report progress to dashboard tab
    sendProgress(sourceTabId, {
      type: 'ZIPBABBOT_PROGRESS',
      step: i + 1,
      total: items.length,
      item: item,
      status: 'SEARCHING'
    });

    // 2. Process item
    const result = await processSingleItem(item, i);

    // 3. Report result to dashboard tab
    sendProgress(sourceTabId, {
      type: 'ZIPBABBOT_ITEM_DONE',
      index: (item.index !== undefined) ? item.index : i,
      query: item.query,
      success: result.success,
      reason: result.reason,
      details: result
    });

    // Cooldown between items
    if (i < items.length - 1 && isRunning) {
      await wait(1200);
    }
  }

  // Finished! Open Coupang Cart
  if (isRunning) {
    try {
      if (autoTabId) {
        await chrome.tabs.update(autoTabId, {
          url: 'https://cart.coupang.com/cartView.pang',
          active: true
        });
      } else {
        await chrome.tabs.create({
          url: 'https://cart.coupang.com/cartView.pang',
          active: true
        });
      }
    } catch (e) {}

    sendProgress(sourceTabId, {
      type: 'ZIPBABBOT_COMPLETE'
    });
  }

  isRunning = false;
}

async function processSingleItem(item, itemIndex) {
  const searchUrl = `https://www.coupang.com/np/search?q=${encodeURIComponent(item.query)}&channel=user`;

  try {
    // Step 1: Ensure automation tab is navigated to search page
    if (!autoTabId) {
      const tab = await chrome.tabs.create({
        url: searchUrl,
        active: false
      });
      autoTabId = tab.id;
      await waitForTabUrlAndComplete(autoTabId, '/np/search', 15000);
    } else {
      try {
        await chrome.tabs.get(autoTabId);
        await navigateTab(autoTabId, searchUrl, '/np/search', 12000);
      } catch (err) {
        const tab = await chrome.tabs.create({
          url: searchUrl,
          active: false
        });
        autoTabId = tab.id;
        await waitForTabUrlAndComplete(autoTabId, '/np/search', 15000);
      }
    }

    // Step 2: Extract best 1-person product link from search results (retries up to 12 times)
    let prodUrl = null;
    let lastExtractError = null;

    for (let r = 0; r < 12; r++) {
      if (!isRunning) return { success: false, reason: '중단됨' };

      try {
        const results = await chrome.scripting.executeScript({
          target: { tabId: autoTabId },
          func: extractBestProductFromSearch,
          args: [item.qty || 1]
        });

        if (results && results[0] && results[0].result) {
          const evalResult = results[0].result;
          if (evalResult.url) {
            prodUrl = evalResult.url;
            break;
          }
          if (evalResult.error) {
            lastExtractError = evalResult.error;
          }
        }
      } catch (err) {
        lastExtractError = err.message;
      }

      await wait(600);
    }

    if (!prodUrl) {
      console.warn(`[ZipbabBot] Product URL not found for '${item.name}':`, lastExtractError);
      return { success: false, reason: lastExtractError || '검색 결과 없음' };
    }

    // Step 3: Navigate directly to product detail page!
    await navigateTab(autoTabId, prodUrl, '/vp/products/', 12000);

    // Step 4: Click add-to-cart button (retries up to 12 times)
    let addSuccess = false;
    let lastAddError = null;

    for (let r = 0; r < 12; r++) {
      if (!isRunning) return { success: false, reason: '중단됨' };

      try {
        const results = await chrome.scripting.executeScript({
          target: { tabId: autoTabId },
          func: clickAddToCartInProductPage,
          args: [item.qty || 1]
        });

        if (results && results[0] && results[0].result) {
          const evalResult = results[0].result;
          if (evalResult.success) {
            addSuccess = true;
            break;
          }
          if (evalResult.error) {
            lastAddError = evalResult.error;
          }
        }
      } catch (err) {
        lastAddError = err.message;
      }

      await wait(600);
    }

    if (!addSuccess) {
      console.warn(`[ZipbabBot] Failed to click cart button for '${item.name}':`, lastAddError);
      return { success: false, reason: lastAddError || '담기 버튼 미발견' };
    }

    return { success: true };
  } catch (err) {
    console.error(`[ZipbabBot] Error adding item '${item.name}':`, err);
    return { success: false, reason: err.message || '오류 발생' };
  }
}

// Injected into Coupang search page
function extractBestProductFromSearch(targetQty) {
  if (!window.location.href.includes('/np/search')) {
    return { error: 'WAIT_SEARCH_PAGE', currentUrl: window.location.href };
  }

  let cards = Array.from(document.querySelectorAll('li.search-product, li.baby-product, .search-product'));

  // Fallback: If no li elements, find all /vp/products/ links
  if (!cards.length) {
    const rawLinks = Array.from(document.querySelectorAll('a[href*="/vp/products/"]'));
    const validLinks = rawLinks.filter(a => !a.href.includes('view_together') 
                && !a.closest('.recently-viewed-item') 
                && !a.closest('#recent-view'));
    if (!validLinks.length) {
      return { error: 'NO_PRODUCTS_FOUND' };
    }
    cards = validLinks.map(a => a.closest('li') || a.parentElement || a);
  }

  function parseCard(card) {
    const linkEl = card.tagName === 'A' ? card : card.querySelector('a.search-product-link, a[href*="/vp/products/"], a');
    if (!linkEl) return null;

    let href = linkEl.getAttribute('href') || linkEl.href;
    if (!href || !href.includes('/vp/products/')) return null;
    if (href.startsWith('/')) href = window.location.origin + href;

    // Use textContent so background/hidden tabs return valid strings
    const titleEl = card.querySelector('.name, .title, h2, h3') || linkEl;
    const title = (titleEl.textContent || card.textContent || '').trim();
    const fullText = (card.textContent || '').trim();

    const isSoldOut = fullText.includes('일시품절') || fullText.includes('품절');
    const isFresh = card.querySelector('.badge-rocket-fresh, .rocket-fresh-badge, [class*="fresh"]') !== null || fullText.includes('로켓프레시');
    const isRocket = card.querySelector('.badge.rocket, .rocket-badge, [class*="rocket"]') !== null || fullText.includes('로켓배송');

    return {
      href: href,
      title: title,
      fullText: fullText,
      isSoldOut: isSoldOut,
      isFresh: isFresh,
      isRocket: isRocket
    };
  }

  const parsedItems = cards.map(parseCard).filter(Boolean);
  if (!parsedItems.length) {
    return { error: 'NO_PARSEABLE_CARDS' };
  }

  // Filter out sold out items if non-sold-out items exist
  let candidates = parsedItems.filter(p => !p.isSoldOut);
  if (!candidates.length) candidates = parsedItems;

  function scoreItem(item) {
    const text = item.fullText;
    let score = 0;

    if (text.includes('박스') || text.includes('대용량') || text.includes('벌크') || text.includes('업소용') || text.includes('식자재')) {
      score -= 1000;
    }
    if (text.match(/([2-9]|[0-9]{2,}) *kg/) && !text.includes('쌀') && !text.includes('김치') && !text.includes('양파')) {
      score -= 1200;
    }
    const bulkMatch = text.match(/([4-9]|[0-9]{2,}) *(개|모|팩|봉|입|캔)/);
    if (bulkMatch && targetQty < 4) {
      score -= 1000;
    }

    if (targetQty === 1) {
      if (text.match(/1 *(개|모|단|봉|팩|통|병|입|캔)/)) score += 500;
      else if (text.match(/[23] *(개|모|단|봉|팩|구|입|캔)/)) score += 100;
    } else if (targetQty === 2) {
      if (text.match(/2 *(개|모|단|봉|팩|통|병|입|캔)/)) score += 600;
      else if (text.match(/1 *(개|모|단|봉|팩|통|병|입|캔)/)) score += 500;
    }

    if (item.isFresh) score += 400;
    else if (item.isRocket) score += 250;

    if (text.includes('광고')) score -= 200;

    return score;
  }

  candidates.sort((a, b) => scoreItem(b) - scoreItem(a));
  return { url: candidates[0].href, title: candidates[0].title };
}

// Injected into Coupang product detail page
function clickAddToCartInProductPage(targetQty) {
  if (!window.location.href.includes('/vp/products/')) {
    return { error: 'WAIT_PRODUCT_PAGE', currentUrl: window.location.href };
  }

  const titleEl = document.querySelector('h1.prod-buy-header__title, .prod-title, .title');
  const titleText = titleEl ? (titleEl.textContent || '').trim() : '';

  let bundleSize = 1;
  const bundleMatch = titleText.match(/([2-9])\s*(개|모|팩|봉|입|캔|병|구)/);
  if (bundleMatch) {
    bundleSize = parseInt(bundleMatch[1], 10);
  }

  let finalQty = targetQty;
  if (bundleSize >= targetQty) finalQty = 1;
  else if (bundleSize > 1) finalQty = Math.max(1, Math.ceil(targetQty / bundleSize));

  // Adjust quantity input
  const qtyInput = document.querySelector('input.prod-quantity__input, input.prod-buy-quantity, input.quantity-input');
  if (qtyInput && parseInt(qtyInput.value, 10) !== finalQty) {
    qtyInput.value = String(finalQty);
    qtyInput.dispatchEvent(new Event('input', { bubbles: true }));
    qtyInput.dispatchEvent(new Event('change', { bubbles: true }));
  }

  // Find add-to-cart button
  const btn = document.querySelector('.prod-cart-btn, .prod-buy-cart, .btn-cart, .btnCart') ||
              Array.from(document.querySelectorAll('button, a')).find(b => {
                const t = (b.textContent || '').trim();
                return (t.includes('장바구니 담기') || t === '장바구니') && !b.disabled;
              });

  if (!btn) {
    const isSoldOut = document.body.textContent.includes('일시품절') || document.body.textContent.includes('품절');
    if (isSoldOut) {
      return { error: '품절' };
    }
    return { error: '버튼 미발견' };
  }

  if (btn.disabled) {
    return { error: '버튼 비활성화' };
  }

  try {
    btn.scrollIntoView({ behavior: 'instant', block: 'center' });
    btn.focus();
  } catch(e) {}

  btn.click();
  btn.dispatchEvent(new MouseEvent('mousedown', { bubbles: true, cancelable: true, view: window }));
  btn.dispatchEvent(new MouseEvent('mouseup', { bubbles: true, cancelable: true, view: window }));
  btn.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true, view: window }));

  return { success: true, finalQty: finalQty, title: titleText };
}

function sendProgress(tabId, msg) {
  if (tabId) {
    chrome.tabs.sendMessage(tabId, msg).catch(() => {});
  }
}

function navigateTab(tabId, url, expectedSubstring, maxWaitMs = 12000) {
  return new Promise((resolve) => {
    let resolved = false;

    const cleanup = () => {
      if (!resolved) {
        resolved = true;
        clearTimeout(timer);
        chrome.tabs.onUpdated.removeListener(listener);
        setTimeout(resolve, 800);
      }
    };

    const timer = setTimeout(cleanup, maxWaitMs);

    const listener = (updatedTabId, changeInfo, tab) => {
      if (updatedTabId !== tabId) return;

      const currentUrl = (tab && tab.url) || (changeInfo && changeInfo.url) || '';
      const urlMatches = expectedSubstring ? currentUrl.includes(expectedSubstring) : true;

      if (changeInfo.status === 'complete' && urlMatches) {
        cleanup();
      }
    };

    chrome.tabs.onUpdated.addListener(listener);
    chrome.tabs.update(tabId, { url: url }).catch(() => cleanup());
  });
}

function waitForTabUrlAndComplete(tabId, expectedSubstring, maxWaitMs = 15000) {
  return new Promise((resolve) => {
    let resolved = false;

    const cleanup = () => {
      if (!resolved) {
        resolved = true;
        clearTimeout(timer);
        chrome.tabs.onUpdated.removeListener(listener);
        setTimeout(resolve, 800);
      }
    };

    const timer = setTimeout(cleanup, maxWaitMs);

    const listener = (updatedTabId, changeInfo, tab) => {
      if (updatedTabId !== tabId) return;

      const currentUrl = (tab && tab.url) || (changeInfo && changeInfo.url) || '';
      const urlMatches = expectedSubstring ? currentUrl.includes(expectedSubstring) : true;

      if (changeInfo.status === 'complete' && urlMatches) {
        cleanup();
      }
    };

    chrome.tabs.onUpdated.addListener(listener);

    chrome.tabs.get(tabId, (tab) => {
      if (chrome.runtime.lastError || !tab) return;
      if (tab.status === 'complete' && (!expectedSubstring || (tab.url && tab.url.includes(expectedSubstring)))) {
        cleanup();
      }
    });
  });
}

function wait(ms) {
  return new Promise((r) => setTimeout(r, ms));
}
