from djcelery import celery
from auth.models import Teacher
from core.models import Class, TeacherClass, Participant, ParticipantQuestionAnswer
from organisation.models import Module
from django.db.models import Count
from datetime import datetime, timedelta
import csv
from django.core.mail import EmailMessage
import xlwt
from validate_email import validate_email
from django.core.mail import mail_managers


@celery.task(bind=True)
def debug_task(self):
    print('Request: {0!r}'.format(self.request))


@celery.task
def send_sms(x, y):
    return x + y


def get_teacher_list():
    teacher_list = TeacherClass.objects.filter(teacher__email__isnull=False)\
        .distinct('teacher')
    exclude_list = list()
    for rel in teacher_list:
        if not validate_email(rel.teacher.email):
            exclude_list.append(rel.id)
    return teacher_list.exclude(id__in=exclude_list).values_list('teacher__id')


@celery.task
def send_teacher_reports():
    today = datetime.now()
    # first = datetime.datetime(today.year, today.month, 1)
    first = today.replace(year=today.year, month=today.month, day=1)
    last_month = first - timedelta(days=1)

    #get all the teacher class rel where teachers have set emails
    teacher_list = get_teacher_list()
    all_teachers_list = Teacher.objects.filter(id__in=teacher_list).values('id', 'email', 'username')

    class_list = TeacherClass.objects.filter(teacher__email__isnull=False)\
        .values_list('classs_id')\
        .distinct('classs')
    all_classes = Class.objects.filter(id__in=class_list)

    for current_class in all_classes:
        #list to store tuple of participant data
        class_list = list()

        all_participants = Participant.objects.filter(classs=current_class)

        for participant in all_participants:
            all_time_ans_set = ParticipantQuestionAnswer.objects.filter(participant=participant)
            all_time_ans_num = all_time_ans_set.aggregate(Count('id'))['id__count']

            all_time_cor_set = all_time_ans_set.filter(correct=True)
            all_time_cor_num = all_time_cor_set.aggregate(Count('id'))['id__count']
            if all_time_ans_num != 0:
                all_time_cor_num = all_time_cor_num / all_time_ans_num * 100

            last_month_ans_set = all_time_ans_set.filter(answerdate__year=last_month.year,
                                                         answerdate__month=last_month.month)
            last_month_ans_num = last_month_ans_set.aggregate(Count('id'))['id__count']

            last_month_cor_num = last_month_ans_set.filter(correct=True)\
                .aggregate(Count('id'))['id__count']
            if last_month_ans_num != 0:
                last_month_cor_num = last_month_cor_num / last_month_ans_num * 100

            class_list.append((participant.learner.first_name, last_month_ans_num, last_month_cor_num,
                               all_time_ans_num, all_time_cor_num))

        #create a class report
        csv_class_report = open("%s_class_report.csv" % current_class.name, 'wb')
        try:
            headings = ("Learner's Name", "Answered LAST MONTH", "Answered Correctly LAST MONTH (%)",
                        "Answered ALL TIME", "Answered Correctly ALL TIME (%)")

            writer = csv.writer(csv_class_report)
            writer.writerow(headings)

            xls_class_report = xlwt.Workbook(encoding="utf-8")
            class_worksheet = xls_class_report.add_sheet("%s_class_report" % current_class.name)
            for col_num, item in enumerate(headings):
                class_worksheet.write(0, col_num, item)

            for row_num, row in enumerate(class_list, start=1):
                #csv
                writer.writerow(row)
                #xls
                for col_num, item in enumerate(row):
                    class_worksheet.write(row_num, col_num, item)
        finally:
            csv_class_report.close()
            xls_class_report.save("%s_class_report.xls" % current_class.name)

        #module reports
        class_modules = Module.objects.filter(coursemodulerel__course=current_class.course)
        module_list = list()

        for m in class_modules:
            correct_last_month = 0
            correct_all_time = 0
            answered_all_time = ParticipantQuestionAnswer.objects.filter(question__module=m)
            if answered_all_time.aggregate(Count('id'))['id__count'] != 0:
                correct_all_time = answered_all_time.filter(correct=True).aggregate(Count('id'))['id__count'] \
                    / answered_all_time.aggregate(Count('id'))['id__count'] * 100
                answered_last_month = answered_all_time.filter(answerdate__year=last_month.year,
                                                               answerdate__month=last_month.month)
                if answered_last_month.aggregate(Count('id'))['id__count'] != 0:
                    correct_last_month = answered_last_month.filter(correct=True).aggregate(Count('id'))['id__count'] \
                        / answered_last_month.aggregate(Count('id'))['id__count'] * 100

            module_list.append((m.name, correct_last_month, correct_all_time))

        #create a class report for all the modules
        csv_module_report = open("%s_module_report.csv" % current_class.name, 'wb')
        try:
            headings = ("Module", "Answered Correctly LAST MONTH (%)", "Answered Correctly ALL TIME (%)")
            writer = csv.writer(csv_module_report)
            writer.writerow(headings)

            xls_module_report = xlwt.Workbook(encoding="utf-8")
            modules_worksheet = xls_module_report.add_sheet("%s_module_report" % current_class.name)
            for col_num, item in enumerate(headings):
                modules_worksheet.write(0, col_num, item)

            for row_num, row in enumerate(module_list, start=1):
                #csv
                writer.writerow(row)
                #xls
                for col_num, item in enumerate(row):
                    modules_worksheet.write(row_num, col_num, item)
        finally:
            csv_module_report.close()
            xls_module_report.save("%s_module_report.xls" % current_class.name)

        teachers_to_email = TeacherClass.objects.filter(classs=current_class, teacher__email__isnull=False)\
            .exclude(teacher__email='')\
            .values_list('teacher_id', flat=True)

        for teacher_id in teachers_to_email:
            my_item = next((item for item in all_teachers_list if item['id'] == teacher_id), None)
            if my_item:
                if 'csv_class_reports' in my_item:
                    my_item['csv_class_reports'].append(csv_class_report)
                else:
                    my_item['csv_class_reports'] = [csv_class_report]

                if 'csv_module_reports' in my_item:
                    my_item['csv_module_reports'].append(csv_module_report)
                else:
                    my_item['csv_module_reports'] = [csv_module_report]

                if 'xls_class_reports' in my_item:
                    my_item['xls_class_reports'].append("%s_class_report.xls" % current_class.name)
                else:
                    my_item['xls_class_reports'] = ["%s_class_report.xls" % current_class.name]

                if 'xls_module_reports' in my_item:
                    my_item['xls_module_reports'].append("%s_module_report.xls" % current_class.name)
                else:
                    my_item['xls_module_reports'] = ["%s_module_report.xls" % current_class.name]

    #email the teachers
    month = last_month.strftime("%B")
    subject = "dig-it report %s" % month
    message = "Please find attached reports of your dig-it classes for %s." % month
    from_email = "info@dig-it.me"
    for teacher in all_teachers_list:
        email = EmailMessage(subject, message, from_email, [teacher['email']])
        #attach all the reports for this teacher
        my_item = next((item for item in all_teachers_list if item['id'] == teacher_id), None)
        if my_item:
            for csv_class_report in my_item['csv_class_reports']:
                with open(csv_class_report.name, 'r') as r:
                    email.attach(csv_class_report.name, r.read(), 'text/csv')

            for csv_module_report in my_item['csv_module_reports']:
                with open(csv_module_report.name, 'r') as r:
                    email.attach(csv_class_report.name, r.read(), 'text/csv')

            for xls_class_report in my_item['xls_class_reports']:
                email.attach_file(xls_class_report)

            for xls_module_report in my_item['xls_module_reports']:
                email.attach_file(xls_module_report)
        try:
            email.send()
        except Exception as detail:
            mail_managers("DIG-IT: Teacher report sending failed.", "The system failed to send a teacher report.\n"
                                                            "username: %s\n"
                                                            "email: %s\n"
                                                            "month: %s\n\n\n"
                                                            "Error details: %s"
                                                                    % (teacher['username'],
                                                                       teacher['email'],
                                                                       month,
                                                                       detail))