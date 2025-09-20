(function(){
  // Helper to safely parse dataset numbers
  function parsePrice(v){ var n = parseFloat(v); return isFinite(n) ? n : 0; }
  function parseIntSafe(v){ var n = parseInt(v); return isFinite(n) ? n : 0; }

document.addEventListener("DOMContentLoaded", function() {
    var fbElements = document.querySelectorAll('.fb-data');
    fbElements.forEach(function(fbData) {
        var t = fbData.dataset.type;
        console.log("data-type:", t);

        if (t === 'product') {
            fbq('track', 'ViewContent', {
                content_ids: [fbData.dataset.id],
                content_name: fbData.dataset.name || '',
                currency: 'BDT',
                value: parseFloat(fbData.dataset.price || 0)
            });
        }

        if (t === 'cart') {
            fbq('track', 'InitiateCheckout', {
                content_name: fbData.dataset.name || 'Cart',
                currency: 'BDT',
                value: parseFloat(fbData.dataset.value || 0),
                content_ids: JSON.parse(fbData.dataset.contentIds || "[]")
            });
        }

        if (t === 'order') {
            fbq('track', 'Purchase', {
                order_id: fbData.dataset.orderId,
                value: parseFloat(fbData.dataset.value || 0),
                currency: 'BDT',
                contents: JSON.parse(fbData.dataset.contents || "[]"),
                num_items: parseInt(fbData.dataset.numItems || 0)
            });
        }
    });
});


  // FUNCTION that fires a browser fbq event from a supplied payload
  function fireBrowserEvent(eventName, payload) {
      if (typeof fbq === 'undefined') return;
      try {
          fbq('track', eventName, payload);
          console.log('FBX fired:', eventName, payload);
      } catch (e) {
          console.error('fbq error', e);
      }
  }

  // LISTEN for application-level custom events dispatched by main.js
  // The main.js SHOULD dispatch events (see below) after successful actions:
  //  document.dispatchEvent(new CustomEvent('pixel:add_to_cart', { detail: {...} }));
  //  document.dispatchEvent(new CustomEvent('pixel:initiate_checkout', { detail: {...} }));
  //  document.dispatchEvent(new CustomEvent('pixel:purchase', { detail: {...} }));

  document.addEventListener('pixel:add_to_cart', function(e){
      var d = e.detail || {};
      fireBrowserEvent('AddToCart', {
          content_ids: [d.id],
          content_name: d.name || '',
          currency: d.currency || 'BDT',
          value: (parsePrice(d.price) * parseIntSafe(d.quantity)),
          quantity: parseIntSafe(d.quantity)
      });
  });

  document.addEventListener('pixel:initiate_checkout', function(e){
      var d = e.detail || {};
      fireBrowserEvent('InitiateCheckout', {
          content_ids: d.ids || (d.id ? [d.id] : []),
          content_name: d.name || 'Cart Checkout',
          content_type: 'product',
          currency: d.currency || 'BDT',
          value: parsePrice(d.value || (d.price * (d.quantity || 1))),
          quantity: parseIntSafe(d.quantity) || undefined
      });
  });

  document.addEventListener('pixel:purchase', function(e){
      var d = e.detail || {};
      // d.contents expected as [{id:, quantity:, item_price:}, ...]
      var ids = (d.contents || []).map(function(it){ return it.id; });
      fireBrowserEvent('Purchase', {
          content_ids: ids,
          content_name: d.order_name || 'Order',
          content_type: 'product',
          currency: d.currency || 'BDT',
          value: parsePrice(d.value),
          num_items: parseIntSafe(d.num_items) || undefined
      });
  });

})();
