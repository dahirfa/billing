from odoo import _, api, fields, models


class SaAttendance(models.Model):
    _inherit = "hr.attendance"

    currency_id     = fields.Many2one('res.currency', 'Currency', store=True, related='employee_id.company_id.currency_id', tracking=True)
    penalty_amount  = fields.Monetary(store=True, pre_compute=True, compute="_compute_penalty", readonly=False, tracking=True)
    waved           = fields.Boolean(default=False, tracking=True)

    @api.model_create_multi
    def create(self, vals_list):
        result = super(SaAttendance, self).create(vals_list)
        result._compute_penalty()
        return result
    
    @api.depends("employee_id", "late_minutes")
    def _compute_penalty(self):
        for r in self:
            if not r.employee_id.attendance_rule_id or r.late_minutes == 0:
                r.penalty_amount=0.0
                return
            r.penalty_amount =  r.employee_id.attendance_rule_id._compute_penalty(r.employee_id, r.check_in, r.late_minutes)
            
    def get_compute_penalty(self):
        for r in self:
            r._compute_penalty()
            
    def action_wave_penalty(self):
        for r in self:
            r.waved = True
            
    def action_unwave_penalty(self):
        for r in self:
            r.waved = False