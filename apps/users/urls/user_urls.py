from rest_framework.routers import DefaultRouter
from apps.users.views.user_views import UserViewSet

router = DefaultRouter()
router.register(r'', UserViewSet, basename='users')

urlpatterns = router.urls