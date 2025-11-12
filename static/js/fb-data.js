(function () {
  // 🔹 Helpers
  function parsePrice(v) {
    const n = parseFloat(v);
    return isFinite(n) ? n : 0;
  }

  function parseIntSafe(v) {
    const n = parseInt(v);
    return isFinite(n) ? n : 0;
  }

  function getCookie(name) {
    const m = document.cookie.match(new RegExp("(^| )" + name + "=([^;]+)"));
    return m ? decodeURIComponent(m[2]) : null;
  }

  function setCookie(name, value) {
    document.cookie = `${name}=${value}; path=/; SameSite=Lax`;
  }

  function createEventId(prefix) {
    return `${prefix}_${Date.now()}_${Math.floor(Math.random() * 1e6)}`;
  }

  // 🔹 Track all fired events to prevent duplicates
  const firedEvents = new Set();

  function getDedupKey(eventName, payload, eventID) {
    // Use eventID if present, else eventName + content_ids
    return eventID || eventName + ":" + (payload.content_ids || []).join(",");
  }

  function fireBrowserEvent(eventName, payload, eventID) {
    const dedupKey = getDedupKey(eventName, payload, eventID);
    if (firedEvents.has(dedupKey)) return; // skip duplicates
    firedEvents.add(dedupKey);

    if (!fbq) {
      console.warn("⚠️ FBX: fbq not loaded for", eventName);
      return;
    }
    try {
      fbq("track", eventName, payload, eventID ? { eventID } : undefined);
      console.log(`✅ FBX fired: ${eventName}`, payload, eventID ? `EventID: ${eventID}` : "");
    } catch (err) {
      console.error("❌ FBX fire error:", err);
    }
  }

  // 🔹 Ensure FB cookies exist
  (function ensureFbCookies() {
    const fbclid = new URLSearchParams(location.search).get("fbclid");
    if (!getCookie("_fbp")) setCookie("_fbp", `fb.1.${Date.now()}.${Math.floor(Math.random() * 1e6)}`);
    if (!getCookie("_fbc") && fbclid) setCookie("_fbc", `fb.1.${Date.now()}.${fbclid}`);
    console.log("FB Cookies:", "_fbp=", getCookie("_fbp"), "_fbc=", getCookie("_fbc"));
  })();

  // 🔹 Fire PageView once per page
  (function firePageView() {
    const payload = {
      page_path: window.location.pathname,
      page_title: document.title,
      value: 1.0,
      currency: "BDT",
      content_ids: [window.location.pathname],
      content_type: "page",
      content_category: "PageView",
      event_source_url: window.location.href,
      user_role: window.CURRENT_USER_ROLE || "guest",
    };
    fireBrowserEvent("PageView", payload, "pageview_" + window.location.pathname);
  })();

  // 🔹 Scan .fb-data elements on DOMContentLoaded
  document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll(".fb-data").forEach(function (fbData) {
      if (fbData.dataset.skip === "true") return; // skip manually fired events

      const type = fbData.dataset.type;
      const eventId = fbData.dataset.eventId || createEventId("evt");
      const userRole = fbData.dataset.userRole || window.CURRENT_USER_ROLE || "guest";

      if (type === "product") {
        const payload = {
          content_ids: [fbData.dataset.id],
          content_name: fbData.dataset.name || "",
          content_type: "product",
          content_category: fbData.dataset.category || "Products",
          currency: "BDT",
          value: parsePrice(fbData.dataset.price || 0),
          event_source_url: window.location.href,
          page_title: document.title,
          user_role: userRole,
        };
        fireBrowserEvent("ViewContent", payload, eventId);
      }

      if (type === "cart") {
        let contentIds = [];
        try { contentIds = JSON.parse(fbData.dataset.contentIds || "[]"); } catch (e) {}
        const payload = {
          content_ids: contentIds,
          content_name: fbData.dataset.name || "Cart",
          content_type: "product",
          content_category: "Products",
          currency: "BDT",
          value: parsePrice(fbData.dataset.value || 0),
          quantity: parseIntSafe(fbData.dataset.quantity || 0),
          event_source_url: window.location.href,
          page_title: document.title,
          user_role: userRole,
        };
        fireBrowserEvent("InitiateCheckout", payload, eventId);
      }
    });
  });

  // 🔹 Custom events (AddToCart, Purchase, PollVote)
  function handleCustomEvent(eventName, detail, prefix) {
    const d = detail || {};
    const eventId = d.event_id || createEventId(prefix || "custom");

    // Build payload
    const payload = {
      content_ids: d.ids || (d.id ? [d.id] : []),
      content_name: d.name || "Unknown",
      content_type: d.content_type || "product",
      content_category: d.category || "Products",
      currency: "BDT",
      value: parsePrice(d.value || (d.price || 0) * (d.quantity || 1) || 0),
      quantity: parseIntSafe(d.quantity || d.num_items || 1),
      event_source_url: window.location.href,
      page_title: document.title,
      user_role: d.user_role || window.CURRENT_USER_ROLE || "guest",
      poll_id: d.poll_id || undefined,
      option_ids: d.option_ids || undefined,
      option_texts: d.option_texts || undefined,
      total_votes: d.total_votes || undefined
    };

    fireBrowserEvent(eventName, payload, eventId);
  }

  // 🔹 Event listeners for manual triggers
  document.addEventListener("pixel:add_to_cart", (e) => handleCustomEvent("AddToCart", e.detail, "addtocart"));
  document.addEventListener("pixel:initiate_checkout", (e) => handleCustomEvent("InitiateCheckout", e.detail, "init_checkout"));
  document.addEventListener("pixel:purchase", (e) => handleCustomEvent("Purchase", e.detail, "purchase"));
  document.addEventListener("pixel:poll_vote", (e) => handleCustomEvent("PollVote", e.detail, "pollvote"));
})();
