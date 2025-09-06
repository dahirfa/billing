# -*- coding: utf-8 -*-
# from odoo import http


# class CrmExtension(http.Controller):
#     @http.route('/crm_extension/crm_extension/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/crm_extension/crm_extension/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('crm_extension.listing', {
#             'root': '/crm_extension/crm_extension',
#             'objects': http.request.env['crm_extension.crm_extension'].search([]),
#         })

#     @http.route('/crm_extension/crm_extension/objects/<model("crm_extension.crm_extension"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('crm_extension.object', {
#             'object': obj
#         })
