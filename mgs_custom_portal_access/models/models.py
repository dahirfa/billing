# -*- coding: utf-8 -*-

from odoo import models, fields, api, Command
from odoo.tools.translate import _
from odoo.exceptions import UserError
class MgsPortalWizard(models.TransientModel):

    _name = 'mgs.portal.wizard'
    _description = 'Mgs Grant Portal Access'

    def _mgs_default_partner_ids(self):
        partner_ids = self.env.context.get('default_partner_ids', []) or self.env.context.get('active_ids', [])
        contact_ids = set()
        for partner in self.env['res.partner'].sudo().browse(partner_ids):
            contact_partners = partner.child_ids.filtered(lambda p: p.type in ('contact', 'other')) | partner
            contact_ids |= set(contact_partners.ids)

        return [Command.link(contact_id) for contact_id in contact_ids]

    partner_ids = fields.Many2many('res.partner', string='Partners', default=_mgs_default_partner_ids)
    user_ids = fields.One2many('mgs.portal.wizard.user', 'wizard_id', string='Users', compute='_mgscompute_user_ids', store=True, readonly=False)
    
    @api.depends('partner_ids')
    def _mgscompute_user_ids(self):
        for portal_wizard in self:
            portal_wizard.user_ids = [
                Command.create({
                    'partner_id': partner.id,
                    'email': partner.email,
                    # 'password': partner.password
                })
                for partner in portal_wizard.partner_ids
            ]
            
    @api.model
    def mgs_action_open_wizard(self):
        
        portal_wizard = self.create({})
        return portal_wizard._action_open_modal()

    def _action_open_modal(self):
        
        return {
            'name': _('Portal Access'),
            'type': 'ir.actions.act_window',
            'res_model': 'mgs.portal.wizard',
            'view_type': 'form',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new',
        }
class MgsPortalWizardUser(models.TransientModel):
   
    _name = 'mgs.portal.wizard.user'
    _description = 'Mgs Portal User Config'

    wizard_id = fields.Many2one('mgs.portal.wizard', string='Wizard', required=True, ondelete='cascade')
    partner_id = fields.Many2one('res.partner', string='Contact', required=True, readonly=True, ondelete='cascade')
    email = fields.Char('Email')
    password = fields.Char()

    user_id = fields.Many2one('res.users', string='User', compute='compute_user_id', compute_sudo=True)
    login_date = fields.Datetime(related='user_id.login_date', string='Latest Authentication')
    is_portal = fields.Boolean('Is Portal', compute='compute_group_details')
    is_internal = fields.Boolean('Is Internal', compute='compute_group_details')
    email_state = fields.Selection([
        ('ok', 'Valid'),
        ('ko', 'Invalid'),
        ('exist', 'Already Registered')],
        string='Status', compute='compute_email_state', default='ok')
    
    @api.depends('email')
    def compute_email_state(self):
        portal_users_with_email = self.filtered(lambda user: (user.email))
        (self - portal_users_with_email).email_state = 'ko'

        normalized_emails = [(portal_user.email) for portal_user in portal_users_with_email]
        existing_users = self.env['res.users'].with_context(active_test=False).sudo().search_read([('login', 'in', normalized_emails)], ['id', 'login'])

        for portal_user in portal_users_with_email:
            if next((user for user in existing_users if user['login'] == (portal_user.email) and user['id'] != portal_user.user_id.id), None):
                portal_user.email_state = 'exist'
            else:
                portal_user.email_state = 'ok'
    @api.depends('partner_id')
    def compute_user_id(self):
        for portal_wizard_user in self:
            user = portal_wizard_user.partner_id.with_context(active_test=False).user_ids
            portal_wizard_user.user_id = user[0] if user else False

    @api.depends('user_id', 'user_id.groups_id')
    def compute_group_details(self):
        for portal_wizard_user in self:
            user = portal_wizard_user.user_id

            if user and user._is_internal():
                portal_wizard_user.is_internal = True
                portal_wizard_user.is_portal = False
            elif user and user.has_group('base.group_portal'):
                portal_wizard_user.is_internal = False
                portal_wizard_user.is_portal = True
            else:
                portal_wizard_user.is_internal = False
                portal_wizard_user.is_portal = False
    
    def mgs_action_grant_access(self):
        
        self.ensure_one()
        self.assert_user_email_uniqueness()

        if self.is_portal or self.is_internal:
            raise UserError(_('The partner "%s" already has the portal access.', self.partner_id.name))

        group_portal = self.env.ref('base.group_portal')
        group_public = self.env.ref('base.group_public')

        self.update_partner_email()
        user_sudo = self.user_id.sudo()

        if not user_sudo:
            # create a user if necessary and make sure it is in the portal group
            company = self.partner_id.company_id or self.env.company
            user_sudo = self.sudo().with_company(company.id).create_user()
        return self.action_refresh_modal()
            
    def action_refresh_modal(self):
        """Refresh the portal wizard modal and keep it open. Used as fallback action of email state icon buttons,
        required as they must be non-disabled buttons to fire mouse events to show tooltips on email state."""
        return self.wizard_id._action_open_modal()
    def create_user(self):
       
        return self.env['res.users'].with_context(no_reset_password=True)._create_user_from_template({
            'email': (self.email),
            'login': (self.email),
            'password': (self.password),
            'partner_id': self.partner_id.id,
            'company_id': self.env.company.id,
            'company_ids': [(6, 0, self.env.company.ids)],
        })
    def assert_user_email_uniqueness(self):
        """Check that the email can be used to create a new user."""
        self.ensure_one()
        
        if self.email_state == 'exist':
            raise UserError(_('The contact "%s" has the same email as an existing user', self.partner_id.name))

    def update_partner_email(self):
        """Update partner email on portal action, if a new one was introduced and is valid."""
        email_normalized = (self.email)
        if self.email_state == 'ok' and (self.partner_id.email) != email_normalized:
            self.partner_id.write({'email': email_normalized})
    
    def change_password(self):
        self.update_partner_email()
        self.user_id.write({
            'login': (self.email),
            'password': (self.password)
            })