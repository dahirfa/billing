from odoo import _, api, fields, models


class AttendanceEmployee(models.Model):
    _inherit = "hr.employee"
    
    
    attendance_rule_id  = fields.Many2one('sa.attendance.rule', string='Attendance Rule', tracking=True)