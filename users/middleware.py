class GetTokenMiddleware(object):
    """ Middleware used to get the token from HTTP headers """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.META['PATH_INFO'] == '/users/api-token-auth/':
            if 'HTTP_COOKIE' in request.META:
                request.META['HTTP_COOKIE'] = ''
        return self.get_response(request)
