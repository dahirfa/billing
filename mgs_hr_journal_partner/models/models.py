# -*- coding: utf-8 -*-

from odoo import models


class MgsHrJournalPartner(models.Model):
    _inherit = 'hr.payslip'

    def set_move_partner(self):
        for r in self:
            move_id                 =   r.move_id
            rec_account             =   r.struct_id.rule_ids.filtered(lambda line: line.code=='ELEC')
            partner_id              =   r.employee_id.address_home_id or None
            mgs_billing_account_id  =   r.employee_id.mgs_billing_account_id or None
            
            if move_id and partner_id:
                lines   =   move_id.line_ids.filtered(lambda line: not line.partner_id)
                e_line  =   move_id.line_ids.filtered(lambda line: line.account_id.id==rec_account.account_debit.id)
                lines.write({'partner_id':partner_id.id})
                e_line.write({'partner_id' : mgs_billing_account_id.id})
    # @api.model
    def action_payslip_done(self):
        result = super(MgsHrJournalPartner, self).action_payslip_done()
        self.set_move_partner()
        return result
