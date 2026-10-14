from django.shortcuts import get_object_or_404, redirect, render

from common.decorators import owner_required

from .forms import SubmissionForm
from .models import CodingSubmission


@owner_required
def index(request):
    return render(request, 'coding/index.html', {
        'submissions': CodingSubmission.objects.filter(user=request.user),
    })


@owner_required
def detail(request, pk):
    submission = get_object_or_404(CodingSubmission, pk=pk, user=request.user)
    return render(request, 'coding/detail.html', {
        'submission': submission,
        'analyses': submission.analyses.all(),
    })


@owner_required
def new(request):
    form = SubmissionForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        submission = CodingSubmission.record(
            user=request.user,
            ingestion_status=CodingSubmission.IngestionStatus.INGESTED,
            **form.cleaned_data,
        )
        return redirect('coding:detail', pk=submission.pk)
    return render(request, 'coding/new.html', {'form': form})
