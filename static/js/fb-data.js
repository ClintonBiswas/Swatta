(function () {
  // -----------------------------
  // ✅ Helper Functions
  // -----------------------------
  function parsePrice(v) {
    var n = parseFloat(v);
    return isFinite(n) ? n : 0;
  }

  function parseIntSafe(v) {
    var n = parseInt(v);
    return isFinite(n) ? n : 0;
  }

  function getCookie(name) {
    const match = document.cookie.match(new RegExp("(^| )" + name + "=([^;]+)"));
    return match ? match[2] : null;
  }

  function setCookie(name, value, days = 7) {
    const expires = new Date(Date.now() + days * 864e5).toUTCString();
    document.cookie = `${name}=${value}; expires=${expires}; path=/; SameSite=Lax`;
  }

  function setEventIdCookie(eventId) {
    setCookie("_event_id", eventId);
  }

  // -----------------------------
  // ✅ Handle fbc (Click ID) cookie for deduplication
  // -----------------------------
  if (!getCookie("_fbc") && window.location.search.includes("fbclid=")) {
    const fbclid = new URLSearchParams(location.search).get("fbclid");
    setCookie("_fbc", `fb.1.${Date.now()}.${fbclid}`);
  }

  // -----------------------------
  // ✅ Fire fbq event (with optional deduplication ID)
  // -----------------------------
  function fireBrowserEvent(eventName, payload, eventID) {
    if (typeof fbq === "undefined") {
      console.warn("FBX Warning: fbq not loaded yet", eventName, payload);
      return;
    }
    try {
      if (eventID) {
        fbq("track", eventName, payload, { eventID: eventID });
      } else {
        fbq("track", eventName, payload);
      }
      console.log(
        "%cFBX fired:",
        "color:green;font-weight:bold",
        eventName,
        payload,
        eventID ? "EventID: " + eventID : ""
      );
    } catch (e) {
      console.error("FBX error:", e);
    }
  }

  // -----------------------------
  // ✅ DOM Ready: Fire Events
  // -----------------------------
  document.addEventListener("DOMContentLoaded", function () {
    console.log("%cFBX: DOM Loaded - scanning .fb-data elements", "color:blue;font-weight:bold");

    // 🔹 Fire PageView (always)
    const pageEventId = "pageview_" + Date.now() + "_" + Math.floor(Math.random() * 1000000);
    setEventIdCookie(pageEventId);
    fireBrowserEvent(
      "PageView",
      {
        page_path: window.location.pathname,
        page_title: document.title,
      },
      pageEventId
    );

    // 🔹 Scan for .fb-data elements
    var fbElements = document.querySelectorAll(".fb-data");
    fbElements.forEach(function (fbData) {
      var t = fbData.dataset.type;
      var eventId =
        fbData.dataset.eventId ||
        t + "_" + Date.now() + "_" + Math.floor(Math.random() * 1000000);
      setEventIdCookie(eventId);

      console.log("%cFBX found .fb-data element:", "color:purple", t, fbData.dataset);

      if (t === "product") {
        // ViewContent Event
        fireBrowserEvent(
          "ViewContent",
          {
            content_ids: [fbData.dataset.id],
            content_name: fbData.dataset.name || "",
            content_type: "product",
            currency: "BDT",
            value: parsePrice(fbData.dataset.price || 0),
          },
          eventId
        );
      }

      if (t === "cart") {
        // InitiateCheckout Event
        fireBrowserEvent(
          "InitiateCheckout",
          {
            content_ids: JSON.parse(fbData.dataset.contentIds || "[]"),
            content_name: fbData.dataset.name || "Cart",
            content_type: "product",
            currency: "BDT",
            value: parsePrice(fbData.dataset.value || 0),
          },
          eventId
        );
      }
    });
  });

  // -----------------------------
  // ✅ Listen for custom JS events (AddToCart, Checkout, Purchase)
  // -----------------------------
  document.addEventListener("pixel:add_to_cart", function (e) {
    var d = e.detail || {};
    fireBrowserEvent(
      "AddToCart",
      {
        content_ids: [d.id],
        content_name: d.name || "",
        content_type: "product",
        currency: "BDT",
        value: parsePrice(d.price) * parseIntSafe(d.quantity),
        quantity: parseIntSafe(d.quantity),
      },
      d.event_id
    );
  });

  document.addEventListener("pixel:initiate_checkout", function (e) {
    var d = e.detail || {};
    fireBrowserEvent(
      "InitiateCheckout",
      {
        content_ids: d.ids || (d.id ? [d.id] : []),
        content_name: d.name || "Cart Checkout",
        content_type: "product",
        currency: "BDT",
        value: parsePrice(d.value || (d.price * (d.quantity || 1))),
        quantity: parseIntSafe(d.quantity) || undefined,
      },
      d.event_id
    );
  });

  document.addEventListener("pixel:purchase", function (e) {
    var d = e.detail || {};
    var ids = (d.contents || []).map(function (it) {
      return it.id;
    });
    var purchasePayload = {
      content_ids: ids,
      content_name: d.order_name || "Order",
      content_type: "product",
      value: parsePrice(d.value),
      currency: "BDT",
    };
    var numItems = parseIntSafe(d.num_items || 0);
    if (numItems > 0) purchasePayload.num_items = numItems;
    fireBrowserEvent("Purchase", purchasePayload, d.event_id);
  });
})();
