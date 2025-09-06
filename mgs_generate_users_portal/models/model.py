from odoo import _, api, fields, models
import logging
_logger = logging.getLogger(__name__)
from odoo.exceptions import UserError, ValidationError
class InheritPartner(models.Model):
    _inherit = 'res.partner'
    
    def _clean_phone_number(self):
        for record in self:
            if record.phone:
                # Step 1: Remove '+' and spaces if present
                phone_number = record.phone.replace("+", "").replace(" ", "")
                
                # Step 2: Determine the country_id (use the company's country if not specified)
                country = record.country_id or self.env.company.country_id
                
                if country and country.phone_code:
                    # Step 3: Remove the country calling code if present
                    phone_code = str(country.phone_code)
                    if phone_number.startswith(phone_code):
                        phone_number = phone_number[len(phone_code):]
                
                # Step 4: Validate the length of the remaining number
                # if len(phone_number) != 9:
                #     raise ValidationError(
                #         "The phone number must have exactly 9 digits after the country code, excluding spaces."
                #     )
                
                # Step 5: Return the cleaned phone number
                return phone_number

    
    def generate_users_portal(self):
        group_portal = self.env.ref('base.group_portal')
        for r in self:
            # Check if a user with the same login (email) already exists
            existing_user = self.env['res.users'].sudo().search([('login', '=', r.email)])
            
            # Extract digits from the name for the login
            login = ''.join([char for char in r.name if char.isdigit()])
            
            # Skip creation if login is empty
            if not login:
                continue
            
            # phone_number = r._clean_phone_number()
            
            if not existing_user and r.phone:
                user_info = {
                    'name': r.name,
                    'login': login,
                    'partner_id': r.id,
                    'password': phone_number[-4:],  # Use the last 4 digits of the phone number as password
                    'groups_id': [(4, group_portal.id)],
                }
                user = self.env['res.users'].sudo().with_context(no_reset_password=True).create(user_info)
            else:
                raise ValidationError(f"Make sure the selected customers have a valid phone number")

 

    
