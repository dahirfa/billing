# -*- coding: utf-8 -*-
###################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2020-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Ijaz Ahammed (odoo@cybrosys.com)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
###################################################################################

from odoo import models, api, fields


class PayslipLateCheckIn(models.Model):
    _inherit = 'hr.payslip'

    late_check_in_ids = fields.Many2many('late.check_in',compute="get_late_check_in_ids",
    store=True
    )
    
    @api.depends('employee_id','date_to','date_from')
    def get_late_check_in_ids(self):
        obj =  self.env['late.check_in']
        for r in self:
            r.late_check_in_ids =[(6,0, obj.search([('employee_id', '=', r.employee_id.id),('date', '<=', r.date_to),('date', '>=', r.date_from),('state', '=', 'approved'),]).ids)]
    
    # def send_report(self):
    #     for rec in self:
    #         if len(rec.late_check_in_ids)>0:
    #             template_id = self.env.ref('employee_late_check_in_ent.email_template_late_check_in').id
    #             self.env['mail.template'].browse(template_id).send_mail(rec.id, force_send=True)
                
    def action_payslip_done(self):
        # self.send_report()
        for recd in self.late_check_in_ids:
            recd.state = 'deducted'
        return super(PayslipLateCheckIn, self).action_payslip_done()
