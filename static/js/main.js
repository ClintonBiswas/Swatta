
// Typed js on placeholder

document.addEventListener('DOMContentLoaded', () => {
    const typed = new Typed('#desktop-search-input', {
        strings: ['Search product name', 'Search product category', 'Search product subcategory', 'Shop now!'], 
        typeSpeed: 50, 
        backSpeed: 30,  
        backDelay: 1000, 
        loop: true, 
        attr: 'placeholder', 
        bindInputFocusEvents: true, 
    });
});
//navbar animation
document.addEventListener("DOMContentLoaded", () => {
    const navHeader = document.querySelector(".nav-header");

    window.addEventListener("scroll", () => {
        if (window.scrollY > 100) {
            navHeader.classList.add("scroll-active");
        } else {
            navHeader.classList.remove("scroll-active");
        }
    });
});


//product global swiper



// nav menu side bar
document.addEventListener("DOMContentLoaded", function () {
    const menuCategory = document.getElementById("menu-category");
    const sidebarMenu = document.getElementById("sidebar-menu");
    const closeSidebar = document.getElementById("close-sidebar");

    // Show sidebar on menu category click
    menuCategory.addEventListener("click", function () {
        sidebarMenu.classList.add("active");
    });

    // Hide sidebar on close button click
    closeSidebar.addEventListener("click", function () {
        sidebarMenu.classList.remove("active");
    });

    // Optional: Close sidebar if user clicks outside of it
    window.addEventListener("click", function (e) {
        if (!sidebarMenu.contains(e.target) && e.target !== menuCategory) {
            sidebarMenu.classList.remove("active");
        }
    });
});

//nav menu sidebar dropdown

document.addEventListener("DOMContentLoaded", () => {
    const toggles = document.querySelectorAll(".sidebar-dropdown-toggle");
  
    toggles.forEach((toggle) => {
        toggle.addEventListener("click", (e) => {
            const dropdownMenu = toggle.closest(".list-group-item").querySelector(".sidebar-dropdown-menu");
            const icon = toggle.querySelector("i"); // Select the <i> element directly
  
            // Close other dropdowns
            document.querySelectorAll(".sidebar-dropdown-menu").forEach((menu) => {
                if (menu !== dropdownMenu) {
                    menu.style.display = "none";
                    const otherIcon = menu.previousElementSibling.querySelector("i");
                    if (otherIcon) {
                        otherIcon.classList.remove("active");
                    }
                }
            });
  
            // Toggle current dropdown
            if (dropdownMenu) {
                dropdownMenu.style.display = dropdownMenu.style.display === "block" ? "none" : "block";
                icon.classList.toggle("active"); // Toggle the active class
            }
        });
    });
  });

  // cart buy now update cart js

  document.addEventListener("DOMContentLoaded", function () {
    // Fetch Cart Count on Page Load
    fetch("/get-cart-count/")
        .then(response => response.json())
        .then(data => {
            let cartCountElements = document.querySelectorAll(".cart-count");
            cartCountElements.forEach(function (element) {  // Corrected loop
                element.textContent = data.cart_count;  // Update all cart count elements
            });
        })
        .catch(error => console.error("Error fetching cart count:", error));

// Helper: extract product info safely start pixel
function getProductData(btn) {
    let productId = btn.dataset.product;
    let productName = btn.dataset.productName || productId;
    let productPrice = parseFloat(btn.dataset.productPrice || 0);
    let productCategory = btn.dataset.category || "Products";

    let quantity = 1;
    const qtyInput = document.querySelector("#cart-quantity");
    if (qtyInput) {
        let q = parseInt(qtyInput.value);
        if (!isNaN(q) && q > 0) quantity = q;
    }

    // Safe size/color
    let size = null, color = null;
    const sizeInput = document.querySelector('input[name="size"]:checked');
    const colorInput = document.querySelector('input[name="color"]:checked');
    if (sizeInput) size = sizeInput.value;
    if (colorInput) color = colorInput.value;

    return { productId, productName, productPrice, quantity, size, color, productCategory };
}

// Add to Cart
document.addEventListener("click", function(event) {
    const btn = event.target.closest(".add-to-cart-btn, .add-to-cartt");
    if (!btn) return;
    event.preventDefault();

    const { productId, productName, productPrice, quantity, size, color, productCategory } = getProductData(btn);
    const eventId = "evt_" + Date.now() + "_" + Math.random().toString(36).substr(2, 9);

    console.log("🔥 AddToCart frontend event_id:", eventId);

    document.dispatchEvent(new CustomEvent("pixel:add_to_cart", {
        detail: { id: productId, name: productName, price: productPrice, quantity, currency:"BDT", event_id: eventId, category: productCategory }
    }));

    fetch("/add-to-cart/", {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-CSRFToken": getCSRFToken() },
        body: JSON.stringify({ product_id: productId, quantity, size, color, event_id: eventId }),
    })
    .then(res => res.json())
    .then(data => {
        if(data.status === "success") {
            updateCartUI(data);
            showToast(data.message);
        } else {
            alert("Error: " + data.message);
        }
    });
});


// Buy Now
document.addEventListener("click", function(event) {
  const btn = event.target.closest(".buy-now-btn, .buy-now-mobile, .buy-noww");
  if (!btn) return;
  event.preventDefault();

  const { productId, productName, productPrice, quantity, size, color, productCategory } = getProductData(btn);

  const ts = Date.now();
  const rand = Math.random().toString(36).substr(2,9);
  const addToCartEventId = `evt_${ts}_add_${rand}`;
  const checkoutEventId   = `evt_${ts}_checkout_${rand}`;

  document.dispatchEvent(new CustomEvent("pixel:add_to_cart", {
    detail: { id: productId, name: productName, price: productPrice, quantity, currency:"BDT", event_id: addToCartEventId, category: productCategory }
  }));

  document.dispatchEvent(new CustomEvent("pixel:initiate_checkout", {
    detail: { id: productId, name: productName, price: productPrice, quantity, currency:"BDT", event_id: checkoutEventId, category: productCategory }
  }));

  setCookie("fb_event_id", checkoutEventId, 300);

  fetch("/buy-now/", {
    method: "POST",
    headers: { "Content-Type": "application/json", "X-CSRFToken": getCSRFToken() },
    body: JSON.stringify({
      product_id: productId,
      quantity,
      size,
      color,
      add_to_cart_event_id: addToCartEventId,
      checkout_event_id: checkoutEventId
    }),
  })
  .then(res => res.json())
  .then(data => {
    if (data.status === "success") {
      window.location.href = data.redirect_url || "/checkout/";
    } else {
      deleteCookie("fb_event_id");
      alert("Error: " + data.message);
    }
  });
});


//end pixel

//set cookie globally
function setCookie(name, value, maxAgeSeconds) {
  let cookie = encodeURIComponent(name) + "=" + encodeURIComponent(value) + "; path=/; SameSite=Lax";
  if (typeof maxAgeSeconds === "number") {
    cookie += "; max-age=" + parseInt(maxAgeSeconds, 10);
  }
  document.cookie = cookie;
}

function getCookie(name) {
  const m = document.cookie.match(new RegExp("(^| )" + name + "=([^;]+)"));
  return m ? decodeURIComponent(m[2]) : null;
}

function deleteCookie(name) {
  document.cookie = encodeURIComponent(name) + "=; path=/; max-age=0; SameSite=Lax";
}



    // Quantity Buttons
    document.querySelectorAll(".quantity-product-button").forEach((button) => {
        button.addEventListener("click", function () {
            const quantityInput = document.querySelector("#cart-quantity");
            let quantity = parseInt(quantityInput.value);

            if (this.classList.contains("increment-button")) {
                quantity += 1; // Increase quantity
                
            } else if (this.classList.contains("decrement-button")) {
                quantity = Math.max(1, quantity - 1); // Decrease quantity (minimum 1)
                
            }

            quantityInput.value = quantity; // Update the input field
        });
    });


    // Function to update cart UI
    function updateCartUI(data) {
        let cartCountElements = document.querySelectorAll(".cart-count");
    cartCountElements.forEach(function (element) {  // Corrected loop
        element.textContent = data.cart_count;  // Update all instances of cart count
    });
    }

    // Function to get CSRF token
    function getCSRFToken() {
        let tokenElement = document.querySelector("[name=csrfmiddlewaretoken]");
        return tokenElement ? tokenElement.value : "";
    }
});


    // cart sidebar logic
    document.addEventListener("DOMContentLoaded", function () {
        const cartIconButton = document.querySelectorAll(".cart-side-menu");
        const cartSidebarMenu = document.getElementById("cart-sidebar-menu");
        const cartCloseBtn = document.getElementById("cart-close-sidebar");
        const cartItemList = document.querySelector(".cart-item-list");
        const overlay = document.getElementById("overlay");
    
        // Function to update cart item quantity on server
        // Function to update cart item quantity on server
        async function updateCartItemQuantity(itemId, quantity) {
            if (!itemId || itemId === "undefined") {
                console.error("Invalid item ID received:", itemId);
                return { status: "error", message: "Invalid cart item" };
            }
        
            try {
                const response = await fetch("/update-cart/", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        "X-CSRFToken": getCSRFToken(),
                    },
                    body: JSON.stringify({
                        item_id: itemId,
                        quantity: quantity
                    }),
                });
                
                if (!response.ok) {
                    const errorData = await response.json();
                    throw new Error(errorData.message || 'Failed to update quantity');
                }
                
                return await response.json();
            } catch (error) {
                console.error("Error updating cart item:", {
                    error: error,
                    itemId: itemId,
                    quantity: quantity
                });
                return { 
                    status: "error", 
                    message: error.message || "Failed to update quantity" 
                };
            }
        }

            // Function to get CSRF token
            function getCSRFToken() {
                const cookieValue = document.cookie
                    .split('; ')
                    .find(row => row.startsWith('csrftoken='))
                    ?.split('=')[1];
                return cookieValue || '';
            }
    
        // Function to update the subtotal
        function updateSubtotal() {
            let subtotal = 0;
            document.querySelectorAll(".cart-item").forEach((item) => {
                const totalPriceElement = item.querySelector(".item-total-price");
                if (totalPriceElement) {
                    subtotal += extractPrice(totalPriceElement.textContent);
                }
            });
            document.querySelector(".cart-subtotal span").textContent = `${subtotal.toFixed(2)} tk`;
        }
    
        // Improved price extraction function
        function extractPrice(text) {
            if (!text) return 0;
            const priceStr = text.toString().replace(/[^\d.]/g, '');
            const price = parseFloat(priceStr);
            return isNaN(price) ? 0 : price;
        }
    
        // Function to attach event listeners
        function attachEventListeners() {
            // Quantity Buttons
document.querySelectorAll(".quantity-product-button").forEach((button) => {
    button.addEventListener("click", async function (event) {
        event.preventDefault();
        
        const card = this.closest(".card");
        const quantityInput = card.querySelector(".cart-quantity");
        const itemId = card.dataset.itemId;
        
        if (!itemId) {
            alert("Error: Item ID is missing from the card element");
            return;
        }
        
        let quantity = parseInt(quantityInput.value) || 1;
        
        if (this.classList.contains("increment-button")) {
            quantity += 1;
        } else if (this.classList.contains("decrement-button")) {
            quantity = Math.max(1, quantity - 1);
        }
        
        quantityInput.value = quantity;
        
        try {
            // Show loading state
            this.disabled = true;
            const originalHTML = this.innerHTML;
            
            // Update server first
            const result = await updateCartItemQuantity(itemId, quantity);
            
            if (result.status === "success") {
                // Then update UI
                const unitPrice = extractPrice(card.querySelector(".unit-price").textContent);
                card.querySelector(".item-total-price").textContent = (unitPrice * quantity).toFixed(2);
                updateSubtotal();
            } else {
                alert(result.message);
                // Revert quantity if update failed
                quantityInput.value = quantity - (this.classList.contains("increment-button") ? 1 : -1);
            }
        } catch (error) {
            console.error("Error:", error);
            alert("Failed to update quantity. Please try again.");
        } finally {
            // Restore button state
            this.disabled = false;
            this.innerHTML = originalHTML;
        }
    });
});

    
document.querySelectorAll(".remove-item-button").forEach((button) => {
    button.addEventListener("click", function (event) {
        event.preventDefault();
        const itemId = this.dataset.itemId;

        if (!itemId) {
            alert("Error: Item ID is missing.");
            return;
        }

        fetch("/remove-from-cart/", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": "{{ csrf_token }}",
            },
            body: JSON.stringify({ item_id: itemId }),
        })
        .then((response) => response.json())
        .then((data) => {
            if (data.status === "success") {
                // Remove the item from the DOM
                this.closest(".card").remove();
                updateSubtotal();
                updateCartCount(data.cart_count); // Add this line
                showToast(data.message);
            } else {
                alert("Error: " + data.message);
            }
        })
        .catch((error) => console.error("Error:", error));
    });
});

// Function to update the cart count
function updateCartCount(newCount) {
    const cartCountElement = document.querySelector(".cart-count");
    if (cartCountElement) {
        cartCountElement.textContent = newCount;
    }
}

    
// Update checkout button to ensure quantities are saved
    document.querySelector(".cart-subtotal-button")?.addEventListener("click", async function(event) {
    event.preventDefault();
    const button = this;
    button.disabled = true;

    try {
        // Only update items inside the sidebar cart list
        const updates = Array.from(cartItemList.querySelectorAll(".card")).map(async (card) => {
            const itemId = card.dataset.itemId;
            const qtyInput = card.querySelector(".cart-quantity");
            const quantity = parseInt(qtyInput?.value) || 1;

            if (itemId) {
                return updateCartItemQuantity(itemId, quantity);
            }
        });

        await Promise.all(updates);
        window.location.href = "/checkout/";
    } catch (error) {
        console.error("Error updating quantities:", error);
        alert("Failed to update quantities. Please try again.");
        button.disabled = false;
        button.innerHTML = '<a href="/checkout/">Go to checkout</a>';
    }
});

        }
    
        // Function to fetch cart data (keep your existing implementation)
        async function fetchCartData() {
            try {
                const response = await fetch("/cart/");
                if (!response.ok) {
                    throw new Error(`HTTP error! Status: ${response.status}`);
                }

                const data = await response.json();
                const cartItems = data.cart_items;
                const cartTotal = data.cart_total;

                // Clear existing items
                cartItemList.innerHTML = "";

                // Render cart items
                cartItems.forEach((item) => {
                    const cartItemElement = document.createElement("div");
                    cartItemElement.classList.add("cart-item");
                    cartItemElement.innerHTML = `
                        <div class="card mb-3" data-product-id="${item.product_id}" data-item-id="${item.id}" style="border: none; border-bottom: 1px solid #f6e7e5;">
                            <div class="row g-0 align-items-center d-flex flex-nowrap">
                                <div class="col-3 d-flex justify-content-center">
                                    <img src="${item.product_image}" class="img-fluid rounded-start" alt="${item.product_name}" style="height: 80px; width: 80px; object-fit: cover;" onerror="this.src='/static/images/default-product-image.png'">
                                </div>
                                <div class="col-9">
                                    <div class="card-body p-2">
                                        <h5 class="custom-card-title" style="font-size: 14px;">${item.product_name}</h5>
                                        <div class="d-flex align-items-center justify-content-between w-100 mb-2">
                                            <!-- Left Side: Quantity Buttons -->
                                            <div class="quantity d-flex align-items-center">
                                                <button class="quantity-product-button decrement-button"><i class="bi bi-dash"></i></button>
                                                <input type="number" class="cart-quantity text-center mx-1" value="${item.quantity}" min="1" style="width: 40px;">
                                                <button class="quantity-product-button increment-button"><i class="bi bi-plus"></i></button>
                                            </div>
                                            
                                            <!-- Right Side: Remove Button -->
                                            <button class="btn btn-danger btn-sm remove-item-button" data-item-id="${item.id}">
                                                <i class="bi bi-trash-fill"></i> Remove
                                            </button>
                                        </div>
                                        
                                        ${(item.product_size || item.product_color) ? `
                                        <div class="d-flex checkout-price" style="gap: 10px;">
                                            ${item.product_size ? `
                                                <p class="card-text mb-1" style="font-size: 12px;">
                                                    Size:<span style="font-weight: 600; color: #700000;">&nbsp;${item.product_size}</span>
                                                </p>` : ''}
                                            ${item.product_color ? `
                                                <p class="card-text mb-1" style="font-size: 12px;">
                                                    Color:<span style="font-weight: 600; color: #700000;">&nbsp;${item.product_color}</span>
                                                </p>` : ''}
                                        </div>` : ''}

                                        
                                        <div class="d-flex checkout-price" style="gap: 10px;">
                                            <p class="card-text">Unit Price: <span class="unit-price">${item.product_price} tk</span></p>
                                            <p class="card-text">Total Price: <span class="item-total-price">${(parseFloat(item.product_price) * item.quantity)} tk</span></p>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    `;
                    cartItemList.appendChild(cartItemElement);
                });

                // Render cart total
                const cartTotalElement = document.createElement("div");
                cartTotalElement.classList.add("cart-total");
                cartTotalElement.innerHTML = `
                    <div class="subtotal mt-5">
                        <div class="cart-subtotal">
                            <p>Subtotal: <span class="subtotal-amount">${cartTotal} tk</span></p>
                            <button class="cart-subtotal-button">
                                <a href="/checkout/">Go to Checkout</a>
                            </button>
                        </div>
                    </div>
                `;
                cartItemList.appendChild(cartTotalElement);

                // Reattach event listeners
                attachEventListeners();

            } catch (error) {
                console.error("Error fetching cart data:", error);
                // Show error to user
                showToast('error', 'Failed to load cart data. Please try again.');
            }
        }
    
        // Open sidebar and fetch cart data
        // Cart Sidebar Toggle
        cartIconButton.forEach(button => {
            button.addEventListener("click", function(e) {
                e.stopPropagation(); // Prevent event bubbling
                cartSidebarMenu.classList.add("active");
                overlay.classList.add("active");
                fetchCartData();
            });
        });

        // Close sidebar when close button is clicked
        cartCloseBtn.addEventListener("click", function(e) {
            e.stopPropagation(); // Prevent event bubbling
            cartSidebarMenu.classList.remove("active");
            overlay.classList.remove("active");
        });

        // Close sidebar when clicking outside (on overlay)
        overlay.addEventListener("click", function(e) {
            e.stopPropagation(); // Prevent event bubbling
            cartSidebarMenu.classList.remove("active");
            overlay.classList.remove("active");
        });

        // Prevent clicks inside cart from closing it
        cartSidebarMenu.addEventListener("click", function(e) {
            e.stopPropagation();
        });

        // Add this to prevent navbar from opening when these elements are clicked
        [cartSidebarMenu, overlay, cartCloseBtn, ...cartIconButton].forEach(el => {
            el.addEventListener("click", function(e) {
                e.stopImmediatePropagation();
            });
        });
    });
//  checkout js start
    document.addEventListener("DOMContentLoaded", function() {
        // Get CSRF token
        const csrfToken = document.querySelector('input[name="csrfmiddlewaretoken"]')?.value || '';
        
        // Price formatting helper
        const getPrice = (text) => {
            const price = parseFloat(text.replace(/[^\d.]/g, ''));
            return isNaN(price) ? 0 : price;
        };
        
        // Helper function for showing messages
        const showMessage = (element, message, color) => {
            if (!element) return;
            element.textContent = message;
            element.style.color = color;
            element.style.display = message ? 'block' : 'none';
        };
    
        // Cart quantity functions
        const updateQuantityOnServer = async (itemId, quantity) => {
            try {
                const response = await fetch("/update-cart/", {
                    method: "POST",
                    headers: { 
                        "Content-Type": "application/json", 
                        "X-CSRFToken": csrfToken 
                    },
                    body: JSON.stringify({ item_id: itemId, quantity }),
                });
                
                if (!response.ok) throw new Error('Network response was not ok');
                
                const data = await response.json();
                return data.status === "success";
            } catch (err) {
                console.error("Update quantity failed:", err);
                return false;
            }
        };
    
        const handleQuantityChange = async (input, increment = 0) => {
            const card = input.closest(".card");
            if (!card) return;
    
            const itemId = card.dataset.itemId;
            const unitPriceElement = card.querySelector(".unit-price");
            
            if (!itemId || !unitPriceElement) return;
    
            const unitPrice = parseFloat(unitPriceElement.dataset.unitPrice || getPrice(unitPriceElement.textContent));
            const totalPriceElement = card.querySelector(".item-total-price");
    
            let quantity = parseInt(input.value) || 1;
            quantity = Math.max(1, quantity + increment);
    
            input.value = quantity;
            if (totalPriceElement) {
                totalPriceElement.textContent = `৳${(unitPrice * quantity).toFixed(2)}`;
            }
    
            const success = await updateQuantityOnServer(itemId, quantity);
            if (!success) {
                quantity = Math.max(1, parseInt(input.dataset.oldValue) || 1);
                input.value = quantity;
                if (totalPriceElement) {
                    totalPriceElement.textContent = `৳${(unitPrice * quantity).toFixed(2)}`;
                }
            }
    
            updateSubtotal();
        };
    
        // Cart total calculations
        const updateSubtotal = () => {
            let subtotal = 0;
            document.querySelectorAll(".item-total-price").forEach(item => {
                subtotal += getPrice(item.textContent);
            });
            
            const subtotalElement = document.getElementById("subtotal");
            if (subtotalElement) {
                subtotalElement.textContent = `৳${subtotal.toFixed(2)}`;
            }
            updateGrandTotal();
        };
    
        const updateGrandTotal = () => {
            const subtotalElement = document.getElementById("subtotal");
            const deliveryCostElement = document.getElementById("delivery-cost");
            const discountInfo = document.getElementById("discount-info");
            const grandTotalElement = document.getElementById("grand-total");
            
            if (!subtotalElement || !deliveryCostElement || !grandTotalElement) return;
    
            const subtotal = getPrice(subtotalElement.textContent);
            const deliveryCost = getPrice(deliveryCostElement.textContent);
            let grandTotal = subtotal + deliveryCost;
    
            if (window.activePromoCode) {
                let discount = 0;
                if (window.activePromoCode.discount_type === 'percentage') {
                    discount = subtotal * (window.activePromoCode.discount_value / 100);
                } else {
                    discount = Math.min(window.activePromoCode.discount_value, subtotal);
                }
                
                grandTotal = Math.max(0, subtotal - discount + deliveryCost);
                
                const discountValueElement = document.getElementById("discount-value");
                if (discountValueElement) {
                    discountValueElement.textContent = `-৳${discount.toFixed(2)}`;
                }
                
                if (discountInfo) {
                    discountInfo.style.display = 'flex';
                }
            } else if (discountInfo) {
                discountInfo.style.display = 'none';
            }
    
            grandTotalElement.textContent = `৳${grandTotal.toFixed(2)}`;
        };
    
        // Promo code functions
        const applyPromoCode = async () => {
            const promoCodeInput = document.getElementById('promo-code-input');
            const applyPromoBtn = document.getElementById('apply-promo-btn');
            const promoMessage = document.getElementById('promo-code-message');
            
            if (!promoCodeInput || !applyPromoBtn || !promoMessage) return;
    
            const code = promoCodeInput.value.trim();
            if (!code) {
                showMessage(promoMessage, 'Please enter a promo code', 'red');
                return;
            }
    
            // Clear previous state
            showMessage(promoMessage, '', '');
            const activePromo = document.getElementById('active-promo');
            if (activePromo) activePromo.remove();
            
            applyPromoBtn.disabled = true;
            applyPromoBtn.innerHTML = `<span class="spinner-border spinner-border-sm"></span> Applying...`;
    
            try {
                const response = await fetch('/apply-promo-code/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/x-www-form-urlencoded',
                        'X-CSRFToken': csrfToken
                    },
                    body: `code=${encodeURIComponent(code)}`
                });
    
                if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
    
                const data = await response.json();
    
                if (data.success) {
                    window.activePromoCode = data.promo_data;
                    
                    // Create success message
                    const promoContainer = document.querySelector('.promocode-container');
                    if (promoContainer) {
                        const successDiv = document.createElement('div');
                        successDiv.className = 'alert alert-success mt-2';
                        successDiv.id = 'active-promo';
                        successDiv.innerHTML = `
                            Promo code <strong>${data.promo_data.code}</strong> applied!
                            <button class="btn btn-sm p-1 btn-link" id="remove-promo-btn">Remove</button>
                        `;
                        promoContainer.appendChild(successDiv);
                        
                        // Add event listener to new button
                        document.getElementById('remove-promo-btn')?.addEventListener('click', removePromoCode);
                    }
                    
                    updateGrandTotal();
                } else {
                    showMessage(promoMessage, data.message || 'Invalid promo code', 'red');
                }
            } catch (error) {
                console.error('Promo code error:', error);
                showMessage(promoMessage, 'Failed to apply promo code. Please try again.', 'red');
            } finally {
                applyPromoBtn.disabled = false;
                applyPromoBtn.textContent = 'Apply';
            }
        };
    
        const removePromoCode = async () => {
            const promoMessage = document.getElementById('promo-code-message');
            
            try {
                const response = await fetch('/remove-promo-code/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/x-www-form-urlencoded',
                        'X-CSRFToken': csrfToken
                    }
                });
    
                if (!response.ok) throw new Error('Network error');
    
                const data = await response.json();
                if (data.success) {
                    window.activePromoCode = null;
                    document.getElementById('active-promo')?.remove();
                    updateGrandTotal();
                } else {
                    showMessage(promoMessage, 'Failed to remove promo code', 'red');
                }
            } catch (error) {
                console.error('Remove promo error:', error);
                showMessage(promoMessage, 'Failed to remove promo code', 'red');
            }
        };
    
        // Cart item removal
        const removeCartItem = (button) => {
            const card = button.closest(".card");
            if (!card) return;
    
            const itemId = button.dataset.itemId;
            if (!itemId) return;
    
            card.style.display = 'none';
    
            fetch("/remove-from-cart/", {
                method: "POST",
                headers: { 
                    "Content-Type": "application/json", 
                    "X-CSRFToken": csrfToken 
                },
                body: JSON.stringify({ item_id: itemId }),
            })
            .then(res => {
                if (!res.ok) throw new Error('Network response was not ok');
                return res.json();
            })
            .then(data => {
                if (data.status === "success") {
                    card.remove();
                    updateSubtotal();
                    updateCartCount(data.cart_count); 
                    showToast(data.message);
                } else {
                    card.style.display = '';
                    alert(data.message || 'Failed to remove item');
                }
            })
            .catch(err => {
                console.error("Remove item failed:", err);
                card.style.display = '';
            });
        };
    
        const updateCartCount = (newCount) => {
            const cartCountElement = document.querySelector(".cart-count");
            if (cartCountElement) {
                cartCountElement.textContent = newCount;
            }
        };
    
        // Initialize all event listeners
        const initializeCart = () => {
            // Quantity controls
            document.querySelectorAll(".cart-quantity").forEach(input => {
                input.dataset.oldValue = input.value;
                input.addEventListener("change", () => handleQuantityChange(input));
            });
    
            document.querySelectorAll(".increment-button").forEach(btn => {
                btn.addEventListener("click", () => {
                    const input = btn.closest(".card")?.querySelector(".cart-quantity");
                    if (input) handleQuantityChange(input, 1);
                });
            });
    
            document.querySelectorAll(".decrement-button").forEach(btn => {
                btn.addEventListener("click", () => {
                    const input = btn.closest(".card")?.querySelector(".cart-quantity");
                    if (input) handleQuantityChange(input, -1);
                });
            });
    
            // Remove item buttons
            document.querySelectorAll(".remove-item-button").forEach(btn => {
                btn.addEventListener("click", (e) => {
                    e.preventDefault();
                    removeCartItem(btn);
                });
            });
    
            // Delivery location change
            document.getElementById("delivery-location")?.addEventListener("change", function() {
                const deliveryCost = this.value === "inside_dhaka" ? 70 : 130;
                const deliveryCostElement = document.getElementById("delivery-cost");
                if (deliveryCostElement) {
                    deliveryCostElement.textContent = `৳${deliveryCost.toFixed(2)}`;
                }
                updateGrandTotal();
            });
    
            // Initialize product cards
            document.querySelectorAll(".card").forEach(card => {
                const unitPriceElement = card.querySelector(".unit-price");
                if (unitPriceElement) {
                    if (!unitPriceElement.dataset.unitPrice) {
                        unitPriceElement.dataset.unitPrice = getPrice(unitPriceElement.textContent);
                    }
                    const quantityInput = card.querySelector(".cart-quantity");
                    const quantity = parseInt(quantityInput?.value) || 1;
                    const totalPriceElement = card.querySelector(".item-total-price");
                    if (totalPriceElement) {
                        totalPriceElement.textContent = `৳${(parseFloat(unitPriceElement.dataset.unitPrice) * quantity).toFixed(2)}`;
                    }
                }
            });
    
            // Promo code initialization
            document.getElementById('apply-promo-btn')?.addEventListener('click', applyPromoCode);
            document.getElementById('promo-code-input')?.addEventListener('keypress', e => {
                if (e.key === 'Enter') applyPromoCode();
            });
            document.getElementById('remove-promo-btn')?.addEventListener('click', removePromoCode);
    
            // Initialize totals
            updateSubtotal();
    
            // Initialize any existing promo code from server-side rendering
            const activePromo = document.getElementById('active-promo');
            if (activePromo) {
                const promoCode = activePromo.querySelector('strong')?.textContent;
                if (promoCode) {
                    window.activePromoCode = {
                        code: promoCode,
                        discount_type: 'percentage', // Default, adjust as needed
                        discount_value: 0 // Will be updated when applied
                    };
                    updateGrandTotal();
                }
            }
        };
    
        // Start the application
        initializeCart();
    });

    function showToast(message, duration = 3000, backgroundColor) {
        // Create toast element if it doesn't exist
        let toast = document.querySelector('.custom-toast');
        
        if (!toast) {
            toast = document.createElement('div');
            toast.className = 'custom-toast';
            document.body.appendChild(toast);
        }
        
        // Set message and optional background color
        toast.textContent = message;
        if (backgroundColor) {
            toast.style.backgroundColor = backgroundColor;
        } else {
            toast.style.backgroundColor = ''; // Reset to default
        }
        
        // Show toast
        toast.classList.add('show');
        
        // Hide after duration
        const timer = setTimeout(() => {
            toast.classList.remove('show');
        }, duration);
        
        // Allow manual dismissal by click
        toast.addEventListener('click', () => {
            clearTimeout(timer);
            toast.classList.remove('show');
        });
    }
    
    // Make it available globally
    window.showToast = showToast;

// Search functionality for both mobile and desktop
document.addEventListener("DOMContentLoaded", () => {
    // Mobile search elements
    const openSearchBtn = document.getElementById("open-search-window");
    const bottomSearchBtn = document.getElementById("bottom-open-search-window");
    const closeSearchBtn = document.getElementById("close-search-window");
    const searchWindow = document.getElementById("search-window");
    const overlay = document.getElementById("overlay");
    const bottomHeader = document.querySelector(".bottom-header");
    const mobileSearchInput = document.getElementById("mobile-search-input");
    const mobileSearchSuggestions = document.getElementById("mobile-search-suggestions");
    const mobileSearchForm = document.getElementById("mobile-search-form");
    
    // Desktop search elements
    const desktopSearchInput = document.getElementById('desktop-search-input');
    const desktopSearchSuggestions = document.getElementById('desktop-search-suggestions');
    const desktopSearchContainer = document.querySelector('.search-container');
    const desktopSearchForm = document.querySelector('.search form'); // Select the desktop search form
    
    let debounceTimer;

    // Open/close search window for mobile
    const openSearchWindow = () => {
        if (searchWindow) searchWindow.classList.add("active");
        if (overlay) overlay.classList.add("active");
        if (bottomHeader) bottomHeader.style.display = "none";
        if (mobileSearchInput) mobileSearchInput.focus();
    };

    const closeSearchWindow = () => {
        if (searchWindow) searchWindow.classList.remove("active");
        if (overlay) overlay.classList.remove("active");
        if (bottomHeader) bottomHeader.style.display = "flex";
        if (mobileSearchSuggestions) mobileSearchSuggestions.style.display = "none";
    };

    // Event listeners for opening/closing mobile search
    if (openSearchBtn) {
        openSearchBtn.addEventListener("click", (e) => {
            e.preventDefault();
            openSearchWindow();
        });
    }

    if (bottomSearchBtn) {
        bottomSearchBtn.addEventListener("click", (e) => {
            e.preventDefault();
            openSearchWindow();
        });
    }

    if (closeSearchBtn) closeSearchBtn.addEventListener("click", closeSearchWindow);
    if (overlay) overlay.addEventListener("click", closeSearchWindow);

    // Auto-suggest functionality for both mobile and desktop
    const handleSearchInput = (inputElement, suggestionsElement) => {
        if (!inputElement) return;
        
        inputElement.addEventListener('input', function(e) {
            clearTimeout(debounceTimer);
            const query = e.target.value.trim();
            
            if (query.length < 2) {
                if (suggestionsElement) {
                    suggestionsElement.innerHTML = '';
                    suggestionsElement.style.display = 'none';
                }
                return;
            }
            
            debounceTimer = setTimeout(() => {
                fetchSearchResults(query, suggestionsElement);
            }, 300);
        });
    };

    // Handle search form submission
    const handleSearchSubmit = (formElement, inputElement, suggestionsElement) => {
        if (!formElement || !inputElement) return;
        
        formElement.addEventListener('submit', function(e) {
            const query = inputElement.value.trim();
            if (!query) {
                e.preventDefault();
                return;
            }
            
            // Check if there are any suggestions visible
            if (suggestionsElement && suggestionsElement.style.display === 'block') {
                const firstSuggestion = suggestionsElement.querySelector('.suggestion-item:not(.no-results):not(.loading)');
                if (firstSuggestion) {
                    e.preventDefault();
                    window.location.href = firstSuggestion.href;
                    return;
                }
            }
            
            // If no suggestions found, let the form submit naturally (which goes to /search-results/?q=query)
            // The form already has action="/search-results/" and method="GET"
        });
    };

    // Handle Enter key in search input
    const handleEnterKey = (inputElement, suggestionsElement) => {
        if (!inputElement) return;
        
        inputElement.addEventListener('keydown', function(e) {
            if (e.key === 'Enter') {
                // For desktop, we don't need to prevent default if the form will handle it
                const query = inputElement.value.trim();
                if (query) {
                    // Check if there are any suggestions visible
                    if (suggestionsElement && suggestionsElement.style.display === 'block') {
                        const firstSuggestion = suggestionsElement.querySelector('.suggestion-item:not(.no-results):not(.loading)');
                        if (firstSuggestion) {
                            e.preventDefault();
                            window.location.href = firstSuggestion.href;
                            return;
                        }
                    }
                    // If no suggestions, let the form submit naturally
                }
            }
        });
    };

    // Initialize mobile search
    handleSearchInput(mobileSearchInput, mobileSearchSuggestions);
    handleSearchSubmit(mobileSearchForm, mobileSearchInput, mobileSearchSuggestions);
    handleEnterKey(mobileSearchInput, mobileSearchSuggestions);

    // Initialize desktop search
    handleSearchInput(desktopSearchInput, desktopSearchSuggestions);
    
    // Handle desktop search form
    if (desktopSearchForm && desktopSearchInput) {
        handleSearchSubmit(desktopSearchForm, desktopSearchInput, desktopSearchSuggestions);
        handleEnterKey(desktopSearchInput, desktopSearchSuggestions);
    }

    // Handle click outside to close suggestions (desktop)
    if (desktopSearchContainer) {
        document.addEventListener('click', function(e) {
            if (desktopSearchSuggestions && !desktopSearchContainer.contains(e.target)) {
                desktopSearchSuggestions.style.display = 'none';
            }
        });
    }
});

// Shared Functions
function fetchSearchResults(query, suggestionsElement) {
    if (!suggestionsElement) return;
    
    // Show loading state
    suggestionsElement.innerHTML = '<div class="suggestion-item loading">Searching...</div>';
    suggestionsElement.style.display = 'block';
    
    fetch(`/search/?q=${encodeURIComponent(query)}`, {
        method: 'GET',
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'Accept': 'application/json'
        }
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        displaySuggestions(data, suggestionsElement);
    })
    .catch(error => {
        console.error('Fetch error:', error);
        suggestionsElement.innerHTML = '<div class="suggestion-item no-results">Error loading results</div>';
        suggestionsElement.style.display = 'block';
    });
}

function displaySuggestions(results, suggestionsElement) {
    if (!suggestionsElement) return;
    
    if (!results || results.length === 0) {
        suggestionsElement.innerHTML = '<div class="suggestion-item no-results">No results found</div>';
        suggestionsElement.style.display = 'block';
        return;
    }

    let html = '';
    results.forEach(item => {
        let url = item.url || '#';
        let icon = 'bi-question-circle';
        let type = '';
        
        if (item.model === 'ourproduct') {
            icon = 'bi-box-seam';
            type = 'Product';
        } else if (item.model === 'productbrand') {
            icon = 'bi-tags';
            type = 'Brand';
        } else if (item.model === 'featurecategory') {
            icon = 'bi-list-ul';
            type = 'Category';
        } else if (item.model === 'productsubcategory') {
            icon = 'bi-list-ul';
            type = 'Sub-Category';
        } else if (item.model === 'productmoresubcategory') {
            icon = 'bi-list-nested';
            type = 'Sub-Category';
        }

        // For mobile search
        if (suggestionsElement.id === 'mobile-search-suggestions') {
            html += `
                <a href="${url}" class="suggestion-item" style="gap:10px">
                    <i class="bi ${icon} suggestion-icon"></i>
                    <span class="suggestion-text">${item.name}</span>
                </a>
            `;
        } 
        // For desktop search
        else {
            html += `
                <a href="${url}" class="suggestion-item">
                    <span class="suggestion-text">${item.name}</span>
                    <span class="suggestion-type">${type}</span>
                </a>
            `;
        }
    });

    suggestionsElement.innerHTML = html;
    suggestionsElement.style.display = 'block';
}
//end
//email subscribe
document.getElementById('subscribeForm').addEventListener('submit', function (e) {
    e.preventDefault();

    let form = e.target;
    let formData = new FormData(form);
    let csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;

    fetch('', {
        method: 'POST',
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRFToken': csrfToken,
        },
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        let alertWrapper = document.getElementById('subscribe-alert-wrapper');
        alertWrapper.innerHTML = `
            <div class="alert alert-${data.status === 'success' ? 'success' : 'danger'} alert-dismissible fade show" role="alert">
                <strong>${data.status === 'success' ? 'Success!' : 'Oops!'}</strong> ${data.message}
                <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
            </div>
        `;
        if (data.status === 'success') {
            form.reset();
        }
    })
    .catch(error => {
        console.error('Error:', error);
    });
});
//lazy load image
document.addEventListener("DOMContentLoaded", function() {
    var lazyImages = [].slice.call(document.querySelectorAll("img.lazyload"));
    if ("IntersectionObserver" in window) {
        let lazyImageObserver = new IntersectionObserver(function(entries, observer) {
            entries.forEach(function(entry) {
                if (entry.isIntersecting) {
                    let lazyImage = entry.target;
                    lazyImage.src = lazyImage.dataset.src;
                    lazyImageObserver.unobserve(lazyImage);
                }
            });
        });
        lazyImages.forEach(function(lazyImage) {
            lazyImageObserver.observe(lazyImage);
        });
    }
});

// Universal product tracking for both static and dynamic content
function trackProductView(event) {
    const productLink = event.target.closest('[data-product-slug]');
    
    if (productLink) {
        event.preventDefault();
        const productSlug = productLink.dataset.productSlug;
        console.log('Tracking product:', productSlug);
        
        // Get CSRF token from meta tag (more reliable)
        const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content || 
                         document.cookie.match(/csrftoken=([^;]+)/)?.[1];
        
        fetch(`/api/track-product-view/${productSlug}/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrfToken,
                'Content-Type': 'application/json'
            },
            credentials: 'same-origin'
        })
        .then(() => {
            console.log('Tracking successful, navigating to:', productLink.href);
            window.location.href = productLink.href;
        })
        .catch(error => {
            console.error('Tracking failed, navigating anyway:', error);
            window.location.href = productLink.href;
        });
    }
}

// Attach event listener to document for dynamic content
document.addEventListener('click', trackProductView);

// Also attach to window load for safety
window.addEventListener('load', () => {
    document.querySelectorAll('[data-product-slug]').forEach(link => {
        link.addEventListener('click', trackProductView);
    });
});


