(function () {
  // 🔹 Utility helpers
  function parsePrice(v) {
    var n = parseFloat(v);
    return isFinite(n) ? n : 0;
  }
  function parseIntSafe(v) {
    var n = parseInt(v);
    return isFinite(n) ? n : 0;
  }
  function getCookie(name) {
    var m = document.cookie.match(new RegExp('(^| )' + name + '=([^;]+)'));
    return m ? m[2] : null;
  }
  function setEventIdCookie(eventId) {
    document.cookie = `fb_event_id=${eventId}; path=/; SameSite=Lax`;
  }

  // 🔹 Fire Facebook Pixel Event safely
  function fireBrowserEvent(eventName, payload, eventID) {
    if (typeof fbq === "undefined") {
      console.warn("⚠️ FBX: fbq not loaded for", eventName);
      return;
    }
    try {
      if (eventID) fbq("track", eventName, payload, { eventID: eventID });
      else fbq("track", eventName, payload);
      console.log(`✅ FBX fired: ${eventName}`, payload, eventID ? `EventID: ${eventID}` : "");
    } catch (err) {
      console.error("❌ FBX fire error:", err);
    }
  }

  // 🔹 Generate unique event IDs
  function createEventId(prefix) {
    return `${prefix}_${Date.now()}_${Math.floor(Math.random() * 1e6)}`;
  }

  // 🔹 Always fire a PageView event
  (function firePageView() {
    const pageEventId = createEventId("pageview");
    setEventIdCookie(pageEventId);
    fireBrowserEvent(
      "PageView",
      {
        page_path: window.location.pathname,
        page_title: document.title,
        value: 1.0,
        currency: "BDT",
        content_ids: [window.location.pathname],
        content_category: "PageView",
        event_source_url: window.location.href,
      },
      pageEventId
    );
  })();

  // 🔹 When DOM ready, scan all .fb-data elements
  document.addEventListener("DOMContentLoaded", function () {
    console.log("🔍 FBX: DOM Loaded - scanning .fb-data elements");

    document.querySelectorAll(".fb-data").forEach(function (fbData) {
      const type = fbData.dataset.type;
      const eventId =
        fbData.dataset.eventId ||
        getCookie("fb_event_id") ||
        createEventId("evt");
      const userRole =
        fbData.dataset.userRole || window.CURRENT_USER_ROLE || "guest";

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
        let contentCategories = [];
        try {
          contentIds = JSON.parse(fbData.dataset.contentIds || "[]");
        } catch (e) {}
        try {
          contentCategories = JSON.parse(fbData.dataset.contentCategories || "[]");
        } catch (e) {}

        const payload = {
          content_ids: contentIds,
          content_name: fbData.dataset.name || "Cart",
          content_type: "product",
          content_category:"Products",
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

  // 🔹 Listen for custom pixel events
  function handleCustomEvent(eventName, detail, prefix) {
    const d = detail || {};
    const eventId =
      d.event_id ||
      getCookie("fb_event_id") ||
      createEventId(prefix || "custom");

    const payload = {
      content_ids: d.ids || (d.id ? [d.id] : []),
      content_name: d.name || "Unknown",
      content_type: "product",
      content_category: d.category || "Products",
      currency: d.currency || "BDT",
      value: parsePrice(
        d.value || (d.price || 0) * (d.quantity || 1) || 0
      ),
      quantity: parseIntSafe(d.quantity || d.num_items || 1),
      event_source_url: window.location.href,
      page_title: document.title,
      user_role: d.user_role || window.CURRENT_USER_ROLE || "guest",
    };

    fireBrowserEvent(eventName, payload, eventId);
  }

  // 🔹 Custom event listeners
  document.addEventListener("pixel:add_to_cart", (e) =>
    handleCustomEvent("AddToCart", e.detail, "addtocart")
  );
  document.addEventListener("pixel:initiate_checkout", (e) =>
    handleCustomEvent("InitiateCheckout", e.detail, "init_checkout")
  );
  document.addEventListener("pixel:purchase", (e) =>
    handleCustomEvent("Purchase", e.detail, "purchase")
  );
})();
