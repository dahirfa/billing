from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError


class MGSSubPropertyTypes(models.Model):
    _name = 'mgs.property.sub.categories'
    _description = 'Billing Sub Property Types'    
    _order = "id DESC"
    
    name = fields.Char(string = "Property Sub Category", required = True)
    property_type_id = fields.Many2one("mgs_billing.property.type", string = "Property")
    property_ids = fields.One2many("mgs_billing.property", "property_sub_category_id",  string = "Properties")
        
    

class MGSBillingSubPropertyTypes(models.Model):
    _inherit = "mgs_billing.property.type"
    
    property_sub_category_ids = fields.One2many("mgs.property.sub.categories", "property_type_id",  string = "Sub Properties")



    
class MGSBillingProperty(models.Model):
    _inherit = "mgs_billing.property"
    
    property_sub_category_id = fields.Many2one('mgs.property.sub.categories', string = "Property Sub Category", ondelete='restrict', tracking=True)