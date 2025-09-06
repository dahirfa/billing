from odoo import models, fields, api
import requests
import json

# """THIS IS DEPRICATED"""
# """THIS IS DEPRICATED"""
# """THIS IS DEPRICATED"""
# """THIS IS DEPRICATED"""
# """THIS IS DEPRICATED"""
# """THIS IS DEPRICATED"""
# """THIS IS DEPRICATED"""
# """THIS IS DEPRICATED"""
# """THIS IS DEPRICATED"""
# """THIS IS DEPRICATED"""
# """THIS IS DEPRICATED"""
# """THIS IS DEPRICATED"""
# """THIS IS DEPRICATED"""
# """THIS IS DEPRICATED"""
# """THIS IS DEPRICATED"""
# """THIS IS DEPRICATED"""
# """THIS IS DEPRICATED"""
# """THIS IS DEPRICATED"""
# """THIS IS DEPRICATED"""
# """THIS IS DEPRICATED"""
# """THIS IS DEPRICATED"""
# """THIS IS DEPRICATED"""
# """THIS IS DEPRICATED"""
# """THIS IS DEPRICATED"""
# """THIS IS DEPRICATED"""
# """THIS IS DEPRICATED"""

class MgsSparkmeterSite(models.Model):
    _name = 'mgs_sparkmeter.site'
    _description = 'SparkMeter Site'

    name = fields.Char(string='Spark Meter Site Name', required=True)
    sparkmeter_site_id = fields.Char(string='Spark Meter SiteID')
    site_type = fields.Char(string='Type')

    def action_get_sparkmeter_sites(self, organization_id):
        current_company = self.env.company
        current_company.check_sparkmeter_credentials()
        url = '%s/organizations/%s/sites' % (
            current_company.mgs_sparkmeter_api_link.replace('/v1', '/v0'), organization_id)
        headers = {
            "Content-Type": "application/json",
            "X-API-KEY": current_company.mgs_sparkmeter_api_key,
            "X-API-SECRET": current_company.mgs_sparkmeter_api_secret
        }
        payload = {}
        response = requests.get(url, headers=headers, json=payload)
        response_dict = json.loads(response.text)
        result='Invalid'
        if response_dict['sites'] and len(response_dict['sites']) > 0:
            result = response_dict['sites']
        return result

class MgsSparkmeterSiteCreateWiz(models.TransientModel):
    _name = 'mgs_sparkmeter.create.site.wizard'
    _description = 'Create Sparkmeter Site Wizard'

    def action_confirm(self):
        site_obj = self.env['mgs_sparkmeter.site']

        for site in self.env['mgs_sparkmeter.site'].action_get_sparkmeter_sites(self.env.company.mgs_sparkmeter_service_area_id):
            if site_obj.search([('sparkmeter_site_id', '=', site['id'])]):
                continue

            site_obj.create({
                'name': site['name'],
                'sparkmeter_site_id': site['id'],
                'site_type': site['type']
            })
            