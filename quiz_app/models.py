from django.db import models
from django.conf import settings

class Quiz(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    video_url = models.URLField(blank=True, null=True, unique=True)
    owner = models.ForeignKey(                      # <-- NEU
        settings.AUTH_USER_MODEL,   
        on_delete=models.CASCADE,             # schützt vor versehentlichem Löschen des Owners
        related_name='quizzes',
        null=False, blank=False,                      # Schritt 1: zunächst optional
        db_index=True,
        help_text="Ersteller des Quizzes"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['video_url'],
                name='unique_quiz_per_video_url'
            )
        ]
        verbose_name = 'Quiz'
        verbose_name_plural = 'Quizzes'

    def __str__(self):
        return self.title


class Question(models.Model):
    quiz = models.ForeignKey(Quiz, related_name='questions', on_delete=models.CASCADE)
    question_title = models.CharField(max_length=255)
    question_options = models.JSONField(default=list)  
    answer = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['id']

    def __str__(self):
        return f"{self.quiz.title} - {self.question_title}"