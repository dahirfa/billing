# # -*- coding: utf-8 -*-
# from odoo import _, api, fields, models


# # class AccountBudgetPostInherit(models.Model):
# #     _inherit = "account.budget.post"

# #     mgs_budget_position_category_id = fields.Many2one(
# #         string="Budget Postion Category",
# #         comodel_name="mgs.budget.position.category",
# #         ondelete="restrict",
# #     )


# class MgsBudgetPositionCategory(models.Model):
#     _name = "mgs.budget.position.category"
#     _description = "MGS Budget Position Category"

#     name = fields.Char(string="Category Name", required=True, copy=False)


# class CrossedoverBudgetLineInherit(models.Model):
#     _inherit = "crossovered.budget.lines"

#     # budget_position_category = fields.Many2one(
#     #     string="Budget Position Category",
#     #     related="general_budget_id.mgs_budget_position_category_id",
#     #     readonly=True,
#     #     store=True,
#     # )

#     difference = fields.Float(
#         string="Difference",
#         compute="_compute_difference"
#     )

#     @api.depends("planned_amount", "practical_amount")
#     def _compute_difference(self):
#         for record in self:
#             record.difference = record.planned_amount - record.practical_amount
            
#     @api.model
#     def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
#         # overrides the default read_group in order to compute the computed fields manually for the group

#         fields_list = {'difference'}

#         # Not any of the fields_list support aggregate function like :sum
#         def truncate_aggr(field):
#             field_no_aggr = field.split(':', 1)[0]
#             if field_no_aggr in fields_list:
#                 return field_no_aggr
#             return field
#         fields = {truncate_aggr(field) for field in fields}

#         # Read non fields_list fields
#         result = super(CrossedoverBudgetLineInherit, self).read_group(
#             domain, list(fields - fields_list), groupby, offset=offset,
#             limit=limit, orderby=orderby, lazy=lazy)

#         # Populate result with fields_list values
#         if fields & fields_list:
#             for group_line in result:

#                 # initialise fields to compute to 0 if they are requested
#                 if 'difference' in fields:
#                     group_line['difference'] = 0

#                 domain = group_line.get('__domain') or domain
#                 all_budget_lines_that_compose_group = self.search(domain)

#                 for budget_line_of_group in all_budget_lines_that_compose_group:
#                     if 'difference' in fields:
#                         group_line['difference'] += budget_line_of_group.difference
#         return result