from django.contrib import admin

from apps.post.models import Categoria, Post

# Register your models here.
admin.site.register(Categoria)
admin.site.register(Post)