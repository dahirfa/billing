
from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
import logging
_logger = logging.getLogger(__name__)


# from statistics import mean
# from odoo.exceptions import UserError


class MGSBillingPropertyConHistory(models.Model):
    _name = 'mgs_billing.property.connection.log'
    _description = 'Connection History'
    _order = "time DESC"

    property_id = fields.Many2one('mgs_billing.property')
    time = fields.Datetime(default=fields.Datetime().now())
    memo = fields.Text(string='Comment')
    state = fields.Selection(
        [('connected', 'Connected'), ('disconnected', 'disconnected'),
         ('suspend', 'Suspended')])


class MGSBillingPropertyType(models.Model):
    _name = 'mgs_billing.property.type'
    _description = 'MGS Billing Document Type'
    # _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = "id DESC"

    name = fields.Char('Name', required=True)
    pricelist_id = fields.Many2one(
        'product.pricelist', string='Pricelist', required=True)
    property_ids = fields.One2many(
        'mgs_billing.property', 'property_type_id', string='Properties')
    counter = fields.Integer(
        string='Properties', compute='_count_properties')
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(
        'res.company', string='Company', default=lambda self: self.env.company.id)

    max_above_avg = fields.Float(string='Max Above Average')
    max_under_avg = fields.Float(string='Max Under Average')

    custom_average = fields.Boolean(
        default=False, string='Use Custom Average')
    if_its_less_than = fields.Float(string="If it's less than")
    make_rate = fields.Float(string='Make Amount')

    @api.depends('property_ids')
    def _count_properties(self):
        for r in self:
            r.counter = len(r.property_ids.ids)

    def action_open_properties(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Properties',
            'view_mode': 'list,form',
            'res_model': 'mgs_billing.property',
            'domain': [('property_type_id', '=', self.id)],
            'context': "{'create': False}"}

    def unlink(self):
        property_ids = self.env['mgs_billing.property'].search(
            [('property_type_id', '=', self.id)])

        if len(property_ids) > 0:
            raise UserError(
                "You cannot delete property type which has related properties.")
        return super(MGSBillingPropertyType, self).unlink()


class MGSBillingProperty(models.Model):
    _name = 'mgs_billing.property'
    _description = 'Billing Property'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = "id DESC"

    name = fields.Char(string='House #', default='/', tracking=True)
    property_type_id = fields.Many2one(
        'mgs_billing.property.type', string='Property Type', ondelete='restrict', tracking=True)
    zone_id = fields.Many2one('mgs_billing.zone', string='Zone',
                              ondelete='restrict', required=True, tracking=True)
    company_id = fields.Many2one(
        'res.company', string='Company', default=lambda self: self.env.company.id)
    city = fields.Char(tracking=True)
    street = fields.Char(tracking=True)
    street2 = fields.Char(tracking=True)
    zip = fields.Char()
    country_id = fields.Many2one(
        'res.country', string='Country', ondelete='restrict', tracking=True)
    state_id = fields.Many2one(
        'res.country.state', string='Country', ondelete='restrict')
    pricelist_id = fields.Many2one(
        'product.pricelist', string='Pricelist', compute='get_pricelist', store=True, readonly=False)
    owner_id = fields.Many2one('mgs_billing.partner', domain=[
                               ('type', '=', 'owner')], tracking=True, required=True)
    product_id = fields.Many2one('product.product', string="Plan", domain=[
                                 ('is_billing_pan', '=', True)], required=True)
    reading_history_counter = fields.Integer(
        string='Reading History', compute='get_reading_history')
    meter_reading_ids = fields.One2many(
        'mgs_billing.meter.reading', 'property_id')
    connection_log_ids = fields.One2many(
        'mgs_billing.property.connection.log', 'property_id')
    connection_log_count = fields.Integer(
        'Log Count', default=0, compute='_compute_connection_log_count', store=True)
    meter_id = fields.Many2one('mgs_billing.meter', ondelete='restrict')
    initial_meter = fields.Float(string='Initial Meter Read', tracking=True)
    reader_ref = fields.Char()
    
    meter_type = fields.Selection(
        [('normal', 'Normal'), ('smart', 'Smart')], default='normal',required=True)
    
    state = fields.Selection(
        [('connected', 'Connected'), ('disconnected', 'Disconnected'),
         ('suspend', 'Suspended')], default='connected')
    suspended = fields.Boolean(default=False, tracking=True)
    suspension_date = fields.Date(tracking=True)
    connection_date = fields.Datetime(string='Connection Date')
    
    def action_unsuspend(self):
        for r in self:
            r.suspended = False
            self.action_change_state('connected')

    # average_usage = fields.Float(
    #     'Average Usage', compute='_compute_average_usage')

    # @api.depends('meter_reading_ids', 'meter_reading_ids.reading_difference')
    # def _compute_average_usage(self):
    #     for r in self:
    #         meter_reading_ids = r.meter_reading_ids.filtered(
    #             lambda r: r.state == 'posted')
    #         r.average_usage = mean(
    #             meter_reading_ids.mapped('reading_difference'))

    @api.depends('connection_log_ids')
    def _compute_connection_log_count(self):
        for r in self:
            r.connection_log_count = len(r.connection_log_ids)

    def action_change_state(self, state='', memo=''):
        log_obj = self.env['mgs_billing.property.connection.log']
        state = state
        for r in self.filtered(lambda x: x.state != state):
            r.state = state
            log_obj.create(
                {'property_id': r.id, 'state': state, 'memo': memo, })

    def action_connected(self):
        self.action_change_state('connected')

    def action_disconnected(self, wizard=False):
        if wizard != True:
            self.action_change_state('disconnected')

    def action_open_conncection_log(self):
        action = self.env.ref(
            'mgs_billing.mgs_billing_connection_log_action').sudo().read()[0]
        action['domain'] = [('property_id', '=', self.id)]
        action['context'] = {}
        action['context']['create'] = False
        return action

    # @api.model
    def write(self, vals):
        if vals.get('zone_id'):                     
            if not self.env.company.mgs_billing_global_seq:
                if vals.get('name') and vals.get('name') != "/":         
                    pass           
                else:
                    vals['name'] = self.env['ir.sequence'].next_by_code(
                        self.env['mgs_billing.zone'].search([('id', '=', vals.get('zone_id'))]).code) or '/'
                    
            # else:
            #     mgs_billing_global_seq_id = self.env.company.mgs_billing_global_seq_id
            #     if not mgs_billing_global_seq_id:
            #         raise UserError(
            #             "Please select default global sequence in the billing settings")
            #     vals['name'] = self.env['ir.sequence'].next_by_code(
            #         mgs_billing_global_seq_id.code) or '/'

        if vals.get('owner_id'):
            partner = self.env['res.partner'].search([('is_tenancy', '=', True), ('property_id.id', '=', self.id)], limit=1)
            partner.customer_id = vals.get('owner_id')
            partner._compute_billing_name()
            partner._onchange_billing_name()

        return super(MGSBillingProperty, self).write(vals)

        # for r in self:
        #     for partner in self.env['res.partner'].search([('is_tenancy', '=', True), ('property_id', '=', r.id)]):
        #         partner.customer_id = r.owner_id.id
        #         partner._compute_billing_name()
        #         partner._onchange_billing_name()
        # return res

    def unlink(self):
        reading_ids = self.env['mgs_billing.reading'].search_count(
            [('property_id', '=', self.id)])
        if reading_ids:
            raise UserError(
                "You cannot delete property which has reading history.")
        return super(MGSBillingProperty, self).unlink()

    # @api.model_create_multi
    # def create(self, vals_list):
    #     for vals in vals_list:
    #         if not self.env.company.mgs_billing_global_seq:
    #             vals['name'] = self.env['ir.sequence'].next_by_code(
    #                 self.env['mgs_billing.zone'].search([('id', '=', vals.get('zone_id'))]).code) or '/'
    #         else:
    #             mgs_billing_global_seq_id = self.env.company.mgs_billing_global_seq_id
    #             if not mgs_billing_global_seq_id:
    #                 raise UserError(
    #                     "Please select default global sequence in the billing settings")
    #             vals['name'] = self.env['ir.sequence'].next_by_code(
    #                 mgs_billing_global_seq_id.code) or '/'

    #     recs = super(MGSBillingProperty, self).create(vals_list)
    #     for res in recs:
    #         # create billing account
    #         owner_id = res.owner_id
    #         if not owner_id:
    #             raise ValidationError("Please Set an owner")
    #         property_id = res
    #         created_billing_account = self.env["res.partner"].create({
    #             "name": " - ".join((owner_id.name, res.name)),
    #             "is_tenancy": True,
    #             "property_id": property_id.id,
    #             "product_id": res.product_id.id,
    #             "customer_id": owner_id.id,
    #             "property_product_pricelist": res.pricelist_id.id,
    #             "mobile": owner_id.mobile,
    #             "phone": owner_id.phone,
    #             "email": owner_id.email,
    #             "image_1920": owner_id.image,
    #             "street": property_id.street,
    #             "street2": property_id.street2,
    #             "city": property_id.city,
    #             "country_id": property_id.country_id.id if property_id.country_id else None,
    #             "state_id": property_id.state_id.id if property_id.state_id else None,
    #             "zip": property_id.zip,
    #             "category_id": [(4, res.zone_id.partner_category_id.id)],
    #         })

    #         if res.zone_id.partner_category_id and res.zone_id.partner_category_id.id:
    #             created_billing_account.update({
    #                 "category_id": [(4, res.zone_id.partner_category_id.id)],
    #             })
    #     return recs

    @api.model_create_multi
    def create(self, vals_list):
        # for vals in vals_list:
        #     if not self.env.company.mgs_billing_global_seq:
        #         vals['name'] = self.env['ir.sequence'].next_by_code(
        #             self.env['mgs_billing.zone'].search([('id', '=', vals.get('zone_id'))]).code) or '/'
        #     else:
        #         mgs_billing_global_seq_id = self.env.company.mgs_billing_global_seq_id
        #         if not mgs_billing_global_seq_id:
        #             raise UserError(
        #                 "Please select default global sequence in the billing settings")
        #         vals['name'] = self.env['ir.sequence'].next_by_code(
        #             mgs_billing_global_seq_id.code) or '/'

        recs = super(MGSBillingProperty, self).create(vals_list)
        
        
        for res in recs:
            
            if not self.env.company.mgs_billing_global_seq:
                if res['name'] and res['name'] != "/":
                    continue
                res['name'] = self.env['ir.sequence'].next_by_code(
                    # self.env['mgs_billing.zone'].search([('id', '=', res.get('zone_id'))]).code) or '/'
                    self.env['mgs_billing.zone'].search([('id', '=', res.zone_id.id)]).code) or '/'
            else:
                mgs_billing_global_seq_id = self.env.company.mgs_billing_global_seq_id
                if not mgs_billing_global_seq_id:
                    raise UserError(
                        "Please select default global sequence in the billing settings")
                res['name'] = self.env['ir.sequence'].next_by_code(
                    mgs_billing_global_seq_id.code) or '/'
            
            # create billing account
            owner_id = res.owner_id
            property_id = res
            created_billing_account = self.env["res.partner"].create({
                "name": " - ".join((owner_id.name, res.name)),
                "is_tenancy": True,
                "property_id": property_id.id,
                "product_id": res.product_id.id,
                "customer_id": owner_id.id,
                "property_product_pricelist": res.pricelist_id.id,
                "mobile": owner_id.mobile,
                "phone": owner_id.phone,
                "email": owner_id.email,
                "image_1920": owner_id.image,
                "street": property_id.street,
                "street2": property_id.street2,
                "city": property_id.city,
                "country_id": property_id.country_id.id if property_id.country_id else None,
                "state_id": property_id.state_id.id if property_id.state_id else None,
                "zip": property_id.zip,
                "category_id": [(4, res.zone_id.partner_category_id.id)],
            })

            if res.zone_id.partner_category_id and res.zone_id.partner_category_id.id:
                created_billing_account.update({
                    "category_id": [(4, res.zone_id.partner_category_id.id)],
                })
        return recs

    # def (self):

    def get_reading_history(self):
        for r in self:
            r.reading_history_counter = len(r.meter_reading_ids)

    def action_open_reading_history(self):
        self.ensure_one()
        action = self.env.ref(
            'mgs_billing.mgs_billing_meter_reading_action').sudo().read()[0]
        action['domain'] = "[('property_id.id','=',%s)]" % str(self.id)
        action['context'] = {}
        action['context']['create'] = False
        return action

    @api.depends('property_type_id')
    def get_pricelist(self):
        for r in self:
            r.pricelist_id = r.property_type_id.pricelist_id.id
