from rest_framework import permissions

class IsManagerOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        # Разрешение для суперпользователя
#        if request.user.is_superuser:
#            return True
        # Разрешение для менеджеров
        return hasattr(request.user, 'manager')
