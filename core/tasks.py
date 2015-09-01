from djcelery import celery
from datetime import datetime, timedelta
from core.models import BadgeAwardLog, Setting
from django.core.mail import EmailMultiAlternatives
from django.db.models import Count


@celery.task
def weekly_badge_email():
    week_range = datetime.now() - timedelta(weeks=1)
    results = BadgeAwardLog.objects.filter(award_date__gte=week_range).\
        values("participant_badge_rel__participant__learner__first_name",
               "participant_badge_rel__participant__learner__last_name",
               "participant_badge_rel__scenario__name").\
        annotate(count=Count("participant_badge_rel")).\
        order_by("participant_badge_rel__participant__learner__last_name",
                 "participant_badge_rel__participant__learner__first_name")

    html_content = "<!DOCTYPE html><html><body><table>"
    html_content += "<head><style>table {border-collapse: collapse;}" \
                    "table, td, th {border: 1px solid black;}</style></head>"
    html_content += "<tr><th>Learner's Name</th>"
    html_content += "<th>Badge Name</th>"
    html_content += "<th>Badge Count</th></tr>"
    for result in results:
        html_content += "<tr><td>%s %s</td>" % (result["participant_badge_rel__participant__learner__first_name"],
                                                result["participant_badge_rel__participant__learner__last_name"])
        html_content += "<td>%s</td>" % result["participant_badge_rel__scenario__name"]
        html_content += "<td>%s</td></tr>" % result["count"]

    html_content += "</table></body></html>"

    subject = "dig-it Weekly Badge Earners %s - %s" % (week_range.date(), datetime.now().date())
    to = Setting.objects.get(key="WEEKLY_BADGE_EMAIL").value
    from_email = "info@dig-it.me"

    text_content = 'This email contains a list of all the dig-it learners that earned badges this week.'
    msg = EmailMultiAlternatives(subject, text_content, from_email, [to])
    msg.attach_alternative(html_content, "text/html")
    msg.send()
