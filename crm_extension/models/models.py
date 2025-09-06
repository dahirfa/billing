# -*- coding: utf-8 -*-

from odoo import models, fields, api


# class CRMLeads(models.Model):
#     _inherit = 'crm.lead'

# @api.model
# def name_get(self):
#     result = []
#     for record in self:
#         if record.partner_id and record.partner_id.mobile:
#             name = str(record.name) + ' - ' + \
#                 record.partner_id.mobile + ' - ' + record.partner_id.name
#         elif record.partner_id and not record.partner_id.mobile:
#             name = str(record.name) + ' - ' + record.partner_id.name
#         else:
#             name = record.name
#         result.append((record.id, name))
#     return result

# @api.model
# def name_search(self, name, args=None, operator='ilike', limit=100):
#     args = args or []
#     recs = self.browse()
#     if name:
#         recs = self.search((args + ['|', '|', ('name', 'ilike', name), ('partner_id.mobile', 'ilike', name), ('partner_id.name', 'ilike', name)]),
#                            limit=limit)
#     if not recs:
#         recs = self.search([('name', operator, name)] + args, limit=limit)
#     return recs.name_get()

# class SaleOrder(models.Model):
#     _inherit = 'sale.order'

#     cust_contact_name = fields.Char(string = 'Contact Name')
#     cust_mobile = fields.Char(string = 'Mobile')
#     cust_area = fields.Char(string = 'Area')
#     cust_distance = fields.Float(string = 'Distance')
#     surveyor = fields.Char(string = 'Surveyor')

#     def _prepare_invoice(self):
#         invoice_vals = {
#             'ref': self.client_order_ref or '',
#             'type': 'out_invoice',
#             'narration': self.note,
#             'currency_id': self.pricelist_id.currency_id.id,
#             'campaign_id': self.campaign_id.id,
#             'medium_id': self.medium_id.id,
#             'source_id': self.source_id.id,
#             'invoice_user_id': self.user_id and self.user_id.id,
#             'team_id': self.team_id.id,
#             'partner_id': self.partner_invoice_id.id,
#             'partner_shipping_id': self.partner_shipping_id.id,
#             'invoice_partner_bank_id': self.company_id.partner_id.bank_ids[:1].id,
#             'fiscal_position_id': self.fiscal_position_id.id or self.partner_invoice_id.property_account_position_id.id,
#             'invoice_origin': self.name,
#             'invoice_payment_term_id': self.payment_term_id.id,
#             'invoice_payment_ref': self.reference,
#             'transaction_ids': [(6, 0, self.transaction_ids.ids)],
#             'invoice_line_ids': [],
#         }

#         invoice_vals['cust_contact_name'] = self.cust_contact_name
#         invoice_vals['cust_mobile'] = self.cust_mobile
#         invoice_vals['cust_area'] = self.cust_area
#         invoice_vals['cust_distance'] = self.cust_distance
#         invoice_vals['surveyor'] = self.surveyor

#         return invoice_vals

#     @api.onchange('cust_contact_name', 'cust_mobile', 'cust_area', 'cust_distance', 'surveyor')
#     def _onchange_cust_fields(self):
#         for r in self:
#             text = ""
#             if r.cust_contact_name:
#                 text += r.cust_contact_name + " | "

#             if r.cust_mobile:
#                 text += r.cust_mobile + " | "

#             if r.cust_area:
#                 text += r.cust_area + " | "

#             if r.cust_distance:
#                 text += str(r.cust_distance) + " | "

#             if r.surveyor:
#                 text += r.surveyor

#             r.client_order_ref = text

# class AccountMove(models.Model):
#     _inherit = 'account.move'

#     cust_contact_name = fields.Char(string = 'Contact Name')
#     cust_mobile = fields.Char(string = 'Mobile')
#     cust_area = fields.Char(string = 'Area')
#     cust_distance = fields.Float(string = 'Distance')
#     surveyor = fields.Char(string = 'Surveyor:')
