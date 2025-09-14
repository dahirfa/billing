from odoo import models, fields, api
import qrcode
import base64
from io import BytesIO

class Mgs_Project_Stage_Extension(models.Model):
    _inherit = 'helpdesk.stage'
    
    does_appear_in_mobile = fields.Boolean(string="Appears in Mobile", default=False)