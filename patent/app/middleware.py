# from importlib import import_module
# from django.core.cache import cache
# from django.conf import settings
#
# class UserRestrict:
#
#     def __init__(self, get_response):
#         self.get_response = get_response
#         # One-time configuration and initialization.
#
#     def __call__(self, request):
#
#         response = self.get_response(request)
#         """
#         Checks if different session exists for user and deletes it.
#         """
#         if request.user.is_authenticated:
#             cache = cache.get('default')
#             cache_timeout = 86400
#             cache_key = "user_pk_%s_restrict" % request.user.pk
#             cache_value = cache.get(cache_key)
#
#             if cache_value is not None:
#                 if request.session.session_key != cache_value:
#                     engine = import_module(settings.SESSION_ENGINE)
#                     session = engine.SessionStore(session_key=cache_value)
#                     session.delete()
#                     cache.set(cache_key, request.session.session_key,
#                               cache_timeout)
#             else:
#                 cache.set(cache_key, request.session.session_key, cache_timeout)
#
#         return response