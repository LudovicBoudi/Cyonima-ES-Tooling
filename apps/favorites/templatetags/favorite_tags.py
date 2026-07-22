from django import template
from ..models import Favorite

register = template.Library()


@register.inclusion_tag('favorites/_button.html', takes_context=True)
def favorite_button(context, user, content_type, object_id):
    is_fav = False
    if user.is_authenticated:
        is_fav = Favorite.objects.filter(
            user=user, content_type=content_type, object_id=object_id
        ).exists()
    return {
        'is_fav': is_fav,
        'content_type': content_type,
        'object_id': object_id,
        'user': user,
        'request': context.get('request'),
    }


@register.simple_tag
def is_favorited(user, content_type, object_id):
    if not user.is_authenticated:
        return False
    return Favorite.objects.filter(
        user=user, content_type=content_type, object_id=object_id
    ).exists()
