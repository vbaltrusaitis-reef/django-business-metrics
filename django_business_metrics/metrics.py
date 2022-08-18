from django.contrib.auth import get_user_model

def user_count_metric() -> int:
    User = get_user_model()
    return User.objects.count()
