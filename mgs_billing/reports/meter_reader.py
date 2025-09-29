from odoo import models
from datetime import date, timedelta, datetime
import calendar

class MeterReaderSummaryReport(models.AbstractModel):
    _name = 'report.mgs_billing.report_meter_reader_summary'
    _description = 'Meter Reader Summary Report'

    def _get_report_values(self, docids, data=None):
        # Convert date string
        date_str = data.get('date')
        if not date_str:
            raise ValueError("Date field is required")
        selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()

        month = selected_date.month
        year = selected_date.year
        month_name = selected_date.strftime('%B')

        # Date range: 20th → last day
        start_date = date(year, month, 20)
        last_day = calendar.monthrange(year, month)[1]
        end_date = date(year, month, last_day)

        # Generate headers
        date_headers = []
        current_day = start_date
        while current_day <= end_date:
            date_headers.append(current_day)
            current_day += timedelta(days=1)

        collector_id = data.get('collector_id')

        # Collectors
        if collector_id:
            collectors = self.env['res.partner'].browse(collector_id)
        else:
            collectors = self.env['res.partner'].search([
                ('is_collector', '=', True)
            ])

        report_data = []
        grand_totals = [0] * len(date_headers)

        for collector in collectors:
            readings = self.env['mgs_billing.reading'].search([
                ('collector_id', '=', collector.id),
                ('date', '>=', start_date),
                ('date', '<=', end_date),
            ])

            # Group by zone
            zones = readings.mapped('zone_id')
            for zone in zones:
                zone_readings = readings.filtered(lambda r: r.zone_id == zone)

                counts_per_day = []
                row_total = 0
                for i, d in enumerate(date_headers):
                    count = len(zone_readings.filtered(lambda r: r.date == d))
                    counts_per_day.append(count)
                    row_total += count
                    grand_totals[i] += count

                report_data.append({
                    'collector': collector,
                    'zone': zone,
                    'counts_per_day': counts_per_day,
                    'row_total': row_total,
                })

        grand_total_all = sum(grand_totals)

        return {
            'doc_model': 'mgs_billing.meter.reader.summary.wizard',
            'month': month,
            'year': year,
            'month_name': month_name,
            'date_headers': date_headers,
            'report_data': report_data,
            'grand_totals': grand_totals,
            'grand_total_all': grand_total_all,
        }
