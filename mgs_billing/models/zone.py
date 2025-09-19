from odoo import models, fields, api
from odoo.exceptions import UserError


class MGSBillingZones(models.Model):
    _name = 'mgs_billing.zone'
    _description = 'Billing Zone'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = "id DESC"

    name = fields.Char()
    code = fields.Char(required=True)

    property_ids = fields.One2many(
        'mgs_billing.property', 'zone_id', string='Properties')
    collector_id = fields.Many2one(
        'res.partner', string='Collector', domain=[('is_collector', '=', True)], tracking=True)

    counter = fields.Integer(
        string='Properties', compute='_count_properties', store=True)
    active_counter = fields.Integer(
        string='Active Properties', compute='_count_properties', store=True)
    aactive = fields.Boolean(default=True)
    journal_id = fields.Many2one('account.journal', string="Invoice Journal", domain="[('type', '=', 'sale')]", required=True, company_dependent=True, check_company=True,
                                 help="If set, properties with zone this will be invoiced in this journal; ""otherwise the sales journal with the lowest sequence is used.")
    sequence_id = fields.Many2one('ir.sequence')
    partner_category_id = fields.Many2one(
        'res.partner.category', string='Zone Customers Tag')
    company_id = fields.Many2one(
        'res.company', string='Company', default=lambda self: self.env.company.id)
    _sql_constraints = [
        ('unique_code', 'unique(code)', 'Code already exists!')]

    def unlink(self):
        for rec in self:
            property_ids = rec.env['mgs_billing.property'].search(
                [('zone_id', '=', rec.id)])

            if len(property_ids) > 0:
                raise UserError(
                    "You cannot delete zone which has related properties.")
        return super(MGSBillingZones, self).unlink()

    def write(self, vals):
        res = super(MGSBillingZones, self).write(vals)
        seq_obj = self.env['ir.sequence']
        if self.partner_category_id:
            if vals.get('name'):
                self.partner_category_id.name = vals.get('name')
        if self.sequence_id:
            if vals.get('name'):
                self.sequence_id.name = vals.get('name')
            if vals.get('code'):
                self.sequence_id.prefix = vals.get('code')
                self.sequence_id.code = vals.get('code')
        elif not self.sequence_id and self.name and self.code:
            seq_id = seq_obj.create({
                'name': self.name,
                'code': vals.get('code'),
                'prefix': self.code,
                'padding': 3,
                'company_id': False, })
            self.sequence_id = seq_id.id
        return res

    @api.model_create_multi
    def create(self, vals_list):
        seq_obj = self.env['ir.sequence']
        category_obj = self.env['res.partner.category']
        for vals in vals_list:
            if vals.get('name') and vals.get('code'):
                cat_id = category_obj.create({'name': vals.get('name')})
                seq_id = seq_obj.sudo().create({
                    'name': vals.get('name'),
                    'code': vals.get('code'),
                    'prefix': vals.get('code'),
                    'padding': 3,
                    'company_id': False, })

                vals['sequence_id'] = seq_id.id
                vals['partner_category_id'] = cat_id.id
        result = super(MGSBillingZones, self).create(vals_list)
        return result

    @api.depends('property_ids')
    def _count_properties(self):
        for r in self:
            r.counter = len(r.property_ids.ids)
            r.active_counter = len(r.property_ids.filtered(
                lambda p: p.state == 'connected'))

    def action_open_properties(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Properties',
            'view_mode': 'list,form',
            'res_model': 'mgs_billing.property',
            'domain': [('zone_id', '=', self.id)],
            'context': "{'create': False}"}
