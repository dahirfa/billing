
from odoo import models, fields
import requests
import json
from odoo.exceptions import UserError


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    property_sparkmeter_tariff_id = fields.Char(string='Tariff', company_dependent=True)

    def action_create_sparkmeter_tariff(self):
        for r in self:
            if not r.is_billing_pan:
                return None

            self.env.company.check_sparkmeter_credentials()

            name = r.name
            price = r.list_price
            current_company = self.env.company

            # API endpoint and headers
            url = '%s/tariffs' % current_company.mgs_sparkmeter_api_link
            headers = {
                "Content-Type": "application/json",
                "X-API-KEY": current_company.mgs_sparkmeter_api_key,
                "X-API-SECRET": current_company.mgs_sparkmeter_api_secret
            }

            # Request body
            payload = {
                "name": name,
                "electricity_rate": str(price),
                "load_limit": {
                    "type": "flat",
                    "value": 10000
                },
                "low_balance_threshold": 5,
                "inrush_current_protection_disabled": False
            }

            # Make POST request
            response = requests.post(url, headers=headers, json=payload)
            response_dict = json.loads(response.text)
            # Print status code to Odoo chatter
            if response.status_code == 201:
                self.message_post(
                    body="Record created successfully. Status code: " + str(response.status_code))
                r.property_sparkmeter_tariff_id = response_dict['data']['id']
            elif response.status_code == 400:
                self.message_post(
                    body="""Failed to create record. Status code: """ +
                    str(response.status_code)
                    + """ Msg: """ + response_dict['errors'][0]['details']
                )

    
    def write(self, values):
        for r in self:
            r.action_update_sparkmeter_tariff()
        result = super(ProductTemplate, self).write(values)
        return result
    

    def action_update_sparkmeter_tariff(self):
        for r in self:
            if not r.is_billing_pan:
                return None

            if not r.property_sparkmeter_tariff_id:
                return None

            self.env.company.check_sparkmeter_credentials()

            current_company = self.env.company

            # API endpoint and headers
            url = '%s/tariffs/%s' % (current_company.mgs_sparkmeter_api_link, r.property_sparkmeter_tariff_id)
            headers = {
                "Content-Type": "application/json",
                "X-API-KEY": current_company.mgs_sparkmeter_api_key,
                "X-API-SECRET": current_company.mgs_sparkmeter_api_secret
            }

            # Request body
            payload = [
                {
                    "op": "replace",
                    "path": "/name",
                    "value": r.name
                },
                {
                    "op": "replace",
                    "path": "/electricity_rate",
                    "value": str(r.list_price)
                }
            ]

            # Make POST request
            response = requests.patch(url, headers=headers, json=payload)
            response_dict = json.loads(response.text)
            # Print status code to Odoo chatter
            if response.status_code == 200:
                self.message_post(
                    body="Record update successfully. Status code: " + str(response.status_code))
                # r.property_sparkmeter_tariff_id = response_dict['data']['id']
            elif response.status_code == 400:
                self.message_post(
                    body="""Failed to update record. Status code: """ +
                    str(response.status_code)
                    + """ Msg: """ + response_dict['errors'][0]['details']
                )