from rest_framework.permissions import BasePermission


class IsAuthorOrReadOnly(BasePermission):

    def has_permission(self, request, view):
        user = request.user.is_authenticated
        if user:
            return True
        if request.method in 'GET':
            return True

        return False

    def AuthorAccess(self, user, obj):
        return obj.author == user

    def has_object_permission(self, request, view, obj):
        if request.method in 'GET':
            return True

        return self.AuthorAccess(request.user, obj) or request.user.is_staff
