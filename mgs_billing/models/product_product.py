from odoo import models, fields, api

from odoo.exceptions import ValidationError

class MGSBillingPlan(models.Model):
    _inherit = 'product.template'
    
    is_billing_pan = fields.Boolean(string='Billing Plan',default=False)

    def action_open_billing_products_menu(self):
        billing_product_category=self.env.company.mgs_plan_categ_id
        if not billing_product_category:
            raise ValidationError("Set Billing Plan Categoty in the settings")
        return {
            'type': 'ir.actions.act_window',
            'name': 'Billing Plan',
            'view_mode': 'kanban,list,form',
            'res_model': 'product.template',
            'domain': [('is_billing_pan','=',True),('type','=','service')],
            'context': "{'default_is_billing_pan': True,'default_categ_id': %s,'default_detailed_type': 'service'}"%billing_product_category.id}