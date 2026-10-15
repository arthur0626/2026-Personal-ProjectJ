from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from kombu.exceptions import OperationalError

from common.decorators import owner_required
from common.models import ProcessingRun

from .forms import SubmissionForm
from .models import CodingSubmission
from .tasks import analyze_submission


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
        'runs': submission.processing_runs.all(),
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


@owner_required
@require_POST
def request_analysis(request, pk):
    submission = get_object_or_404(CodingSubmission, pk=pk, user=request.user)
    run = ProcessingRun.objects.create(
        user=request.user, run_type='coding.analyze', related_object=submission
    )
    try:
        analyze_submission.delay(run.pk)
    except OperationalError as exc:
        # Broker down: record it instead of leaving the run queued forever.
        run.fail(f'Broker unavailable: {exc}')
    return redirect('coding:detail', pk=pk)
