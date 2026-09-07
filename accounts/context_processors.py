from django.conf import settings

from accounts.models import OwnerPreference
from core.assets import frontend_version

NAV_SECTIONS = {
    "dashboard:index": "overview",
    "dashboard:reports": "analysis",
    "training:history": "history",
    "training:workout-detail": "history",
    "training:routines": "routines",
    "training:routine-detail": "routines",
    "planning:import": "routines",
    "planning:proposal": "routines",
    "training:exercises": "exercises",
    "training:exercise-detail": "exercises",
    "planning:generate": "prompt",
    "planning:generations": "prompt",
    "planning:generation": "prompt",
}


def application_state(request):
    preference = None
    if request.user.is_authenticated:
        preference = OwnerPreference.objects.filter(user=request.user).first()

    from integrations.models import HevyAccount, IntegrationState

    account = (
        HevyAccount.objects.filter(user=request.user).first()
        if request.user.is_authenticated
        else None
    )
    state = (
        IntegrationState.objects.filter(hevy_account=account).first()
        if account
        else None
    )
    return {
        "frontend_version": frontend_version(),
        "active_section": NAV_SECTIONS.get(
            getattr(request.resolver_match, "view_name", ""), ""
        ),
        "connected_account": bool(account and account.encrypted_api_key),
        "data_freshness": state.last_success_at if state else None,
        "signup_available": settings.ALLOW_SIGNUPS,
        "owner_preferences": preference,
        "presentation_mass_unit": preference.mass_unit if preference else "kg",
        "presentation_distance_unit": preference.distance_unit if preference else "km",
    }
