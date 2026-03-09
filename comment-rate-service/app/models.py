from django.db import models

class CommentRate(models.Model):
    book_id = models.IntegerField()
    customer_id = models.IntegerField()
    rating = models.IntegerField()
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
