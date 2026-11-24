from .permissions import is_admin, is_manager


def roles(request):
    """Lets templates hide actions the current user is not allowed to take."""
    user = getattr(request, 'user', None)
    if user is None or not user.is_authenticated:
        return {'can_manage': False, 'is_admin': False}
    return {'can_manage': is_manager(user), 'is_admin': is_admin(user)}
