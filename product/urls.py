from django.urls import path
from product import views
app_name = 'product'

urlpatterns = [
    path('product-details/<slug:product_slug>/', views.ProductDetails, name='product-details'),
    path("category-products/<slug:slug>/",views.CategoryProducts, name='category-products'),
    path('brand-products/<slug:brand_slug>/', views.brand_products_view, name='brand-products'),
    path('subcategory-products/<slug:subcategory_slug>/', views.subcategory_products_view, name='subcategory-products'),
    path('api/track-product-view/<slug:product_slug>/', views.track_product_view, name='track_product_view'),
    path('search/', views.search_view, name='search'),
    path("search-results/", views.search_results_view, name="search_results"),
    path('cart/', views.CartView, name='cart-view'),
    path("get-cart-count/", views.get_cart_count, name="get-cart-count"),
    path("add-to-cart/", views.add_to_cart, name="add-to-cart"),
    path("update-cart/", views.update_cart, name="update-cart"),
    path("remove-from-cart/", views.remove_from_cart, name="remove-from-cart"),
    path("buy-now/", views.buy_now, name="buy-now"),
    path("checkout/", views.checkout_view, name="checkout"),
    path('verify-email/', views.verify_email_view, name='verify_email'),
    path('order-confirmation/<str:order_id>/', views.order_confirmation_view, name='order_confirmation'),
    path('apply-promo-code/', views.apply_promo_code, name='apply_promo_code'),
    path('remove-promo-code/', views.remove_promo_code, name='remove_promo_code'),
    path('toggle_wishlist/', views.toggle_wishlist, name='toggle_wishlist'),
    path('wishlist-product/', views.WishlistView, name='wishlist-product'),
    path('dashboard/orders/', views.order_dashboard, name='order_dashboard'),
    path('update-order-status/<int:order_id>/', views.update_order_status, name='update_order_status'),
    path('contact/', views.ContactUsView, name='contact'),
    path("schedule-message/", views.schedule_message_view, name="schedule_message"),
    path("facebook-product-feed.xml", views.facebook_product_feed, name="facebook_product_feed"),
]