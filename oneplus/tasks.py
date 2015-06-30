from datetime import datetime
from celery import task


@task
def update_num_question_metric():
    update_metric(
        "total.questions",
        1,
        metric_type="SUM"
    )

def update_perc_correct_answers(name, days_ago):
    date_range = (
        datetime.now().date() - timedelta(days=days_ago),
        datetime.now(),
    )
    total = ParticipantQuestionAnswer.objects.filter(
        answerdate__range=date_range
    ).count()
    if total > 0:
        value = ParticipantQuestionAnswer.objects.filter(
            answerdate__range=date_range,
            correct=True
        ).count() / total
    else:
        value = 0
    update_metric(
        "questions.correct." + name,
        value * 100,
        "LAST"
    )

@task
def update_all_perc_correct_answers():
    # Update metrics
    update_perc_correct_answers('24hr', 1)
    update_perc_correct_answers('48hr', 2)
    update_perc_correct_answers('7days', 7)
    update_perc_correct_answers('32days', 32)
