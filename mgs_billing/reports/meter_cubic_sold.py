
from odoo import models, fields, api, tools


class MgsMeterCubicSoldReport(models.Model):
    _name = 'mgs_billing.meter_cubic_sold.report'
    _description = 'mgs_billing.meter_cubic_sold.report'
    _auto = False
    _order = "id DESC"

    zone_id = fields.Many2one(
        'mgs_billing.zone')
    collector_id = fields.Many2one(
        'res.partner', string='Collector', domain=[('is_collector', '=', True)])
    company_id = fields.Many2one(
        'res.company', string='Company', default=lambda self: self.env.company.id)
    total_meter_cubic = fields.Integer(string='Total Meter Cubic')

    @api.model
    def _select(self, report_by='Zone'):
        result = "SELECT mbz.id AS id, mbz.id AS zone_id, mbz.name as zone_name, null AS collector_id, null As collector_name, mbr.company_id AS company_id"

        if report_by == 'Collector':
            result = "SELECT mbz.collector_id AS id, mbz.collector_id AS collector_id, rp.name AS collector_name, null AS zone_id, null AS zone_name,  mbr.company_id AS company_id"

        result += ", sum(mbr.difference) AS total_meter_cubic"
        return result

    @api.model
    def _from(self):
        return """
            FROM mgs_billing_reading mbr
            LEFT JOIN mgs_billing_zone mbz ON mbr.zone_id=mbz.id
            LEFT JOIN res_partner rp ON mbz.collector_id=rp.id
            """

    @api.model
    def _where(self, date_from=fields.Date.today().replace(day=1), date_to=fields.Date.today(), zone_id=None, collector_id=None, company_id=None):
        result = " WHERE mbr.state = 'posted' AND mbr.date BETWEEN '%s' AND '%s'" % (
            date_from, date_to)

        if zone_id:
            result += " AND mbr.zone_id = %s" % zone_id

        if collector_id:
            result += " AND mbz.collector_id = %s" % collector_id

        if company_id:
            result += " AND mbr.company_id = %s" % company_id
        return result

    @api.model
    def _group_by(self, report_by):
        result = "GROUP BY mbz.id, mbr.company_id" if report_by == 'Zone' else "GROUP BY mbz.collector_id, mbr.company_id,rp.name"
        return result

    def query_execute(self, report_by='Zone', date_from=fields.Date.today().replace(day=1), date_to=fields.Date.today(), zone_id=None, collector_id=None, company_id=None):
        result = """
        %s 
        
        %s
         
        %s
         
        %s 
        """ % (self._select(report_by), self._from(), self._where(date_from, date_to, zone_id, collector_id, company_id), self._group_by(report_by))
        return result

    def init(self):
        tools.drop_view_if_exists(self._cr, self._table)
        self._cr.execute('''CREATE OR REPLACE VIEW %s AS (%s)''' %
                         (self._table, self.query_execute()))
