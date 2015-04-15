import csv
from django.http import HttpResponse
import xlwt
import datetime


def get_csv_report(_question_list):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="question_difficulty_report.csv"'
    writer = csv.writer(response)

    for item in _question_list:
        writer.writerow([item[0], item[1], item[2], item[3]])

    return response


def get_xls_report(_question_list):
    columns = (
        'question_id',
        'answered_correct',
        'answered_wrong',
        'percent_answered_correct')
    workbook = list_to_workbook(_question_list, columns)
    response = HttpResponse(mimetype='application/vnd.ms-excel')
    response['Content-Disposition'] = 'attachment; filename="question_difficulty_report.xls"'
    workbook.save(response)
    return response


HEADER_STYLE = xlwt.easyxf('font: bold on')
DEFAULT_STYLE = xlwt.easyxf()
CELL_STYLE_MAP = (
    (datetime.date, xlwt.easyxf(num_format_str='DD/MM/YYYY')),
    (datetime.time, xlwt.easyxf(num_format_str='HH:MM')),
    (bool,          xlwt.easyxf(num_format_str='BOOLEAN')),
)


def list_to_workbook(object_list, columns, header_style=None, default_style=None, cell_style_map=None):
    workbook = xlwt.Workbook()
    report_date = datetime.date.today()
    sheet_name = 'Export {0}'.format(report_date.strftime('%Y-%m-%d'))
    sheet = workbook.add_sheet(sheet_name)

    if not header_style:
        header_style = HEADER_STYLE
    if not default_style:
        default_style = DEFAULT_STYLE
    if not cell_style_map:
        cell_style_map = CELL_STYLE_MAP

    for y, column in enumerate(columns):
        sheet.write(0, y, column, header_style)

    for x, obj in enumerate(object_list, start=1):
        for y, column in enumerate(columns):
            sheet.write(x, y, obj[y], default_style)

    return workbook