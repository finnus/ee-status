from django.db import transaction
from django.http import HttpResponse


# ATOMIC_REQUESTS is on globally, which would otherwise open a transaction --
# and so require a healthy database -- for every probe.
@transaction.non_atomic_requests
def health(request):
    """Liveness probe for the container healthcheck.

    Deliberately touches neither the database nor the cache: a blip in either
    should surface as an error page, not have the orchestrator kill a process
    that is otherwise serving fine.
    """
    return HttpResponse("ok", content_type="text/plain")
