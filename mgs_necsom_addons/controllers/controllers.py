# -*- coding: utf-8 -*-
import json
from odoo import http
from odoo.http import request
import werkzeug.wrappers as wrap

class MgsNecsomAddons(http.Controller):
    @http.route('/mgs/logout', type="http",auth='none')
    def logout(self, **kw):
        request.session.logout()
        return wrap.Response(
                status=200,
                content_type="application/json; charset=utf-8",
                headers=[("Cache-Control", "no-store"), ("Pragma", "no-cache")],
                response=json.dumps(  {
            "msg":"Successfully logged out"
        }))

#     @http.route('/mgs_necsom_addons/mgs_necsom_addons/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('mgs_necsom_addons.listing', {
#             'root': '/mgs_necsom_addons/mgs_necsom_addons',
#             'objects': http.request.env['mgs_necsom_addons.mgs_necsom_addons'].search([]),
#         })

#     @http.route('/mgs_necsom_addons/mgs_necsom_addons/objects/<model("mgs_necsom_addons.mgs_necsom_addons"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('mgs_necsom_addons.object', {
#             'object': obj
#         })
