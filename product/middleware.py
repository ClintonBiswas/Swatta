import logging
logger = logging.getLogger(__name__)
class ProductViewMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        
        # Skip API tracking requests to avoid duplicates
        if not request.path.startswith('/api/track-product-view/') and \
           response.status_code == 200 and \
           request.method == 'GET' and \
           request.path.startswith('/products/'):
            
            try:
                product_slug = request.path.split('/')[2]
                if not request.session.get(f'viewed_product_{product_slug}'):
                    # Let the JavaScript handle the tracking for consistency
                    pass
            except Exception:
                logger.exception("Middleware tracking failed")
        
        return response