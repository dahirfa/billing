
from odoo import models, fields
from odoo.exceptions import UserError

class ResCompany(models.Model):
    _inherit = 'res.company'

    mgs_sparkmeter_api_link = fields.Char(string='API Link')
    mgs_sparkmeter_api_key = fields.Char(string='API Key')
    mgs_sparkmeter_api_secret = fields.Char(string='API Secret')
    mgs_meters_per_click = fields.Integer(string='Meters Per Click')
    mgs_sparkmeter_service_area_id = fields.Char(string='Sevice Area ID')
    mgs_sparkmeter_follower_ids = fields.Many2many('res.users',string='Spark Email Follower IDs')
    mgs_sparkmeter_prb = fields.Integer(string='Pervent Readings Before(days)')
    

    def check_sparkmeter_credentials(self):
        current_company = self

        if not current_company.mgs_sparkmeter_api_link:
            raise UserError(
                "Please write API link in the billing settings")

        if not current_company.mgs_sparkmeter_api_key:
            raise UserError(
                "Please write API key in the billing settings")

        if not current_company.mgs_sparkmeter_api_secret:
            raise UserError(
                "Please write API secret in the billing settings")

        if not current_company.mgs_sparkmeter_service_area_id:
            raise UserError(
                "Please write Sevice Area ID for spark meter")


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    mgs_sparkmeter_api_link = fields.Char(
        string='API Link', related="company_id.mgs_sparkmeter_api_link", readonly=False)
    mgs_sparkmeter_api_key = fields.Char(
        string='API Key', related="company_id.mgs_sparkmeter_api_key", readonly=False)
    mgs_sparkmeter_api_secret = fields.Char(
        string='API Secret', related="company_id.mgs_sparkmeter_api_secret", readonly=False)
    mgs_meters_per_click = fields.Integer(
        string='Meters Per Click', related="company_id.mgs_meters_per_click", readonly=False)
    mgs_sparkmeter_service_area_id = fields.Char(
        string='Sevice Area ID', related="company_id.mgs_sparkmeter_service_area_id", readonly=False)
    mgs_sparkmeter_follower_ids = fields.Many2many('res.users',
        string='Spark Email Follower IDs',related="company_id.mgs_sparkmeter_follower_ids", readonly=False)
    mgs_sparkmeter_prb = fields.Integer(string='Pervent Readings Before(days)', 
                                        related="company_id.mgs_sparkmeter_prb", readonly=False)
