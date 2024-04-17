from rest_framework.permissions import BasePermission


class IsAuthorOrReadOnly(BasePermission):

    def has_permission(self, request, view):
        user = request.user.is_authenticated
        if user:
            return True
        if request.method in 'GET':
            return True
        
        return False

    def has_object_permission(self, request, view, obj):
        if request.method in 'GET':
            return True

        if obj.author == request.user:
            return True

        if request.user.is_staff:
            return True

        return False
