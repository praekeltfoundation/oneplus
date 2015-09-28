from djcelery import celery
from auth.models import Teacher
from core.models import Class, TeacherClass, Participant, ParticipantQuestionAnswer
from organisation.models import Module
from django.db.models import Count
from datetime import datetime, timedelta
from validate_email import validate_email
from django.core.mail import mail_managers
from django.conf import settings
from django.core.mail import EmailMessage
import xlwt
import csv
import logging
import traceback

logger = logging.getLogger(__name__)


@celery.task(bind=True)
def debug_task(self):
    print('Request: {0!r}'.format(self.request))


@celery.task
def send_sms(x, y):
    return x + y


def get_teacher_list():
    """
    Return a list of teacher id's who have a valid email
    """
    teacher_list = TeacherClass.objects.filter(teacher__email__isnull=False).\
        values_list("teacher__id", "teacher__email").distinct()
    exclude_list = list()
    for rel in teacher_list:
        if not validate_email(rel[1]):
            exclude_list.append(rel[0])
    return teacher_list.exclude(id__in=exclude_list).values_list('teacher__id', flat=True)


def make_safe_sheet_name(sheet_name):
    return (sheet_name[:31]) if len(sheet_name) > 31 else sheet_name


@celery.task
def send_teacher_reports():
    send_teacher_reports_body()


def send_teacher_reports_body():
    # Get last month date
    today = datetime.now()
    first = today.replace(year=today.year, month=today.month, day=1)
    last_month = first - timedelta(days=1)

    # Get all the teachers with a valid email
    teacher_list = get_teacher_list()
    all_teachers_list = Teacher.objects.filter(id__in=teacher_list).values('id', 'email', 'username')

    # Get all the classes that have an assigned teacher to it
    teacher_class_list = TeacherClass.objects.filter(teacher__id__in=teacher_list)\
        .values_list('classs__id', flat=True)\
        .distinct()
    all_classes = Class.objects.filter(id__in=teacher_class_list)

    # List to be used to store any reports that fail during creation
    failed_reports = list()

    # Iterate through each class and create respective reports
    for current_class in all_classes:
        # List to store tuple of class's participant report data
        class_list = list()

        # Variables used to hold current class and module reports
        csv_class_report = None
        csv_module_report = None
        xls_class_report = None
        xls_module_report = None

        # GENERATE CLASS REPORT
        # Get all participants in the class
        all_participants = Participant.objects.filter(classs=current_class)

        # Iterate through each participant and store generate data needed for the report
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

            # Append a participant with it's data to the class list
            class_list.append((participant.learner.first_name, last_month_ans_num, last_month_cor_num,
                               all_time_ans_num, all_time_cor_num))

        # Create a class report
        class_report_name = "%s%s_%s_%s_%s_class_report" % (settings.MEDIA_ROOT, last_month.year, last_month.month,
                                                            last_month.day, current_class.name)

        try:
            logger.info("Opening file: %s.csv" % class_report_name)
            csv_class_report = open(class_report_name + ".csv", 'wb')
            logger.info("File opened: %s.csv" % class_report_name)
            logger.info("Creating report: %s" % class_report_name)

            headings = ("Learner's Name", "Answered LAST MONTH", "Answered Correctly LAST MONTH (%)",
                        "Answered ALL TIME", "Answered Correctly ALL TIME (%)")

            writer = csv.writer(csv_class_report)
            writer.writerow(headings)

            xls_class_report = xlwt.Workbook(encoding="utf-8")

            class_worksheet = xls_class_report.add_sheet(make_safe_sheet_name("%s_class_report" % current_class.name))

            for col_num, item in enumerate(headings):
                class_worksheet.write(0, col_num, item)

            for row_num, row in enumerate(class_list, start=1):
                # Write to csv file
                writer.writerow(row)

                # Write to xls file
                for col_num, item in enumerate(row):
                    class_worksheet.write(row_num, col_num, item)

            logger.info("Report created: %s" % class_report_name)
        except (OSError, IOError, Exception):
            print traceback.format_exc()
            logger.info("Failed to create report: %s.\n%s" % (class_report_name, traceback.format_exc()))
            failed_reports.append(class_report_name)

        try:
            if csv_class_report is not None:
                logger.info("Saving report: %s.csv" % class_report_name)
                csv_class_report.close()
                logger.info("Report saved: %s.csv" % class_report_name)
        except (OSError, IOError, Exception):
            print traceback.format_exc()
            logger.info("Failed to save report: %s.csv\n%s" % (class_report_name, traceback.format_exc()))
            if class_report_name not in failed_reports:
                failed_reports.append(class_report_name)

        try:
            if xls_class_report is not None:
                logger.info("Saving report: %s.xls" % class_report_name)
                xls_class_report.save(class_report_name + ".xls")
                logger.info("Report saved: %s.xls" % class_report_name)
        except (OSError, IOError, Exception):
            print traceback.format_exc()
            logger.info("Failed to save report: %s.xls\n%s" % (class_report_name, traceback.format_exc()))
            if class_report_name not in failed_reports:
                failed_reports.append(class_report_name)

        # GENERATE MODULE REPORT
        # Get all the modules that the class is linked to
        class_modules = Module.objects.filter(coursemodulerel__course=current_class.course)

        # List to store tuple of class's module report data
        module_list = list()

        # Iterate through each module and store generate data needed for the report
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

             # Append a module with it's data to the module list
            module_list.append((m.name, correct_last_month, correct_all_time))

        # Create a class report
        module_report_name = "%s%s_%s_%s_%s_module_report" % (settings.MEDIA_ROOT, last_month.year, last_month.month,
                                                              last_month.day, current_class.name)

        try:
            logger.info("Opening file: %s.csv" % module_report_name)
            csv_module_report = open(module_report_name + ".csv", 'wb')
            logger.info("File opened: %s.csv" % module_report_name)
            logger.info("Creating report: %s" % module_report_name)

            headings = ("Module", "Answered Correctly LAST MONTH (%)", "Answered Correctly ALL TIME (%)")
            writer = csv.writer(csv_module_report)
            writer.writerow(headings)

            xls_module_report = xlwt.Workbook(encoding="utf-8")
            modules_worksheet = xls_module_report.add_sheet(
                make_safe_sheet_name("%s_module_report" % current_class.name))

            for col_num, item in enumerate(headings):
                modules_worksheet.write(0, col_num, item)

            for row_num, row in enumerate(module_list, start=1):
                # Write to csv file
                writer.writerow(row)

                # Write to xls file
                for col_num, item in enumerate(row):
                    modules_worksheet.write(row_num, col_num, item)

            logger.info("Reports created: %s" % module_report_name)
        except (OSError, IOError, Exception):
            logger.info("Failed to create report: %s\n%s" % (module_report_name, traceback.format_exc()))
            failed_reports.append(module_report_name)

        try:
            if csv_module_report is not None:
                logger.info("Saving report: %s.csv" % module_report_name)
                csv_module_report.close()
                logger.info("Report saved: %s.csv" % module_report_name)
        except (OSError, IOError, Exception):
            logger.info("Failed to save report: %s.csv\n%s" % (module_report_name, traceback.format_exc()))
            if module_report_name not in failed_reports:
                failed_reports.append(module_report_name)

        try:
            if xls_module_report is not None:
                logger.info("Saving report: %s.xls" % module_report_name)
                xls_class_report.save(module_report_name + ".xls")
                logger.info("Report saved: %s.xls" % module_report_name)
        except (OSError, IOError, Exception):
            logger.info("Failed to save report: %s.xls\n%s" % (module_report_name, traceback.format_exc()))
            if module_report_name not in failed_reports:
                failed_reports.append(module_report_name)

        # Get all the teachers of this class
        teachers_to_email = TeacherClass.objects.filter(classs=current_class, teacher__id__in=teacher_list)\
            .values_list('teacher_id', flat=True)

        # Iterate through each teacher and append their reports to the dictionary
        for teacher_id in teachers_to_email:
            my_item = next((item for item in all_teachers_list if item['id'] == teacher_id), None)
            if my_item:
                if 'csv_class_reports' in my_item:
                    my_item['csv_class_reports'].append("%s.csv" % class_report_name)
                else:
                    my_item['csv_class_reports'] = ["%s.csv" % class_report_name]

                if 'csv_module_reports' in my_item:
                    my_item['csv_module_reports'].append("%s.csv" % module_report_name)
                else:
                    my_item['csv_module_reports'] = ["%s.csv" % module_report_name]

                if 'xls_class_reports' in my_item:
                    my_item['xls_class_reports'].append("%s.xls" % class_report_name)
                else:
                    my_item['xls_class_reports'] = ["%s.xls" % class_report_name]

                if 'xls_module_reports' in my_item:
                    my_item['xls_module_reports'].append("%s.xls" % module_report_name)
                else:
                    my_item['xls_module_reports'] = ["%s.xls" % module_report_name]

    # List to be used to store emails that fail to send
    failed_emails = list()

    # Email the teachers their reports
    month = last_month.strftime("%B")
    subject = "dig-it report %s" % month
    message = "Please find attached reports of your dig-it classes for %s." % month
    from_email = "info@dig-it.me"
    logger.info("Emailing teachers.")

    for teacher in all_teachers_list:
        logger.info("Sending email to teacher %s", teacher["email"])
        email = EmailMessage(subject, message, from_email, [teacher['email']])

        # Attach all the reports for this teacher
        try:
            my_item = next((item for item in all_teachers_list if item['id'] == teacher["id"]), None)
            if my_item:
                for csv_class_report in my_item['csv_class_reports']:
                    try:
                        email.attach_file(csv_class_report, "r")
                    except Exception as detail:
                        logger.info("Failed to attach report %s for teacher %s. Reason: %s"
                                    % (csv_class_report, teacher["email"], detail))

                for csv_module_report in my_item['csv_module_reports']:
                    try:
                        email.attach_file(csv_module_report, "r")
                    except Exception as detail:
                        logger.info("Failed to attach report %s for teacher %s. Reason: %s"
                                    % (csv_module_report, teacher["email"], detail))

                for xls_class_report in my_item['xls_class_reports']:
                    try:
                        email.attach_file(xls_class_report, "r")
                    except Exception as detail:
                        logger.info("Failed to attach report %s for teacher %s. Reason: %s"
                                    % (xls_class_report, teacher["email"], detail))

                for xls_module_report in my_item['xls_module_reports']:
                    try:
                        email.attach_file(xls_module_report, "r")
                    except Exception as detail:
                        logger.info("Failed to attach report %s for teacher %s. Reason: %s"
                                    % (xls_module_report, teacher["email"], detail))

            email.send()
        except Exception as detail:
            logger.info("Failed to send email to teacher.\n%s" % traceback.format_exc())
            failed_emails.append((teacher['username'], teacher['email'], detail))

    # Check if any reports failed to get created and notify the managers
    if len(failed_reports) > 0:
        logger.info("Sending failed report email")
        message = "The system failed to create the following reports:\n\n"
        for fail in failed_reports:
            message = "report: %s\n " % fail
        try:
            mail_managers("DIG-IT: Teacher report creation failed.", message, fail_silently=False)
        except Exception as ex:
            logger.error("Error while sending email:\nmsg: %s\nError: %s" % (message, ex))

    # Check if any emails failed to get sent and notify the managers
    if len(failed_emails) > 0:
        logger.info("Sending failed emails email")
        message = "The system failed to email report to the following teachers:\n\n"
        for fail in failed_emails:
            message = "username: %s\n " \
                      "email: %s\n" \
                      "Error details: %s" \
                      % (fail[0],
                         fail[1],
                         fail[2])
        try:
            mail_managers("DIG-IT: Teacher report sending failed.", message, fail_silently=False)
        except Exception as ex:
            logger.error("Error while sending email:\nmsg: %s\nError: %s" % (message, ex))