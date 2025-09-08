from django.db import models
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils.text import slugify
from unidecode import unidecode
from product.models import FeatureCategory

User = get_user_model()

class Poll(models.Model):
    SINGLE = 'single'
    MULTIPLE = 'multiple'
    POLL_TYPE_CHOICES = [
        (SINGLE, 'Single Choice'),
        (MULTIPLE, 'Multiple Choice'),
    ]
    question = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    product_category = models.ForeignKey(FeatureCategory, on_delete=models.CASCADE, blank=True, null=True)
    poll_type = models.CharField(max_length=10, choices=POLL_TYPE_CHOICES, default=SINGLE)
    slug = models.SlugField(unique=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField(null=True, blank=True)
    total_votes = models.PositiveIntegerField(default=0)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(unidecode(self.question))
        super().save(*args, **kwargs)

    def __str__(self):
        return self.question

    def get_absolute_url(self):
        return reverse('poll_detail', kwargs={'slug': self.slug})

    def update_total_votes(self):
        # More efficient way to calculate total votes
        self.total_votes = self.vote_set.count()
        self.save()

class PollOption(models.Model):
    poll = models.ForeignKey(Poll, related_name='options', on_delete=models.CASCADE)
    text = models.CharField(max_length=100, blank=True, null=True)
    image = models.ImageField(upload_to='poll_options/', blank=True, null=True)

    def __str__(self):
        return f"{self.poll.question} - {self.text}"
    
    @property
    def vote_count(self):
        return self.vote_set.count()
    
    @property
    def percentage(self):
        if self.poll.total_votes == 0:
            return 0
        return round((self.vote_count / self.poll.total_votes) * 100, 2)

class Vote(models.Model):
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE)
    option = models.ForeignKey(PollOption, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    session_key = models.CharField(max_length=100, blank=True, null=True)
    ip_address = models.GenericIPAddressField()
    voted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['poll', 'user']),
            models.Index(fields=['poll', 'session_key']),
            models.Index(fields=['poll', 'ip_address']),
        ]
        unique_together = [['poll', 'user'], ['poll', 'session_key'], ['poll', 'ip_address']]

class PollView(models.Model):
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE)
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    session_key = models.CharField(max_length=100, blank=True, null=True)
    ip_address = models.GenericIPAddressField()
    viewed_at = models.DateTimeField(auto_now_add=True)