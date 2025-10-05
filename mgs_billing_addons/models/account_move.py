from odoo import models, fields

from odoo.exceptions import  UserError

class AccountMove(models.Model):
    _inherit = 'account.move'
    
    
    tenant_phone = fields.Char(related="partner_id.phone", string="Tenant Phone")
    sender_phone = fields.Char(related="partner_id.alternative_number", string="Sender Phone")
    
    
    
    