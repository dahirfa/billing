from odoo import fields, models, api
from datetime import datetime, date
from odoo.exceptions import UserError, ValidationError
import logging
_logger = logging.getLogger(__name__)

class Mgs_Product_Extension_Hide_Cost(models.Model):
    _inherit = 'product.template'
    
    hide_cost_group_condition_invisible = fields.Boolean(compute='_compute_hide_cost_group_condition_invisible')

    def _compute_hide_cost_group_condition_invisible(self):
        for record in self:                       
            record.hide_cost_group_condition_invisible = self.env.user.has_group('mgs_hide_product_cost.hide_cost_group_invisible')
