from odoo import models, fields, api
from datetime import datetime, date


class ResCompany(models.Model):
    _inherit = 'res.company'

    sms_type = fields.Selection(selection_add=[(
        'Utility Golis', "Utility Golis")])


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    sms_type = fields.Selection(selection_add=[(
        'Utility Golis', "Utility Golis")])


class MgsSms(models.Model):
    _inherit = 'mgs.sms'

    def action_send_sms(self):
        if self.env.company.sms_type == 'Telesom':
            self.telesom_sms()
        elif self.env.company.sms_type == 'Golis':
            self.golis_sms()
        elif self.env.company.sms_type == 'Utility Golis':
            self.golis_sms()
        # elif self.env.company.sms_type == 'Utility Golis' and self.reading_id:
            # self.send_utility_sms()


class AccountMove(models.Model):
    _inherit = 'account.move'

    def send_utility_sms(self):
        mgs_sms_obj = self.env['mgs.sms']
        model_obj = self.env['ir.model'].sudo().search(
            [('model', '=', self._inherit)]).id
        for rec in self:
            partner_id = rec.reading_id.billing_account_id
            mobile = partner_id.mobile

            if '+' in mobile:
                mobile = mobile.replace('+', '')

            if partner_id:
                balance_query = mgs_sms_obj.get_partner_balance(
                    rec.partner_id.id)

                # if rec.move_type == 'out_invoice':
                partner_balance = "{:,.2f}".format(
                    balance_query)
                # elif rec.move_type == 'out_refund':
                #     partner_balance = "{:,.2f}".format(balance_query)
                amount_total = "{:,.2f}".format(rec.amount_total)

                prev_bal = "{:,.2f}".format(self.get_mgs_partner_prev_balance(
                    partner_id.id, rec.invoice_date)) or 0.0

            if not mobile:
                rec.message_post(
                    body='This partner has no mobile number attached')
                continue
            # partner_balance = str(partner_id.credit)
            # msg = '''Meter No: %s Biilka %s, Waa Akhr.Hore:%s Akhr.Danbe:%s Farqi:%s Lacagta: USD %s Deyntaada cusubi waa USD: %s''' % (
            #     rec.reading_id.property_id.name, rec.invoice_date.strftime("%B"), rec.reading_id.last_reading, rec.reading_id.current_reading, rec.reading_id.difference, amount_total, partner_balance)
            msg = """Macmiil: %s Biilka %s Saacad lanbar: %s Akhr. Hore: %s Akhr. Danbe: %s Farqi: %s Lacagta: USD %s iyo haraa hore USD: %s Haraagaga cusubi waa USD: %s""" % (rec.partner_id.name, rec.invoice_date.strftime(
                "%B"), rec.reading_id.property_id.name, round(rec.reading_id.last_reading, 2), round(rec.reading_id.current_reading, 2), round(rec.reading_id.difference, 2), amount_total, prev_bal, partner_balance)
            to = mobile
            sms_record = mgs_sms_obj.create({'source_name': rec.name, 'message': msg, 'mobile': to,
                                            'partner_id': partner_id.id, 'model_id': model_obj, 'datetime': datetime.now()})
            if sms_record:
                try:
                    response = sms_record.action_send_mgs_sms_golis()
                    rec.message_post(body=response)
                except Exception as e:
                    sms_record.message_post(body=str(e))

    def button_resend_sms(self):
        if not self.partner_id.mobile:
            return True

        if self.env.company.sms_type == 'Telesom':
            self.sudo().send_sms()
        elif self.env.company.sms_type == 'Golis':
            self.sudo().send_sms_golis()
        elif self.env.company.sms_type == 'Utility Golis':
            self.sudo().send_utility_sms()

    def action_post(self):
        res = super(AccountMove, self).action_post()

        if not self.partner_id.mobile:
            return res

        if self.env.company.sms_type == 'Telesom':
            self.sudo().send_sms()
        elif self.env.company.sms_type == 'Golis':
            self.sudo().send_sms_golis()
        elif self.env.company.sms_type == 'Utility Golis' and not self.reading_id:
            # FIXME
            # self.sudo().send_sms_golis()
            return res
        elif self.env.company.sms_type == 'Utility Golis' and self.reading_id:
            self.sudo().send_utility_sms()
        return res
