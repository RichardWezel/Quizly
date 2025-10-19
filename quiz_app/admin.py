from django.contrib import admin
from .models import Quiz, Question

@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'description', 'video_url', 'owner', 'created_at', 'updated_at')
    search_fields = ('title', 'description', 'owner__username', 'owner__email')
    list_filter = ('created_at', 'updated_at', 'owner')
    readonly_fields = ('created_at', 'updated_at')

    fields = (
        "title",
        "description",
        "video_url",
        "owner",         
        "created_at",
        "updated_at",
    )

    def save_model(self, request, obj, form, change):
        if not change and not obj.owner_id:
            obj.owner = request.user
        super().save_model(request, obj, form, change)

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('id', 'question_title', 'question_options', 'answer')
    search_fields = ('question_title',)
    list_filter = ('id', 'question_title')
    readonly_fields = ('id',)