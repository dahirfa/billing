# -*- coding: utf-8 -*-
# from odoo import http
# from odoo.http import request
# from odoo.exceptions import UserError


# class SlniaErpApi(http.Controller):
#     @http.route('/api/policy_type/create/', type='json', auth='user')
#     def create_policy_type(self, **kw):
#         try:
#             policy_type_obj = request.env['mgs_slnia.policy_type']
#             inserted_policy_type = policy_type_obj.sudo().create({
#                 'name': kw.get("name"),
#                 'sahal_policy_type_id': kw.get("sahal_policy_type_id")
#             })

#             return {
#                 "status": 200,
#                 "record": inserted_policy_type.read(['name', 'sahal_policy_type_id'])
#             }
#         except Exception as e:
#             pass
