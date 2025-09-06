from odoo import _, api, fields, models

import logging
_logger = logging.getLogger(__name__)



class MGSPaymentIntegrationInherit(models.Model):
    _inherit = 'mgs.payment.transaction'
    # This field determines whether account.paymnet's partner_type is Supplier or Customer
    
    prepaid_electricity = fields.Boolean(string="Prepaid Electricity", default = False)
    
    def _prepare_payment_vals(self, payment_method_line_id, partner_id):
        action =  super(MGSPaymentIntegrationInherit, self)._prepare_payment_vals(payment_method_line_id, partner_id)
        action['partner_type'] = "supplier" if  self.prepaid_electricity else "customer"
        action['prepaid_electricity'] = True if partner_id.property_id.payment_type == "pre_paid" and self.prepaid_electricity else False
        return action
        
    def get_partner_balance(self, property_id):
        partner_id = self.env['res.partner'].search([('property_id.id', '=', property_id)], limit=1).id
        partner_balance = """
                            select COALESCE(sum(aml.debit - aml.credit), 0)
                            from account_move_line as aml
                            left join account_account as aa on aml.account_id=aa.id
                            where aml.partner_id = %s""" % str(partner_id) + """
                            and aa.account_type = 'asset_receivable'
                            and parent_state in ('posted')"""
        self.env.cr.execute(partner_balance)
        contemp = self.env.cr.fetchone()
        if contemp is not None:
            result = contemp[0] or 0.0
        return result
  
    @api.model_create_multi
    def create(self, values):
        partner_obj = self.env['res.partner']
        for record in values:
                partner = partner_obj.browse(record['partner_id'])
                if partner and partner.property_id and partner.property_id.payment_type == "pre_paid":
                    
                    
                    vat_partner_id = self.env.company.mgs_vat_tax_partner_id
                    amount = record['amount']
                    vat_percentage = 2
                    balance = self.get_partner_balance(partner.property_id.id)
                    payment_lines = []

                    if balance > 0:
                        
                        if amount > balance:
                            record.update({'breakdown': True})
                            balance_payment = balance
                            prepaid_payment = amount - balance_payment
                            vat_tax = prepaid_payment * vat_percentage / 100
                            prepaid_payment_after_vat = prepaid_payment - vat_tax
                            # Balance Payment
                            payment_lines.append((0, 0, {
                                "partner_id": partner.id,
                                "amount": balance_payment,
                            }))
                            
                            # Prepaid Payment
                            payment_lines.append((0, 0, {
                                "partner_id": partner.id,
                                "prepaid_electricity": True,
                                "amount": prepaid_payment_after_vat,
                            }))
                            record.update({'prepaid_electricity': True})
                            
                            
                            
                            # VAT TAX
                            payment_lines.append((0, 0, {
                                "partner_id": vat_partner_id.id,
                                "prepaid_electricity": True,
                                "amount": vat_tax,
                            }))
                    else:
                        record.update({'breakdown': True})
                        vat_tax = amount * vat_percentage / 100
                        prepaid_payment = amount - vat_tax
                        
                        # Prepaid Payment
                        payment_lines.append((0, 0, {
                            "partner_id": partner.id,
                            "prepaid_electricity": True,
                            "amount": prepaid_payment,
                        }))
                        record.update({'prepaid_electricity': True})
                        
                        
                        # VAT TAX
                        payment_lines.append((0, 0, {
                            "partner_id": vat_partner_id.id,
                            "prepaid_electricity": True,
                            "amount": vat_tax,
                        }))

                    record.update({"line_ids": payment_lines})

        action = super(MGSPaymentIntegrationInherit, self).create(values)
        return action
            
    
    
    

    

class MGSPaymentLineInherit(models.Model):
    _inherit = 'mgs.payment.line'
    
    # This field determines whether account.paymnet's partner_type is Supplier or Customer
    prepaid_electricity = fields.Boolean(string="Prepaid Electricity", default = False)
    
    
    def _prepare_payment(self, journal_id, ref, sender, date):
        action = super(MGSPaymentLineInherit, self)._prepare_payment(journal_id, ref, sender, date)
        action['partner_type'] = "supplier" if  self.prepaid_electricity else  "customer"
        action['prepaid_electricity'] = True if self.partner_id.property_id.payment_type == "pre_paid" and self.prepaid_electricity else False
        return action
        



class MGSSahalImporting(models.Model):
    _inherit = "mgs.golis.sahal.payment"
    
    # This field determines whether account.paymnet's partner_type is Supplier or Customer
    prepaid_electricity = fields.Boolean(string="Prepaid Electricity", default = False)
    
    
    def _prepare_payment_vals(self, journal_id, partner_id):
        action = super(MGSSahalImporting, self)._prepare_payment_vals(journal_id, partner_id)
        
        action["partner_type"] = "supplier" if self.prepaid_electricity else  "customer"
        action['prepaid_electricity'] = True if partner_id.property_id.payment_type == "pre_paid" and self.prepaid_electricity else False
        
        
        return action
        