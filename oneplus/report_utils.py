import csv
from django.http import HttpResponse
import xlwt
from datetime import datetime


def get_csv_report(question_list, file_name, columns=None):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="%s_%s.csv"' % (file_name, datetime.now().date().strftime('%Y_%m_%d'))
    writer = csv.writer(response)

    if columns is not None:
        writer.writerows(columns)

    writer.writerows(question_list)

    return response


def get_xls_report(question_list, file_name, columns=None):
    workbook = list_to_workbook(question_list, columns)
    response = HttpResponse(mimetype='application/vnd.ms-excel')
    response['Content-Disposition'] = 'attachment; filename="%s_%s.xls"' % (file_name, datetime.now().date().strftime('%Y_%m_%d'))
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
    report_date = datetime.now().date()
    sheet_name = 'Export {0}'.format(report_date.strftime('%Y-%m-%d'))
    sheet = workbook.add_sheet(sheet_name)

    if not header_style:
        header_style = HEADER_STYLE
    if not default_style:
        default_style = DEFAULT_STYLE
    if not cell_style_map:
        cell_style_map = CELL_STYLE_MAP

    if columns is not None:
        for y, column in enumerate(columns):
            sheet.write(0, y, column, header_style)

        start_x = 1
    else:
        start_x = 0

    for x, obj in enumerate(object_list, start=start_x):
        for y, column in enumerate(obj):
            sheet.write(x, y, obj[y], default_style)

    return workbook