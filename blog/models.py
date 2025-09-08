from django.db import models
from user.models import CustomUser
from django.utils.text import slugify
from unidecode import unidecode
from tinymce.models import HTMLField
from django.utils import timezone

# Create your models here.
class BlogCategory(models.Model):
    title = models.CharField(max_length=150)
    slug = models.SlugField(max_length=200, blank=True, null= True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)
    def __str__(self):
        return self.title

class BlogTags(models.Model):
    title = models.CharField(max_length=100)
    slug = models.SlugField(max_length=120, blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)
    def __str__(self):
        return self.title

class MyBlog(models.Model):
    title = models.CharField(max_length=250)
    category = models.ForeignKey(BlogCategory, on_delete=models.CASCADE)
    tags = models.ManyToManyField(BlogTags, blank=True)
    blog_pic = models.ImageField(upload_to='blog_main_image', blank=True, null=True)
    slug = models.SlugField(max_length=300, blank=True, null=True)
    blog_details = HTMLField()
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)

    def __str__(self):
        return self.title
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(unidecode(self.title))
        super().save(*args, **kwargs)
    
    class Meta:
        ordering = ('-created_at',)

class BlogComment(models.Model):
    blog = models.ForeignKey(MyBlog, on_delete=models.CASCADE, related_name='comments', blank=True, null=True)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, null=True, blank=True)
    guest_name = models.CharField(max_length=100, blank=True, null=True)
    comment = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        if self.user:
            return f"Comment by {self.user.username} on {self.blog.title}"
        return f"Comment by {self.guest_name} on {self.blog.title}"