# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
import logging

_logger = logging.getLogger(__name__)


class MGSAssetLocation(models.Model):
    _name = "mgs.asset.location"
    _description = "MGS Asset Location"

    name = fields.Char(string="Location Name", required=True, copy=False)

    location_responsible = fields.Text(string="Location Responsible", required=True)

    phone = fields.Char(string="Phone")



class AccountAssetInherit(models.Model):
    _inherit = 'account.asset'
    

    mgs_location_id = fields.Many2one(
        string='Asset Location',
        comodel_name='mgs.asset.location',
        ondelete='restrict',
    )
    

    
