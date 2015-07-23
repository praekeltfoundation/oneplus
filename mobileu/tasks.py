from djcelery import celery
from auth.models import Teacher
from core.models import Class, TeacherClass, Participant, ParticipantQuestionAnswer
from django.db.models import Count
from datetime import datetime, timedelta
import csv
from django.core.mail import EmailMessage


@celery.task(bind=True)
def debug_task(self):
    print('Request: {0!r}'.format(self.request))


@celery.task
def send_sms(x, y):
    return x + y


@celery.task
def send_teacher_reports():
    today = datetime.now()
    # first = datetime.datetime(today.year, today.month, 1)
    first = today.replace(year=today.year, month=today.month, day=1)
    last_month = first - timedelta(days=1)

    t_c_rel = TeacherClass.objects.values_list("teacher__id", flat=True).distinct()

    #get all the teachers
    all_teachers = Teacher.objects.filter(email__isnull=False, id__in=t_c_rel)

    for teacher in all_teachers:
        all_teacher_classes_rel = TeacherClass.objects.filter(teacher=teacher)

        #list containing reports for a specific teacher to be emailed
        teacher_reports = list()

        for teach_class in all_teacher_classes_rel:

            #list to store tuple of participant data
            class_list = list()

            all_participants = Participant.objects.filter(classs=teach_class.classs)

            for participant in all_participants:
                all_time_ans_set = ParticipantQuestionAnswer.objects.filter(participant=participant)
                all_time_ans_num = all_time_ans_set.aggregate(Count('id'))['id__count']

                all_time_cor_set = all_time_ans_set.filter(correct=True)
                all_time_cor_num = all_time_cor_set.aggregate(Count('id'))['id__count']
                if all_time_ans_num != 0:
                    all_time_cor_num = all_time_cor_num / all_time_ans_num * 100

                last_month_ans_set = all_time_ans_set.filter(answerdate__month=last_month.month)
                last_month_ans_num = last_month_ans_set.aggregate(Count('id'))['id__count']

                last_month_cor_num = last_month_ans_set.filter(correct=True)\
                    .aggregate(Count('id'))['id__count']
                if last_month_ans_num != 0:
                    last_month_cor_num = last_month_cor_num / last_month_ans_num * 100

                class_list.append((participant.learner.first_name, last_month_ans_num, last_month_cor_num,
                                   all_time_ans_num, all_time_cor_num))

            #create a class report
            report_file = open("%s_class_report.csv" % teach_class.classs.name, 'wb')
            try:
                headings = ("Learner's Name", "Answered LAST MONTH", "Answered Correctly LAST MONTH (%)",
                            "Answered ALL TIME", "Answered Correctly ALL TIME (%)")
                writer = csv.writer(report_file)
                writer.writerow(headings)

                for item in class_list:
                    writer.writerow(item)
            finally:
                report_file.close()

            teacher_reports.append(report_file)

        #email all the reports to a teacher
        month = last_month.strftime("%B")
        subject = "OnePlus report %s" % month
        message = "Please find attached reports of your OnePlus classes for %s." % month
        from_email = "info@oneplus.co.za"

        email = EmailMessage(subject, message, from_email, [teacher.email])
        #attach all the reports for this teacher
        for report in teacher_reports:
            with open(report.name, 'r') as r:
                email.attach(report.name, r.read(), 'text/csv')
        email.send()
