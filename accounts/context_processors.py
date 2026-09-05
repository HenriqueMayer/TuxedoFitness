from django.conf import settings

from accounts.models import OwnerPreference


def application_state(request):
    preference = None
    if request.user.is_authenticated:
        preference = OwnerPreference.objects.filter(user=request.user).first()

    from integrations.models import HevyAccount, IntegrationState
    account = HevyAccount.objects.filter(user=request.user).first() if request.user.is_authenticated else None
    state = IntegrationState.objects.filter(hevy_account=account).first() if account else None
    return {
        'connected_account': bool(account and account.encrypted_api_key),
        'data_freshness': state.last_success_at if state else None,
        'signup_available': settings.ALLOW_SIGNUPS,
        'owner_preferences': preference,
        'presentation_mass_unit': preference.mass_unit if preference else 'kg',
        'presentation_distance_unit': preference.distance_unit if preference else 'km',
    }
