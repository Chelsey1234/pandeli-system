from django.shortcuts import redirect
from django.urls import reverse
from django.conf import settings

class LoginRequiredMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Check if the path is exempt from login
        if self.is_public_path(request.path):
            response = self.get_response(request)
            # Login/logout/public pages should not be cached either.
            self._set_no_cache_headers(response)
            return response
        
        # Check if user is authenticated
        # Note: This will only work AFTER AuthenticationMiddleware has run
        if not hasattr(request, 'user') or not request.user.is_authenticated:
            # Redirect to login page with next parameter
            login_url = reverse('login')
            next_url = request.path
            response = redirect(f'{login_url}?next={next_url}')
            self._set_no_cache_headers(response)
            return response

        # Restrict production team accounts to a limited module set.
        if self._is_production_team(request):
            # Allow API requests used by UI widgets.
            if not request.path.startswith('/api/'):
                allowed_path_prefixes = (
                    '/orders/',
                    '/inventory/',
                    '/products/',
                    '/messages/',
                    '/profile/',
                    '/logout/',
                    '/static/',
                    '/media/',
                )
                if not request.path.startswith(allowed_path_prefixes):
                    response = redirect('order_list')
                    self._set_no_cache_headers(response)
                    return response

        response = self.get_response(request)
        # Prevent protected content from being cached,
        # so browser back after logout won't reveal prior pages.
        self._set_no_cache_headers(response)
        return response
    
    def is_public_path(self, path):
        """Check if the path is public (doesn't require login)"""
        public_paths = [
            reverse('login'),
            '/admin/login/',
            '/static/',
            '/media/',
        ]
        
        # Add any additional public paths
        for public_path in public_paths:
            if path.startswith(public_path):
                return True
        
        # Check if path is in settings.PUBLIC_PATHS if defined
        if hasattr(settings, 'PUBLIC_PATHS'):
            for public_path in settings.PUBLIC_PATHS:
                if path.startswith(public_path):
                    return True
        
        return False

    def _set_no_cache_headers(self, response):
        response['Cache-Control'] = 'no-cache, no-store, must-revalidate, private'
        response['Pragma'] = 'no-cache'
        response['Expires'] = '0'

    def _is_production_team(self, request):
        return (
            hasattr(request, 'user')
            and request.user.is_authenticated
            and hasattr(request.user, 'profile')
            and request.user.profile.role == 'production_admin'
        )