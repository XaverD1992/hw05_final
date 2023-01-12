from django.conf import settings
from django.core.paginator import Paginator


def my_paginator(posts, request):
    paginator = Paginator(posts, settings.NUMBER_OF_POSTS_PER_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return page_obj
