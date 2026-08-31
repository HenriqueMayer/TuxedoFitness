from django.conf import settings

from accounts.models import OwnerPreference


def application_state(request):
    preference = None
    if request.user.is_authenticated:
        preference = OwnerPreference.objects.filter(user=request.user).first()

    return {
        'signup_available': settings.ALLOW_SIGNUPS,
        'owner_preferences': preference,
        'presentation_mass_unit': preference.mass_unit if preference else 'kg',
        'presentation_distance_unit': preference.distance_unit if preference else 'km',
    }
