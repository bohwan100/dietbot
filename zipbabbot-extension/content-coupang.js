// ZipbabBot Chrome Extension - Coupang Automation Content Script
(function() {
  chrome.runtime.onMessage.addListener(function(request, sender, sendResponse) {
    if (request.action === 'FIND_BEST_PRODUCT') {
      try {
        const targetQty = request.targetQty || 1;
        const rawLinks = Array.from(document.querySelectorAll('a[href*="/vp/products/"]'));
        const links = rawLinks.filter(a => !a.href.includes('view_together') 
                    && !a.closest('.recently-viewed-item') 
                    && !a.closest('#recent-view') 
                    && (a.innerText || '').trim().length > 3);

        if (!links.length) {
          sendResponse({ success: false, error: 'NO_LINKS', rawCount: rawLinks.length });
          return true;
        }

        function scoreProduct(a) {
          const text = a.innerText;
          let score = 0;
          if (text.includes('박스') || text.includes('대용량') || text.includes('벌크') || text.includes('업소용') || text.includes('식자재')) score -= 1000;
          if (text.match(/([2-9]|[0-9]{2,}) *kg/) && !text.includes('쌀') && !text.includes('김치') && !text.includes('양파')) score -= 1200;
          const bulkMatch = text.match(/([4-9]|[0-9]{2,}) *(개|모|팩|봉|입|캔)/);
          if (bulkMatch && targetQty < 4) score -= 1000;

          if (targetQty === 1) {
            if (text.match(/1 *(개|모|단|봉|팩|통|병|입|캔)/)) score += 500;
            else if (text.match(/[23] *(개|모|단|봉|팩|구|입|캔)/)) score += 100;
          } else if (targetQty === 2) {
            if (text.match(/2 *(개|모|단|봉|팩|통|병|입|캔)/)) score += 600;
            else if (text.match(/1 *(개|모|단|봉|팩|통|병|입|캔)/)) score += 500;
          }

          if (text.includes('로켓프레시') || text.includes('새벽 도착') || text.includes('새벽도착')) score += 350;
          else if (text.includes('로켓배송') || text.includes('쿠팡추천')) score += 200;

          if (text.includes('광고')) score -= 200;
          return score;
        }

        const scored = links.map(a => ({ a: a, score: scoreProduct(a) }));
        scored.sort((x, y) => y.score - x.score);
        const best = scored[0].a;

        sendResponse({
          success: true,
          url: best.href,
          title: best.innerText.slice(0, 60)
        });
      } catch (e) {
        sendResponse({ success: false, error: e.message });
      }
      return true;
    }

    if (request.action === 'CLICK_ADD_TO_CART') {
      try {
        if (!window.location.href.includes('/vp/products/')) {
          sendResponse({ success: false, error: 'NOT_PRODUCT_PAGE', url: window.location.href });
          return true;
        }

        const targetQty = request.targetQty || 1;
        const titleEl = document.querySelector('h1.prod-buy-header__title, .prod-title, .title');
        const titleText = titleEl ? titleEl.innerText : '';
        let bundleSize = 1;
        const bundleMatch = titleText.match(/([2-9])\s*(개|모|팩|봉|입|캔|병|구)/);
        if (bundleMatch) {
          bundleSize = parseInt(bundleMatch[1], 10);
        }

        let finalQty = targetQty;
        if (bundleSize >= targetQty) finalQty = 1;
        else if (bundleSize > 1) finalQty = Math.max(1, Math.ceil(targetQty / bundleSize));

        // Adjust quantity input if needed
        const qtyInput = document.querySelector("input.prod-quantity__input, input.prod-buy-quantity");
        if (qtyInput && parseInt(qtyInput.value, 10) !== finalQty) {
          qtyInput.value = String(finalQty);
          qtyInput.dispatchEvent(new Event("input", { bubbles: true }));
          qtyInput.dispatchEvent(new Event("change", { bubbles: true }));
        }

        // Find cart button with various selectors
        const btn = document.querySelector(".prod-cart-btn") || 
                    Array.from(document.querySelectorAll("button")).find(b => {
                      const t = (b.innerText || '').trim();
                      return t.includes("장바구니 담기") || t === "장바구니" || b.classList.contains("prod-cart-btn");
                    });

        if (btn) {
          btn.click();
          sendResponse({ success: true, finalQty: finalQty });
        } else {
          sendResponse({ success: false, error: 'BUTTON_NOT_FOUND' });
        }
      } catch (e) {
        sendResponse({ success: false, error: e.message });
      }
      return true;
    }
  });
})();
