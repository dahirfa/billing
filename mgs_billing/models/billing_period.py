from odoo.tools import date_utils
from datetime import date
from dateutil.relativedelta import relativedelta


def get_billing_start_and_end_dates(current_date, start, end):
    if current_date.day <= end:
        if current_date.month != 1:
            start_date = date(current_date.year, current_date.month - 1 , start)
        else:
            start_date = date(current_date.year - 1,  12, start)
            
    elif current_date.day >= start:
        start_date = date(current_date.year, current_date.month, start)
    else:
        if  current_date.month != 1:
            start_date = date(current_date.year, current_date.month - 1, end)
        else:
            start_date = date(current_date.year - 1, 12, end)
    
    if current_date.day <= end:
        end_date = date(current_date.year, current_date.month, end)
    elif current_date.day >= start:
        if  current_date.month != 12:
            end_date = date(current_date.year, current_date.month + 1, end)
        else:
            end_date = date(current_date.year + 1, 1, end)
            
    else:
        end_date = date(current_date.year, current_date.month, end)
    return (start_date, end_date)


setattr(date_utils, 'get_billing_start_and_end_dates',
        get_billing_start_and_end_dates)
