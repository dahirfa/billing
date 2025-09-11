# -*- coding: utf-8 -*-
import json
from odoo import http
from odoo.http import request
import werkzeug.wrappers as wrap

# class MgsNecsomAddons(http.Controller):
#     @http.route('/mgs/logout', type="http",auth='none')
#     def logout(self, **kw):
#         request.session.logout()
#         return wrap.Response(
#                 status=200,
#                 content_type="application/json; charset=utf-8",
#                 headers=[("Cache-Control", "no-store"), ("Pragma", "no-cache")],
#                 response=json.dumps(  {
#             "msg":"Successfully logged out"
#         }))