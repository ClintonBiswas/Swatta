import string, random
from django.db.models import Avg, Count
from decimal import Decimal
from django.db import models
from django.utils.text import slugify
from tinymce.models import HTMLField
from django.contrib.auth import get_user_model
from django.core.validators import RegexValidator, FileExtensionValidator
from django.utils import timezone
from django.utils.crypto import get_random_string
from django.contrib.sessions.models import Session
from django.core.exceptions import ValidationError 
from django.urls import reverse

User = get_user_model()

class FeatureCategory(models.Model):
    title = models.CharField(max_length=100)
    slug = models.SlugField(max_length=150, unique=True, blank=True, null=True)
    category_pic = models.ImageField(upload_to='feature_category_pics')
    discount = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.title} - ({self.discount}% discount)"

    class Meta:
        ordering = ['-id']

class ProductBrand(models.Model):
    title = models.CharField(max_length=100)
    slug = models.SlugField(max_length=150, unique=True, blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title
    class Meta:
        ordering = ['-id']

class ProductSubcategory(models.Model):
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=150, unique=True, blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title
    
    
class ProductColor(models.Model):
    name = models.CharField(max_length=50, unique=True)
    hex_code = models.CharField(max_length=7, blank=True, null=True)

    def __str__(self):
        return self.name

product_type_choice = (
    ('Boutique', 'Boutique'),
    ('Pakistani', 'Pakistani'),
    ('Batik', 'Batik'),
    ('Silk', 'Silk'),
    ('Half Silk', 'Half Silk'),
    ('Tant', 'Tant'),
)
class ProductSizes(models.Model):
    title = models.CharField(max_length=10)

    def __str__(self):
        return self.title
    
class ProductMoreSubCategory(models.Model):
    category = models.ForeignKey(FeatureCategory, on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    slug = models.SlugField(max_length=150, unique=True, blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.category.title} - {self.title}"

class OurProduct(models.Model):
    product_name = models.CharField(max_length=500, db_index=True)
    product_brand = models.ForeignKey(ProductBrand, on_delete=models.CASCADE, blank=True, null=True)
    product_category = models.ForeignKey(FeatureCategory, on_delete=models.CASCADE, db_index=True)
    product_sub_category = models.ForeignKey(ProductSubcategory, blank=True, null=True, on_delete=models.CASCADE, db_index=True)
    product_more_sub_category = models.ForeignKey(ProductMoreSubCategory, on_delete=models.CASCADE, blank=True, null=True)
    product_colors = models.ManyToManyField(ProductColor, blank=True)
    product_image = models.ImageField(
        upload_to='product_main_images',
        validators=[FileExtensionValidator(['jpg', 'jpeg', 'png', 'webp'])],
        )
    product_price = models.DecimalField(max_digits=10, decimal_places=2)
    product_make = models.CharField(choices=product_type_choice, max_length=100, blank=True)
    product_size = models.ManyToManyField(ProductSizes, blank=True)
    product_status = models.BooleanField(default=True)
    product_code = models.CharField(max_length=12, unique=True, blank=True)
    product_slug = models.SlugField(max_length=255, unique=True, blank=True)
    video_url = models.URLField(blank=True, null=True, max_length=300)
    product_details = HTMLField()
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)
    view_count = models.PositiveIntegerField(default=0)
    last_viewed = models.DateTimeField(auto_now=True, blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.product_code:
            self.product_code = self.generate_product_code()

        # Generate base slug
        if not self.product_slug:
            base_slug = slugify(self.product_name)
            slug = base_slug
            num = 1

            # Ensure uniqueness BEFORE saving
            while OurProduct.objects.filter(product_slug=slug).exists():
                slug = f"{base_slug}-{num}"
                num += 1
            
            self.product_slug = slug

        super().save(*args, **kwargs)

    def generate_product_code(self):
        """Generate a unique 10-character product code based on the name"""
        name_part = ''.join(e.upper() for e in self.product_name if e.isalnum())[:5]
        random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))
        return (name_part + random_part).upper()[:10]
    def get_absolute_url(self):
        return reverse('product:product-details', kwargs={'product_slug': self.product_slug})

    def discounted_price(self):
        """Calculate price after applying category discount (handles None cases)"""
        discount = getattr(self.product_category, 'discount', Decimal(0)) or Decimal(0)  
        discount_amount = (discount / Decimal(100)) * self.product_price  
        final_price = self.product_price - discount_amount

        # Round to 2 decimal places
        return final_price.quantize(Decimal('0.00'))
    def total_reviews(self):
        return self.reviews.aggregate(total=Count('id'))['total'] or 0

    def average_rating(self):
        result = self.reviews.aggregate(avg_rating=Avg('rating'))
        return round(result['avg_rating'], 1) if result['avg_rating'] else 0

    def __str__(self):
        return f"{self.product_name} - {self.product_code} - {self.product_slug}"
    
    def increment_view_count(self):
        # Use atomic update to prevent race conditions
        OurProduct.objects.filter(pk=self.pk).update(
            view_count=models.F('view_count') + 1,
            last_viewed=timezone.now()
        )
        self.refresh_from_db()

    class Meta:
        ordering = ['-created_at']

class ProductImage(models.Model):
    product = models.ForeignKey(OurProduct, on_delete=models.CASCADE, related_name="images")
    color = models.ForeignKey(ProductColor, on_delete=models.SET_NULL, null=True, blank=True)
    image = models.ImageField(
        upload_to='product-multiple-images',
        validators=[FileExtensionValidator(['jpg', 'jpeg', 'png', 'webp'])],
    )
    alt_text = models.CharField(max_length=255, blank=True, null=True)
    display_order = models.PositiveIntegerField(
        default=0,
        blank=True,
        null=True,
        help_text="Order in which images appear (lower numbers first)"
    )
    
    class Meta:
        ordering = ['display_order']
        verbose_name = "Additional Product Image"
        verbose_name_plural = "Additional Product Images"

    def __str__(self):
        return f"{self.product.product_name} - {self.color.name if self.color else 'No Color'} - Image {self.display_order}"

#popularity product view count
class ProductView(models.Model):
    product = models.ForeignKey(OurProduct, on_delete=models.CASCADE, related_name='product_views')  # Changed related_name
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    session_key = models.CharField(max_length=40, null=True, blank=True)  # Changed from Session FK
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

RATING_CHOICES = [
    (1, '⭐ One Star'),
    (2, '⭐⭐ Two Stars'),
    (3, '⭐⭐⭐ Three Stars'),
    (4, '⭐⭐⭐⭐ Four Stars'),
    (5, '⭐⭐⭐⭐⭐ Five Stars'),
]

class CustomerReview(models.Model):
    product = models.ForeignKey(OurProduct, on_delete=models.CASCADE, related_name="reviews")
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=40, blank=True, null=True) 
    comment = models.TextField()
    rating = models.PositiveSmallIntegerField(choices=RATING_CHOICES, default=5)  
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        # Use the stored name if available, otherwise use user name or Anonymous
        if self.name:
            return f"Review for {self.product.product_name} by {self.name}"
        elif self.user:
            return f"Review for {self.product.product_name} by {self.user.name}"
        else:
            return f"Review for {self.product.product_name} by Anonymous"

    def get_display_name(self):
        """Method to get the display name for templates"""
        if self.name:
            return self.name
        elif self.user:
            return self.user.name
        else:
            return "Anonymous"

# Customer Question Model
class CustomerQuestion(models.Model):
    product = models.ForeignKey(OurProduct, on_delete=models.CASCADE, related_name="questions")
    question = models.CharField(max_length=255)
    answer = models.TextField(blank=True, null=True)  
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Question for {self.product.product_name}: {self.question}"
    

DELIVERY_COST_CHOICES = [
    ('inside_dhaka', 'Inside Dhaka - 70৳'),
    ('outside_dhaka', 'Outside Dhaka - 130৳'),
]

def normalize_phone(phone):
    """Convert Bangla digits to English and clean phone number"""
    if not phone:
        return ""
    bangla_to_english = str.maketrans('০১২৩৪৫৬৭৮৯', '0123456789')
    phone = str(phone).translate(bangla_to_english)
    digits = ''.join(c for c in phone if c.isdigit())
    return digits[-11:] if digits else ""

class ShippingInformation(models.Model):
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        related_name='shipping_infos'
    )
    full_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(
        max_length=15,
        validators=[RegexValidator(regex=r'^\d{11}$', message="Phone number must be 11 digits.")]
    )
    city = models.CharField(max_length=100)
    address = models.CharField(max_length=250)
    special_note = models.CharField(max_length=500, blank=True, null=True)
    delivery_location = models.CharField(
        max_length=15, 
        choices=DELIVERY_COST_CHOICES, 
        default='outside_dhaka'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = [('user', 'phone')]

    def __str__(self):
        return f"{self.full_name} - {self.address}"

    def save(self, *args, **kwargs):
        self.phone = normalize_phone(self.phone)
        if self.is_active:
            ShippingInformation.objects.filter(
                user=self.user,
                phone=self.phone
            ).exclude(pk=self.pk).update(is_active=False)
        super().save(*args, **kwargs)

    @property
    def get_delivery_cost(self):
        return Decimal('70') if self.delivery_location == "inside_dhaka" else Decimal('130')

class MyCart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)
    session_key = models.CharField(max_length=40, null=True, blank=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Cart ({'User: ' + self.user.email if self.user else 'Guest'})"

    def total_items(self):
        return self.items.aggregate(total=models.Sum('quantity'))['total'] or 0

    def total_price(self):
        return sum(item.total_price() for item in self.items.all())

class CartItem(models.Model):
    cart = models.ForeignKey(MyCart, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey('OurProduct', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    size = models.CharField(max_length=500, blank=True, null=True)
    color = models.CharField(max_length=500, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)

    class Meta:
        unique_together = ('cart', 'product')

    def __str__(self):
        return f"{self.quantity} x {self.product.product_name}"

    def total_price(self):
        return self.product.discounted_price() * self.quantity
    @property
    def display_image(self):
        if self.color:
            # Try to find an image matching the selected color
            color_image = self.product.images.filter(
                color__name__iexact=self.color
            ).first()
            if color_image:
                return color_image.image.url
        # Fall back to main product image
        return self.product.product_image.url

    def to_dict(self):
        """Helper method to serialize cart item data"""
        return {
            'id': self.id,
            'product_id': self.product.id,
            'product_name': self.product.product_name,
            'quantity': self.quantity,
            'size': self.size,
            'color': self.color,
            'price': str(self.product.discounted_price()),
            'total_price': str(self.total_price()),
            'image_url': self.display_image,  # This ensures the URL is properly serialized
            'product_url': self.product.get_absolute_url()
        }

class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    session_key = models.CharField(max_length=40, blank=True, null=True)
    shipping_info = models.ForeignKey(
        ShippingInformation,
        on_delete=models.PROTECT,
        related_name='orders'
    )
    cart = models.ForeignKey(MyCart, on_delete=models.SET_NULL, null=True, blank=True)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    delivery_cost = models.DecimalField(max_digits=6, decimal_places=2, default=0.00)
    grand_total = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    promo_code_used = models.CharField(max_length=150, null=True, blank=True)
    verification_code = models.CharField(max_length=6, blank=True, null=True)
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('confirmed', 'Confirmed'),
            ('shipped', 'Shipped'),
            ('delivered', 'Delivered'),
            ('canceled', 'Canceled'),
        ],
        default='pending'
    )
    is_verified = models.BooleanField(default=False)
    order_id = models.CharField(max_length=8, unique=True, editable=False, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order {self.id} - {self.user if self.user else 'Guest'}"

    def save(self, *args, **kwargs):
        if not self.order_id:
            self.order_id = self.generate_unique_order_id()
        super().save(*args, **kwargs)

    def generate_unique_order_id(self):
        while True:
            order_id = str(random.randint(100000, 99999999))
            if not Order.objects.filter(order_id=order_id).exists():
                return order_id
    def clean(self):
        if self.status == 'confirmed' and not self.is_verified:
            raise ValidationError("Order must be verified before confirmation")

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="order_items")
    product = models.ForeignKey('OurProduct', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    size = models.CharField(max_length=500, blank=True, null=True)
    color = models.CharField(max_length=500, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)

    def __str__(self):
        return f"{self.quantity} x {self.product.product_name} in Order {self.order.id}"
    @property
    def display_image(self):
        """Get the correct product image based on ordered color"""
        if self.color:
            # Try to find an image matching the ordered color
            color_image = self.product.images.filter(
                color__name__iexact=self.color
            ).first()
            if color_image:
                return color_image.image
        # Fall back to main product image
        return self.product.product_image
    
# other model for user 
class ContactWithUs(models.Model):
    name = models.CharField(max_length=50)
    email = models.EmailField(max_length=100)
    phone = models.CharField(max_length=11, help_text="Enter 11 digit Ex. 01628777777")
    message = models.TextField()

    def __str__(self):
        return self.name

class PromoCode(models.Model):
    code = models.CharField(max_length=20, unique=True)
    discount_type = models.CharField(
        max_length=10,
        choices=[('percentage', 'Percentage'), ('fixed', 'Fixed Amount')],
        default='fixed'
    )
    discount_value = models.DecimalField(max_digits=10, decimal_places=2)
    valid_from = models.DateTimeField(default=timezone.now)
    valid_to = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    max_uses = models.PositiveIntegerField(default=1)
    times_used = models.PositiveIntegerField(default=0)
    
    class Meta:
        verbose_name = "Promo Code"
        verbose_name_plural = "Promo Codes"
    
    def __str__(self):
        return self.code
    
    def is_valid(self):
        now = timezone.now()
        return (
            self.is_active and
            self.valid_from <= now <= self.valid_to and
            (self.max_uses == 0 or self.times_used < self.max_uses)
        )
    
    def apply_discount(self, amount):
        if self.discount_type == 'percentage':
            return amount * (1 - Decimal(self.discount_value / 100))
        elif self.discount_type == 'fixed':
            return max(amount - Decimal(self.discount_value), Decimal(0))
        return amount
    def get_discount_display(self):
        if self.discount_type == 'percentage':
            return f"{self.discount_value}%"
        elif self.discount_type == 'fixed':
            return f"৳{self.discount_value}"
        return ""

class Wishlist(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    products = models.ManyToManyField(OurProduct)

    def __str__(self):
        return self.user.name

# scheduling a message
class ScheduledMessage(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
    ]

    message = models.TextField()
    scheduled_time = models.DateTimeField()
    send_to_all = models.BooleanField(default=True)
    phone_numbers = models.TextField(blank=True, null=True, help_text="Comma-separated list") 
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    def is_due(self):
        return self.scheduled_time <= timezone.now()