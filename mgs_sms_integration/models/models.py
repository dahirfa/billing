# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import datetime, date
import hashlib
import requests
import json


class MgsSms(models.Model):
    _name = 'mgs.sms'
    _description = 'mgs sms'
    _rec_name = 'source_name'
    _order = 'datetime DESC'

    _inherit = ['mail.thread', 'mail.activity.mixin']

    datetime = fields.Datetime()
    message = fields.Text()
    mobile = fields.Char()
    partner_id = fields.Many2one('res.partner')
    model_id = fields.Many2one('ir.model', string="Model")
    source_name = fields.Char()
    response = fields.Text()
    state = fields.Selection([('sent', 'Sent'), ('failed', 'Failed')])

    @api.model
    def create_mgs_sms(self, name, msg, to, partner, model):
        mgs_sms_obj = self.env['mgs.sms']
        sms_record = mgs_sms_obj.create({
            'source_name': name,
            'message': msg,
            'mobile': to,
            'partner_id': partner,
            'model_id': model,
            'datetime': datetime.now()})
        return sms_record

    @api.model
    def get_partner_balance(self, id):
        partner_balance = """
                            select COALESCE(sum(aml.debit - aml.credit), 0)
                            from account_move_line as aml
                            left join account_account as aa on aml.account_id=aa.id
                            where aml.partner_id = %s""" % str(id) + """
                            and aa.account_type = 'asset_receivable'
                            and parent_state in ('posted')"""
        self.env.cr.execute(partner_balance)
        auto_commit = self.env.context.get('auto_commit', True)
        self.env.cr
        contemp = self.env.cr.fetchone()
        if contemp is not None:
            result = contemp[0] or 0.0
        return result

    def action_send_sms(self):
        if self.env.company.sms_type == 'Telesom':
            self.telesom_sms()
        elif self.env.company.sms_type == 'Golis':
            self.golis_sms()

    def telesom_sms(self):
        if not self.mobile:
            self.message_post(body='This partner has no mobile number')
            return True
        config_params = self._get_mgs_sms_config_params()
        # print(config_params)

        username = config_params['username']
        passowrd = config_params['passowrd']
        sender = config_params['sender']
        private_key = config_params['private_key']
        current_date = config_params['current_date']

        msg = self.message
        to = self.mobile

        msg = msg.replace(" ", "%20")
        hashkey = username + "|" + passowrd + "|" + to + "|" + msg + \
            "|" + sender + "|" + current_date + "|" + private_key
        hashkey = hashlib.md5(hashkey.encode('utf-8')).hexdigest()
        hashkey = str(hashkey).upper()
        url = "https://sms.mytelesom.com/index.php/Gateway/sendsms/%s/%s/%s/%s" % (
            sender, msg, to, hashkey)

        response = requests.get(url)
        self.write({'response': response.text})
        response = json.loads(response.text)
        if response['status'] == "error":
            self.write({'state': 'failed'})
        if response['status'] != "error":
            self.write({'state': 'sent'})
        return "SMS STATUS : " + response['status']

    def golis_sms(self):
        if not self.mobile:
            self.message_post(body='This partner has no mobile number')
            return 'This partner has no mobile number'
        param_obj = self.env['ir.config_parameter']
        sender = self.env.company.mgs_golis_sender
        token = self.env.company.mgs_golis_token

        url = "https://easytechapp.com/api/v3/sms/send?type=plain&message=%s&sender_id=%s&recipient=%s" % (
            self.message, sender, self.mobile)
        payload = {}
        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer %s' % token,
            'Cookie': 'cookiesession1=678A8C55KMNOPQRSTUVWXYZABCDEF7C8'}
        try:
            response = requests.post(
                url, headers=headers, data=payload, timeout=10)
            response = json.loads(response.text)
            self.write({'response': response})

            if response['status'] != "success":
                self.write({'state': 'failed'})
                return 'failed to send sms'
            if response['status'] == "success":
                self.write({'state': 'sent'})
                return 'the sms was sent successfully'
        except Exception as e:
            self.message_post(body=e)
            return 'failed to send sms'

    def action_send_mgs_sms_golis(self):
        if not self.mobile:
            self.message_post(body='This partner has no mobile number')
            return 'This partner has no mobile number'
        # param_obj = self.env['ir.config_parameter']
        # sender = param_obj.sudo().get_param('mgs_sms_golis.sender')
        # token = param_obj.sudo().get_param('mgs_sms_golis.token')

        sender = self.env.company.mgs_golis_sender
        token = self.env.company.mgs_golis_token

        # sms_type = fields.Selection(
        # [('Telesom', 'Telesom'), ('Golis', 'Golis')], default='Telesom', string="SMS Type")

        # mgs_username = fields.Char(
        #     string='Telesom Username')
        # mgs_password = fields.Char(
        #     string='Telesom Password')
        # mgs_sender = fields.Char(string='Telesom Sender Name')
        # mgs_key = fields.Char(
        #     string='Telesom SMS Key')

        # mgs_golis_sender = fields.Char(
        #     string='Golis Sender Name')
        # mgs_golis_token = fields.Char(
        #     string='Golis Key')
        # mgs_golis_overwrite_odoo_sms = fields.Boolean(
        #     string='Golis Overwrite odoo sms', default=True)

        url = "https://easytechapp.com/api/v3/sms/send?type=plain&message=%s&sender_id=%s&recipient=%s" % (
            self.message, sender, self.mobile)
        payload = {}
        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer %s' % token,
            'Cookie': 'cookiesession1=678A8C55KMNOPQRSTUVWXYZABCDEF7C8'}
        try:
            response = requests.post(
                url, headers=headers, data=payload, timeout=10)
            response = json.loads(response.text)
            self.write({'response': response})

            if response['status'] != "success":
                self.write({'state': 'failed'})
                return 'failed to send sms'
            if response['status'] == "success":
                self.write({'state': 'sent'})
                return 'the sms was sent successfully'
        except Exception as e:
            self.message_post(body=e)
            return 'failed to send sms'

    @api.model
    def _get_mgs_sms_config_params(self):
        username = self.env.company.mgs_username
        passowrd = self.env.company.mgs_password
        sender = self.env.company.mgs_sender
        private_key = self.env.company.mgs_key
        current_date = datetime.strptime(
            str(date.today()), '%Y-%m-%d').strftime('%d/%m/%Y')
        return {'username': username, 'passowrd': passowrd, 'sender': sender, 'private_key': private_key, 'current_date': current_date}


class ResPartner(models.Model):
    _inherit = 'res.partner'

    mgs_send_sms = fields.Boolean(default=False, string='Send SMS')


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def button_resend_sms(self):
        if not self.partner_id.mobile:
            return True

        if self.env.company.sms_type == 'Telesom':
            self.sudo().send_mgs_sms()
        elif self.env.company.sms_type == 'Golis':
            self.sudo().send_mgs_sms_golis()

    def send_mgs_sms(self):
        mgs_sms_obj = self.env['mgs.sms']
        model_obj = self.env['ir.model'].sudo().search(
            [('model', '=', self._inherit)]).id
        for rec in self:
            if not rec.partner_id.mgs_send_sms:
                return True

            if rec.picking_type_id.code == 'outgoing':
                if not rec.partner_id.mobile:
                    rec.message_post(
                        body='This partner has no mobile number attached')
                products = ''
                if rec.move_ids_without_package:
                    for product in rec.move_ids_without_package:
                        products += ', %s - %s%s' % (
                            product.product_id.name, product.quantity_done, 'pcs')

                picking_no = rec.name.replace('/', ':')
                msg = 'DELIVERY: Waxaa laguu soo raray tixraac: %s : %s' % (
                    picking_no, products)
                to = rec.partner_id.mobile

                sms_record = mgs_sms_obj.create({'source_name': rec.name, 'message': msg, 'mobile': to,
                                                'partner_id': rec.partner_id.id, 'model_id': model_obj, 'datetime': datetime.now()})
                if sms_record:
                    try:
                        response = sms_record.action_send_sms()
                        rec.message_post(body=response)
                    except Exception as e:
                        sms_record.message_post(body=str(e))

    def send_mgs_sms_golis(self):
        mgs_sms_obj = self.env['mgs.sms']
        model_id = self.env['ir.model'].sudo().search(
            [('model', '=', self._inherit)]).id
        for rec in self:
            # if not rec.partner_id.mgs_send_sms:
            # return True

            if not rec.partner_id.mobile:
                rec.message_post(
                    body='This partner has no mobile number attached')
                return None
            msg = ''
            if rec.picking_type_code == 'outgoing':
                products = ''
                picking_no = rec.name
                if rec.move_ids_without_package:
                    for product in rec.move_ids_without_package:
                        products += ', %s - %s%s' % (
                            product.product_id.name, "{:,.2f}".format(product.quantity_done), 'pcs')
                msg += """DELIVERY: Waxaa laguu soo raray tixraac: %s : %s""" % (
                    picking_no, products)
                to = rec.partner_id.mobile
                sms_record = mgs_sms_obj.sudo().create_mgs_sms(
                    picking_no, msg, to, rec.partner_id.id, model_id)
                if sms_record:
                    try:
                        response = sms_record.action_send_mgs_sms_golis()
                        rec.message_post(body=response)
                    except Exception as e:
                        rec.message_post(body=str(e))

    def _action_done(self):
        res = super(StockPicking, self)._action_done()

        if not self.partner_id.mobile:
            return res

        if self.env.company.sms_type == 'Telesom':
            self.sudo().send_mgs_sms()
        elif self.env.company.sms_type == 'Golis':
            self.sudo().send_mgs_sms_golis()
        return res


class AccountMove(models.Model):
    _inherit = 'account.move'

    def button_resend_sms(self):
        if not self.partner_id.mobile:
            return True

        if self.env.company.sms_type == 'Telesom':
            self.sudo().send_sms()
        elif self.env.company.sms_type == 'Golis':
            self.sudo().send_sms_golis()

    def send_sms(self):
        mgs_sms_obj = self.env['mgs.sms']
        model_obj = self.env['ir.model'].sudo().search(
            [('model', '=', self._inherit)]).id
        for rec in self:
            # if not rec.partner_id.mgs_send_sms:
            # return True

            # if not rec.move_type != 'out_invoice':
            #     return True

            if rec.move_type == 'out_invoice' or rec.move_type == 'out_refund':
                if not rec.partner_id.mobile:
                    rec.message_post(
                        body='This partner has no mobile number attached')
                partner_balance = ''
                if rec.partner_id:
                    balance_query = mgs_sms_obj.get_partner_balance(
                        rec.partner_id.id)

                    # if rec.move_type == 'out_invoice':
                    partner_balance = "{:,.2f}".format(
                        balance_query + rec.amount_total_signed)
                    # elif rec.move_type == 'out_refund':
                    #     partner_balance = "{:,.2f}".format(balance_query)
                    amount_total = "{:,.2f}".format(rec.amount_total)

                invoice_number = rec.name.replace('/', '-')
                if rec.move_type == 'out_invoice':
                    msg = 'INVOICE: Waxaa xisaabtaada lagu dalacay iib dhan USD %s tixraac %s deyntaada cusubi waa USD %s' % (
                        amount_total, invoice_number, partner_balance)
                else:
                    msg = 'INVOICE: Waxaa xisaabtaada laga celiyay iib dhan USD %s tixraac %s deyntaada cusubi waa USD %s' % (
                        amount_total, invoice_number, partner_balance)

                to = rec.partner_id.mobile.replace(" ", "") or None
                sms_record = mgs_sms_obj.create({'source_name': rec.name, 'message': msg, 'mobile': to,
                                                'partner_id': rec.partner_id.id, 'model_id': model_obj, 'datetime': datetime.now()})
                if sms_record:
                    try:
                        response = sms_record.action_send_sms()
                        rec.message_post(body=response)
                    except Exception as e:
                        sms_record.message_post(body=str(e))
        # mgs_sms_obj = self.env['mgs.sms']
        # model_obj = self.env['ir.model'].sudo().search(
        #     [('model', '=', self._inherit)]).id
        # for rec in self:
        #     if rec.move_type == 'out_invoice':
        #         if not rec.partner_id.mobile:
        #             rec.message_post(
        #                 body='This partner has no mobile number attached')
        #         partner_balance = ''
        #         if rec.partner_id:
        #             # partner_balance += "{:,.2f}".format(mgs_sms_obj.get_partner_balance(
        #             #     rec.partner_id.id) + rec.amount_total_signed)
        #             partner_balance = mgs_sms_obj.get_partner_balance(
        #                 rec.partner_id.id) + rec.amount_total_signed

        #             partner_balance = str(partner_balance)
        #             amount_total = "{:,.2f}".format(rec.amount_total)

        #         invoice_number = rec.name.replace('/', '-')
        #         msg = 'INVOICE: Macamiil waxa xisaabtaada lagu dalacay iib dhan USD %s tixraac %s deyntaada cusbi waa USD %s' % (
        #             amount_total, invoice_number, partner_balance)
        #         to = rec.partner_id.mobile.replace(" ", "") or None
        #         sms_record = mgs_sms_obj.create({'source_name': rec.name, 'message': msg, 'mobile': to,
        #                                         'partner_id': rec.partner_id.id, 'model_id': model_obj, 'datetime': datetime.now()})
        #         if sms_record:
        #             try:
        #                 response = sms_record.action_send_sms()
        #                 rec.message_post(body=response)
        #             except Exception as e:
        #                 sms_record.message_post(body=str(e))

    def send_sms_golis(self):
        mgs_sms_obj = self.env['mgs.sms']
        model_id = self.env['ir.model'].sudo().search(
            [('model', '=', self._inherit)]).id
        for rec in self:
            # if not rec.partner_id.mgs_send_sms:
            # return True

            if not rec.partner_id.mobile:
                rec.message_post(
                    body='This partner has no mobile number attached')
                return None

            if rec.move_type != 'out_invoice' or rec.move_type != 'out_refund':
                return True

            invoice_no = rec.name
            amount_total = rec.currency_id.symbol + str("{:,.2f}".format(rec.amount_total)) if rec.currency_id.symbol == '$' else str(
                "{:,.2f}".format(rec.amount_total)) + rec.currency_id.symbol
            # balance = rec.partner_id.credit
            balance_query = mgs_sms_obj.get_partner_balance(rec.partner_id.id)

            if rec.move_type == 'out_invoice':
                balance = "{:,.2f}".format(
                    balance_query + rec.amount_total_signed)
            elif rec.move_type == 'out_refund':
                balance = "{:,.2f}".format(
                    balance_query - rec.amount_total_signed)
            # balance = rec.currency_id.symbol + \
            #     str("{:,.2f}".format(balance)) if rec.currency_id.symbol == '$' else str(
            #         "{:,.2f}".format(balance)) + rec.currency_id.symbol

            msg = ''
            if rec.move_type == 'out_invoice':
                msg += """INVOICE: Waxaa xisaabtaada lagu dalacay iib dhan USD %s  tixraac: %s deyntaada cusubi waa USD %s""" % (
                    amount_total, invoice_no, balance)

            if rec.move_type == 'out_refund':
                msg += """CREDIT NOTE: Waxaa xisaabtaada laga celiyay iib dhan USD %s tixraac: %s deyntaada cusubi waa USD %s""" % (
                    amount_total, invoice_no, balance)
            to = rec.partner_id.mobile

            sms_record = mgs_sms_obj.sudo().create_mgs_sms(
                invoice_no, msg, to, rec.partner_id.id, model_id)
            if sms_record:
                try:
                    response = sms_record.action_send_mgs_sms_golis()
                    rec.message_post(body=response)
                except Exception as e:
                    rec.message_post(body=str(e))

    def action_post(self):
        res = super(AccountMove, self).action_post()

        if not self.partner_id.mobile:
            return res

        if self.env.company.sms_type == 'Telesom':
            self.sudo().send_sms()
        elif self.env.company.sms_type == 'Golis':
            self.sudo().send_sms_golis()
        return res


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    def button_resend_sms(self):
        if not self.partner_id.mobile:
            return True

        if self.env.company.sms_type == 'Telesom':
            self.sudo().send_sms()
        elif self.env.company.sms_type == 'Golis':
            self.sudo().send_sms_golis()

    def send_sms(self):
        mgs_sms_obj = self.env['mgs.sms']
        model_obj = self.env['ir.model'].sudo().search(
            [('model', '=', self._inherit)]).id
        for rec in self:
            if not rec.partner_id.mgs_send_sms:
                return True

            if rec.payment_type == 'inbound':
                if not rec.partner_id.mobile:
                    rec.message_post(
                        body='This partner has no mobile number attached')
                partner_balance = ''
                if rec.partner_id:
                    partner_balance += "{:,.2f}".format(
                        mgs_sms_obj.get_partner_balance(rec.partner_id.id) - rec.amount)
                    partner_balance = str(partner_balance)
                payment_number = ''
                if rec.name:
                    payment_number = rec.name.replace('.', '-')
                    payment_number = rec.name.replace('/', '-')

                msg = 'PAYMENT: Waxaad soo bixisay lacag dhan USD %s tixraac %s deynta kugu hadhay hadda waa USD %s' % (
                    rec.amount, payment_number, partner_balance)
                to = rec.partner_id.mobile.replace(" ", "") or None
                sms_record = mgs_sms_obj.create({'source_name': rec.name, 'message': msg, 'mobile': to,
                                                'partner_id': rec.partner_id.id, 'model_id': model_obj, 'datetime': datetime.now()})
                if sms_record:
                    try:
                        response = sms_record.action_send_sms()
                        rec.message_post(body=response)
                    except Exception as e:
                        sms_record.message_post(body=str(e))

    def send_sms_golis(self):
        mgs_sms_obj = self.env['mgs.sms']
        model_id = self.env['ir.model'].sudo().search(
            [('model', '=', self._inherit)]).id
        for rec in self:
            # if not rec.partner_id.mgs_send_sms:
            # return True

            if not rec.partner_id.mobile:
                rec.message_post(
                    body='This partner has no mobile number attached')
                return None
            payment_no = rec.name
            amount = rec.currency_id.symbol + str("{:,.2f}".format(rec.amount)) if rec.currency_id.symbol == '$' else str(
                "{:,.2f}".format(rec.amount)) + rec.currency_id.symbol
            balance = "{:,.2f}".format(
                mgs_sms_obj.get_partner_balance(rec.partner_id.id) - rec.amount)
            # partner_balance = str(partner_balance)
            # balance = rec.currency_id.symbol + \
            #     str("{:,.2f}".format(balance)) if rec.currency_id.symbol == '$' else str(
            #         "{:,.2f}".format(balance)) + rec.currency_id.symbol

            payment_type = 'Waxaa soo bixisay' if rec.payment_type == 'inbound' else 'Waxaad qaadatay'

            msg = """Payment: %s Waxaad soo bixisay lacag dhan USD %s tixraac: %s deynta kugu hartay hadda waa USD %s""" % (
                payment_type, amount, payment_no, balance)
            to = rec.partner_id.mobile

            sms_record = mgs_sms_obj.sudo().create_mgs_sms(
                payment_no, msg, to, rec.partner_id.id, model_id)
            if sms_record:
                try:
                    response = sms_record.action_send_mgs_sms_golis()
                    rec.message_post(body=response)
                except Exception as e:
                    rec.message_post(body=str(e))

    def action_post(self):
        res = super(AccountPayment, self).action_post()

        if not self.partner_id.mobile:
            return res

        if self.env.company.sms_type == 'Telesom':
            self.sudo().send_sms()
        elif self.env.company.sms_type == 'Golis':
            self.sudo().send_sms_golis()
        return res


class ResCompany(models.Model):
    _inherit = 'res.company'

    sms_type = fields.Selection(
        [('Telesom', 'Telesom'), ('Golis', 'Golis')], default='Telesom', string="SMS Type")

    mgs_username = fields.Char(
        string='Telesom Username')
    mgs_password = fields.Char(
        string='Telesom Password')
    mgs_sender = fields.Char(string='Telesom Sender Name')
    mgs_key = fields.Char(
        string='Telesom SMS Key')

    mgs_golis_sender = fields.Char(
        string='Golis Sender Name')
    mgs_golis_token = fields.Char(
        string='Golis Key')
    mgs_golis_overwrite_odoo_sms = fields.Boolean(
        string='Golis Overwrite odoo sms', default=True)


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    sms_type = fields.Selection(
        [('Telesom', 'Telesom'), ('Golis', 'Golis')], related='company_id.sms_type', readonly=False, string="SMS Type")

    # ------------------------------------------- Telesom -------------------------------------------
    mgs_username = fields.Char(
        string='Telesom Username', related="company_id.mgs_username", readonly=False)
    mgs_password = fields.Char(
        string='Telesom Password', related="company_id.mgs_password", readonly=False)
    mgs_sender = fields.Char(
        string='Telesom Sender Name', related="company_id.mgs_sender", readonly=False)
    mgs_key = fields.Char(
        string='Telesom Key', related="company_id.mgs_key", readonly=False)

    # -------------------------------------------  Golis  -------------------------------------------
    mgs_golis_sender = fields.Char(
        string='Golis Sender Name', related="company_id.mgs_golis_sender", readonly=False)
    mgs_golis_token = fields.Char(
        string='Golis Key', related="company_id.mgs_golis_token", readonly=False)
    mgs_golis_overwrite_odoo_sms = fields.Boolean(
        string='Golis Overwrite odoo sms', default=True, related="company_id.mgs_golis_overwrite_odoo_sms", readonly=False)

    # @api.model
    # def set_values(self):
    #     res = super(ResConfigSettings, self).set_values()
    #     self.env['ir.config_parameter'].sudo().set_param(
    #         'mgs_sms_integration.username', self.mgs_username)
    #     self.env['ir.config_parameter'].sudo().set_param(
    #         'mgs_sms_integration.password', self.mgs_password)
    #     self.env['ir.config_parameter'].sudo().set_param(
    #         'mgs_sms_integration.sender', self.mgs_sender)
    #     self.env['ir.config_parameter'].sudo().set_param(
    #         'mgs_sms_integration.key', self.mgs_key)
