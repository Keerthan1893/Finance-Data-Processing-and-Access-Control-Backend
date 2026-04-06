from rest_framework.routers import DefaultRouter
from apps.records.views import FinancialRecordViewSet

router = DefaultRouter()
router.register(r'records', FinancialRecordViewSet, basename='records')

urlpatterns = router.urls