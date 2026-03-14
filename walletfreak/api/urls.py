from ninja import NinjaAPI
from api.auth_middleware import BearerAuth
from api.routers.auth import router as auth_router
from api.routers.wallet import router as wallet_router
from api.routers.cards import router as cards_router
from api.routers.personality import router as personality_router
from api.routers.blog import router as blog_router
from api.routers.datapoints import router as datapoints_router
from api.routers.subscriptions import router as subscriptions_router
from api.routers.loyalty import router as loyalty_router
from api.routers.profile import router as profile_router
from api.routers.calculators import router as calculators_router
from api.routers.booking import router as booking_router

api = NinjaAPI(
    title="WalletFreak API",
    version="1.0.0",
    description="Mobile API for WalletFreak",
    urls_namespace="api",
)

# Public endpoints (no auth required)
api.add_router("/auth/", auth_router)

# Protected endpoints (Bearer token required)
api.add_router("/wallet/", wallet_router)
api.add_router("/cards/", cards_router)
api.add_router("/personalities/", personality_router)
api.add_router("/blog/", blog_router)
api.add_router("/datapoints/", datapoints_router)
api.add_router("/subscriptions/", subscriptions_router)
api.add_router("/loyalty/", loyalty_router)
api.add_router("/profile/", profile_router)
api.add_router("/calculators/", calculators_router)
api.add_router("/booking/", booking_router)
