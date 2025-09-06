# -*- coding: utf-8 -*-

import xlsxwriter
import base64
from collections import defaultdict
from io import BytesIO
from datetime import date, datetime,time
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import format_date

class MgsNecsomAddonsEmployee(models.Model):
    _inherit = 'hr.employee'

    p_employee_account = fields.Char()
    electricity_deduction = fields.Boolean()
    monthly_advance = fields.Boolean()
    monthly_advance_amount = fields.Float()
    donation1_deduction = fields.Boolean()
    donation1_amount = fields.Float()
    donation2_deduction = fields.Boolean()
    donation2_amount = fields.Float()

class MgsNecsomAddonsEmployeePublic(models.Model):
    _inherit = 'hr.employee.public'

    p_employee_account = fields.Char()
    electricity_deduction = fields.Boolean()
    monthly_advance = fields.Boolean()
    monthly_advance_amount = fields.Float()
    donation1_deduction = fields.Boolean()
    donation1_amount = fields.Float()
    donation2_deduction = fields.Boolean()
    donation2_amount = fields.Float()


class MgsHrElectricityPaysip(models.Model):
    _inherit = 'hr.payslip'

    electricity_deduction = fields.Boolean(related='employee_id.electricity_deduction', states={'done': [('readonly', True)], 'cancel': [('readonly', True)], 'paid': [('readonly', True)]})
    p_employee_account = fields.Char(related='employee_id.p_employee_account')
    e_deduction_amount = fields.Float(states={'done': [('readonly', True)], 'cancel': [('readonly', True)], 'paid': [('readonly', True)]})
    overtime_hours = fields.Float(states={'done': [('readonly', True)], 'cancel': [('readonly', True)], 'paid': [('readonly', True)]})
    unused_leave_hours = fields.Float(states={'done': [('readonly', True)], 'cancel': [('readonly', True)], 'paid': [('readonly', True)]})
    mgs_hourly_wage = fields.Float(readonly=True, compute='get_mgs_hourly_wage', store=True, string="Hourly Wage")
    mgs_payslip_run_id = fields.Many2one('mgs.hr.payslip.run', string="Batch")


    @api.depends('contract_id')
    def get_mgs_hourly_wage(self):
        for r in self:
            if r.contract_id and r.contract_id.wage != 0.0:
                r.mgs_hourly_wage = (r.contract_id.wage / 30) / \
                    r.contract_id.resource_calendar_id.hours_per_day
            else:
                r.mgs_hourly_wage = 0.0


# class MgsHrElectricityPaysipRun(models.Model):
#     _inherit = 'hr.payslip.run'

class MgsPaysipRun(models.Model):
    _inherit = 'hr.payslip.run'

    datas = fields.Binary('File', readonly=True)
    datas_fname = fields.Char('Filename', readonly=True)

    datas_2 = fields.Binary('File', readonly=True)
    datas_fname_2 = fields.Char('Filename', readonly=True)

    def export_account_template(self):
        fp = BytesIO()
        workbook = xlsxwriter.Workbook(fp)
        filename = self.name
        rules=self.env.company.mgs_payroll_account_exp
        num_fmt = workbook.add_format({'num_format': '#,##0.00'})
        sub_heading_format = workbook.add_format({'align': 'center', 'valign': 'vcenter', 'bold': True, 'size': 12})
        cell_text_format = workbook.add_format({'align': 'left', 'bold': False, 'size': 12})
        for rule in rules:
            worksheet = workbook.add_worksheet(rule.name)

            row = 0
            column = 0
            worksheet.write(row, column, "Ref", sub_heading_format)
            worksheet.write(row+1, column, filename+" "+rule.name, sub_heading_format)
            
            column = 1
            worksheet.write(row, column, "Journal Items/Account", sub_heading_format)
            column = 2
            worksheet.write(row, column, "Journal Items/Label", sub_heading_format)
            column = 3
            worksheet.write(row, column, "Journal Items/Partner/External ID", sub_heading_format)
            column = 4
            worksheet.write(row, column, "Journal Items/Debit", sub_heading_format)
            counter = 1
            col = column+counter
            worksheet.write(row, col, "Journal Items/Credit", sub_heading_format)
            debit_total=0
            counter += 1
            for line in self.slip_ids.filtered(lambda x: rule.id in x.line_ids.salary_rule_id.ids):                
                row += 1
                worksheet.write_number(row, 4, 0.0, num_fmt)
                employee_id = line.employee_id
                column = 1
                worksheet.write(row, column, '',cell_text_format)
                column = 2
                worksheet.write(row, column, "".join((rule.name," Deduction-", employee_id.name)),cell_text_format)
                column = 3
                res=employee_id.address_home_id.get_external_id()
                worksheet.write(row, column, res.get(employee_id.address_home_id.id), cell_text_format)
                l=line.line_ids.filtered(lambda x: rule.id == x.salary_rule_id.id)
                worksheet.write_number(row, col, abs(float(l.total)), num_fmt)
                debit_total+=l.total
            row += 1
            worksheet.write(row, 2, "Employee "+rule.name, cell_text_format)
            worksheet.write_number(row, 4, abs(debit_total), num_fmt)
            worksheet.write_number(row, col, 0.0, num_fmt)
        workbook.close()
        out = base64.encodebytes(fp.getvalue())
        self.write({'datas_2': None, 'datas_fname_2': None})
        self.write({'datas_2': out, 'datas_fname_2': filename})
        fp.close()
        filename += '%2Exlsx'
        return {
            'type': 'ir.actions.act_url',
            'target': 'new',
            'url': 'web/content/?model='+self._name+'&id='+str(self.id)+'&field=datas_2&download=true&filename='+filename,
        }

    def export_necsom_hr_template(self):
        fp = BytesIO()
        workbook = xlsxwriter.Workbook(fp)
        filename = self.name
        worksheet = workbook.add_worksheet(filename)
        num_fmt = workbook.add_format({'num_format': '#,##0.00'})
        sub_heading_format = workbook.add_format({'align': 'center', 'valign': 'vcenter', 'bold': True, 'size': 12})
        cell_text_format = workbook.add_format({'align': 'left', 'bold': False, 'size': 12})
        row = 0
        column = 0
        worksheet.write(row, column, "RN", sub_heading_format)
        column = 1
        worksheet.write(row, column, "Name", sub_heading_format)
        counter = 1
        map = {}
        totals = {}
        for rule in self.slip_ids.struct_id.rule_ids:
            col = column+counter
            worksheet.write(row, col, rule.name, sub_heading_format)
            map[rule.id] = col
            totals[rule.id] = 0.0
            counter += 1
        for line in self.slip_ids:
            row += 1
            column = 0
            worksheet.write(row, column, int(line.employee_id.registration_number),cell_text_format)
            column = 1
            worksheet.write(row, column, line.employee_id.name,cell_text_format)
            for l in line.line_ids:
                totals[l.salary_rule_id.id] += l.total
                worksheet.write_number(row, map[l.salary_rule_id.id], float(
                    l.total), num_fmt)  # '{:,.2f}'.format(l.total)
        row += 1
        for item in totals.items():
            worksheet.write_number(row, map[item[0]], float(item[1]), num_fmt)

        workbook.close()
        out = base64.encodebytes(fp.getvalue())
        self.write({'datas': out, 'datas_fname': filename})
        fp.close()
        filename += '%2Exlsx'
        return {
            'type': 'ir.actions.act_url',
            'target': 'new',
            'url': 'web/content/?model='+self._name+'&id='+str(self.id)+'&field=datas&download=true&filename='+filename,
        }
class MgsPaysipRun(models.Model):
    _name = 'mgs.hr.payslip.run'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'MGS Payslip Batches'
    _order = 'date_end desc'

    name = fields.Char(required=True, readonly=True, states={'draft': [('readonly', False)]})
    slip_ids = fields.One2many('hr.payslip', 'mgs_payslip_run_id', string='Payslips', readonly=True, states={'draft': [('readonly', False)]})
    state = fields.Selection([('draft', 'New'),('verify', 'Confirmed'),('close', 'Done'),('paid', 'Paid'),], string='Status', index=True, readonly=True, copy=False, default='draft', store=True, compute='_compute_state_change')
    date_start = fields.Date(string='Date From', required=True, readonly=True, states={'draft': [('readonly', False)]}, default=lambda self: fields.Date.to_string(date.today().replace(day=1)))
    date_end = fields.Date(string='Date To', required=True, readonly=True, states={'draft': [('readonly', False)]}, default=lambda self: fields.Date.to_string((datetime.now() + relativedelta(months=+1, day=1, days=-1)).date()))
    payslip_count = fields.Integer(compute='_compute_payslip_count')
    company_id = fields.Many2one('res.company', string='Company', readonly=True, required=True, default=lambda self: self.env.company)
    structure_id = fields.Many2one('hr.payroll.structure', string='Salary Structure', readonly=True, states={'draft': [('readonly', False)]})
    employee_ids = fields.Many2many('hr.employee', required=True, domain=[('contract_id','!=',False)], readonly=True, states={'draft': [('readonly', False)]})
    datas = fields.Binary('File', readonly=True)
    datas_fname = fields.Char('Filename', readonly=True)

    datas_2 = fields.Binary('File', readonly=True)
    datas_fname_2 = fields.Char('Filename', readonly=True)


    def compute_sheet(self):
        self.ensure_one()
        payslip_run = self
        employees = self.employee_ids
        if not employees:
            raise UserError(_("You must select employee(s) to generate payslip(s)."))
        #Prevent a payslip_run from having multiple payslips for the same employee
        
        employees -= payslip_run.slip_ids.employee_id
        success_result = {
            'type': 'ir.actions.act_window',
            'res_model': 'mgs.hr.payslip.run',
            'views': [[False, 'form']],
            'res_id': payslip_run.id,
        }
        if not employees:
            return success_result

        payslips = self.env['hr.payslip']
        Payslip = self.env['hr.payslip']

        contracts = employees._get_contracts(
            payslip_run.date_start, payslip_run.date_end, states=['open', 'close']
        ).filtered(lambda c: c.active)
        contracts.generate_work_entries(payslip_run.date_start, payslip_run.date_end)
        work_entries = self.env['hr.work.entry'].search([
            ('date_start', '<=', payslip_run.date_end),
            ('date_stop', '>=', payslip_run.date_start),
            ('employee_id', 'in', employees.ids),
        ])
        self._check_undefined_slots(work_entries, payslip_run)

        if(self.structure_id.type_id.default_struct_id == self.structure_id):
            work_entries = work_entries.filtered(lambda work_entry: work_entry.state != 'validated')
            if work_entries._check_if_error():
                work_entries_by_contract = defaultdict(lambda: self.env['hr.work.entry'])

                for work_entry in work_entries.filtered(lambda w: w.state == 'conflict'):
                    work_entries_by_contract[work_entry.contract_id] |= work_entry

                for contract, work_entries in work_entries_by_contract.items():
                    conflicts = work_entries._to_intervals()
                    time_intervals_str = "\n - ".join(['', *["%s -> %s" % (s[0], s[1]) for s in conflicts._items]])
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Some work entries could not be validated.'),
                        'message': _('Time intervals to look for:%s', time_intervals_str),
                        'sticky': False,
                    }
                }

        default_values = Payslip.default_get(Payslip.fields_get())
        payslips_vals = []
        for contract in contracts:
            values = dict(default_values, **{
                'name': _('New Payslip'),
                'employee_id': contract.employee_id.id,
                'mgs_payslip_run_id': payslip_run.id,
                'date_from': payslip_run.date_start,
                'date_to': payslip_run.date_end,
                'contract_id': contract.id,
                'struct_id': self.structure_id.id or contract.structure_type_id.default_struct_id.id,
            })
            payslips_vals.append(values)
        payslips = Payslip.with_context(tracking_disable=True).create(payslips_vals)
        payslips._compute_name()
        payslips.compute_sheet()
        payslip_run.state = 'verify'
        return success_result
    
    def _check_undefined_slots(self, work_entries, payslip_run):
        """
        Check if a time slot in the contract's calendar is not covered by a work entry
        """
        work_entries_by_contract = defaultdict(lambda: self.env['hr.work.entry'])
        for work_entry in work_entries:
            work_entries_by_contract[work_entry.contract_id] |= work_entry

        for contract, work_entries in work_entries_by_contract.items():
            if contract.work_entry_source != 'calendar':
                continue
            calendar_start = pytz.utc.localize(datetime.combine(max(contract.date_start, payslip_run.date_start), time.min))
            calendar_end = pytz.utc.localize(datetime.combine(min(contract.date_end or date.max, payslip_run.date_end), time.max))
            outside = contract.resource_calendar_id._attendance_intervals_batch(calendar_start, calendar_end)[False] - work_entries._to_intervals()
            if outside:
                time_intervals_str = "\n - ".join(['', *["%s -> %s" % (s[0], s[1]) for s in outside._items]])
                raise UserError(_("Some part of %s's calendar is not covered by any work entry. Please complete the schedule. Time intervals to look for:%s") % (contract.employee_id.name, time_intervals_str))

    def _compute_payslip_count(self):
        for payslip_run in self:
            payslip_run.payslip_count = len(payslip_run.slip_ids)

    @api.depends('slip_ids', 'state')
    def _compute_state_change(self):
        for payslip_run in self:
            if payslip_run.state == 'draft' and payslip_run.slip_ids:
                payslip_run.update({'state': 'verify'})

    def action_draft(self):
        if self.slip_ids.filtered(lambda s: s.state == 'paid'):
            raise ValidationError(_('You cannot reset a batch to draft if some of the payslips have already been paid.'))
        self.write({'state': 'draft'})
        self.slip_ids.write({'state': 'draft'})

    def action_open(self):
        self.write({'state': 'verify'})

    def action_close(self):
        if self._are_payslips_ready():
            self.write({'state' : 'close'})

    def action_paid(self):
        # self.mapped('slip_ids').action_payslip_paid()
        for slip in self.slip_ids:
            slip.action_payslip_paid()
        self.write({'state': 'paid'})

    def action_validate(self):
        payslip_done_result = self.slip_ids.filtered(lambda slip: slip.state not in ['draft', 'cancel'])
        for slip in payslip_done_result:
            slip.action_payslip_done()
        self.action_close()
        return payslip_done_result

    def action_open_payslips(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "res_model": "hr.payslip",
            "views": [[False, "list"], [False, "form"]],
            "domain": [['id', 'in', self.slip_ids.ids]],
            "context": {'default_mgs_payslip_run_id': self.id},
            "name": "Payslips",
        }

    def action_open_payslip_run_form(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'mgs.hr.payslip.run',
            'views': [[False, 'form']],
            'res_id': self.id,
        }


    @api.ondelete(at_uninstall=False)
    def _unlink_if_draft_or_cancel(self):
        if any(self.filtered(lambda payslip_run: payslip_run.state not in ('draft'))):
            raise UserError(_('You cannot delete a payslip batch which is not draft!'))
        if any(self.mapped('slip_ids').filtered(lambda payslip: payslip.state not in ('draft', 'cancel'))):
            raise UserError(_('You cannot delete a payslip which is not draft or cancelled!'))

    def _are_payslips_ready(self):
        return all(slip.state in ['done', 'cancel'] for slip in self.mapped('slip_ids'))



