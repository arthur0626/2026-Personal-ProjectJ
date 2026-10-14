from django.shortcuts import render

from common.decorators import owner_required

from .models import ActivityEvent


@owner_required
def timeline(request):
    events = ActivityEvent.objects.filter(user=request.user).select_related('coding_submission')
    return render(request, 'activity/timeline.html', {'events': events})
