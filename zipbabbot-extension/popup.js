document.getElementById('btn-open-dashboard').addEventListener('click', () => {
  chrome.tabs.create({ url: 'https://bohwan100.github.io/zipbab/cart_dashboard.html' });
});

document.getElementById('btn-open-cart').addEventListener('click', () => {
  chrome.tabs.create({ url: 'https://cart.coupang.com/cartView.pang' });
});
