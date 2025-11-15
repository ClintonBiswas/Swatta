(function () {
  function parsePrice(v){const n=parseFloat(v);return isFinite(n)?n:0;}
  function parseIntSafe(v){const n=parseInt(v);return isFinite(n)?n:0;}
  function getCookie(name){const m=document.cookie.match(new RegExp("(^| )"+name+"=([^;]+)"));return m?decodeURIComponent(m[2]):null;}
  function setCookie(name,value,maxAge=60*30){document.cookie=`${name}=${value}; path=/; SameSite=Lax; max-age=${maxAge}`;}

  function createEventId(prefix){return `${prefix}_${Date.now()}_${Math.floor(Math.random()*1e6)}`;}

  const fired = new Set();
  function dedupKey(eventName,payload,eventId){ return eventId || eventName + ":" + (payload.content_ids||[]).join(","); }

  function fireBrowserEvent(eventName,payload,eventId) {
    const key = dedupKey(eventName,payload,eventId);
    if(fired.has(key)) return;
    fired.add(key);

    // ensure cookies exist for matching
    try {
      const fbclid = new URLSearchParams(location.search).get("fbclid");
      if (!getCookie("_fbp")) setCookie("_fbp", `fb.1.${Date.now()}.${Math.floor(Math.random()*1e6)}`);
      if (fbclid && !getCookie("_fbc")) setCookie("_fbc", `fb.1.${Date.now()}.${fbclid}`);
    } catch(_) {}

    if(!window.fbq){ console.warn("⚠️ FBX: fbq not available for", eventName); return; }
    try{
      fbq('track', eventName, payload, eventId ? { eventID: eventId } : undefined);
      console.log("✅ FBX fired:", eventName, payload, eventId ? "EventID: " + eventId : "");
    }catch(e){
      console.error("❌ FBX fire error:", e);
    }
  }

 // custom event handler - used by site JS
function handleCustomEvent(eventName, detail, prefix){
  const d = detail || {};
  const eventId = d.event_id || createEventId(prefix || "ev");
  const payload = {
    content_ids: d.ids || (d.id ? [d.id] : []),
    content_name: d.name || "Unknown",
    content_type: d.content_type || "product",
    content_category: d.category || "Products",
    currency: d.currency || "BDT",
    value: parseFloat(parsePrice(d.value || d.price || 0) * (d.quantity || 1)).toFixed(2),
    quantity: parseIntSafe(d.quantity || 1),
    // ensure contents always exists
    contents: d.contents || (d.id ? [{id: d.id, quantity: d.quantity || 1, item_price: parseFloat(d.price || 0).toFixed(2)}] : []),
    event_source_url: d.event_source_url || window.location.href,
    page_title: document.title,
    user_role: d.user_role || window.CURRENT_USER_ROLE || "guest",
    fbc: getCookie("_fbc"),
    fbp: getCookie("_fbp"),
    client_user_agent: navigator.userAgent,
    action_source: "website"  // ✅ add this for Meta consistency
  };
  
  if(d.event_id) console.log("%c[Pixel Debug] Using backend event_id: " + d.event_id, "color:green");
  else console.log("%c[Pixel Debug] Generated event_id: " + eventId, "color:orange");

  fireBrowserEvent(eventName, payload, eventId);
}


  document.addEventListener("pixel:add_to_cart", (e) => handleCustomEvent("AddToCart", e.detail, "addtocart"));
  document.addEventListener("pixel:initiate_checkout", (e) => handleCustomEvent("InitiateCheckout", e.detail, "init_checkout"));
  document.addEventListener("pixel:purchase", (e) => handleCustomEvent("Purchase", e.detail, "purchase"));
})();
