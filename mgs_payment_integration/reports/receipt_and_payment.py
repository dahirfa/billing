from odoo import _, api, fields, models

import logging
_logger = logging.getLogger(__name__)



class ReceiptAndPaymentReport(models.AbstractModel):
    _name = 'report.mgs_payment_integration.receipt_and_payment_report'
    _description = 'Receipt and Payment Report'

    @api.model
    def _lines(
        self, date_from, date_to, company_id, partner_id, journal_id,
        user_id, payment_type, mgs_sender_phone, mgs_transaction_ref,
        group_by_option, report_type
    ):
        p_type = 'asset_receivable' if payment_type == 'Receipt' else 'liability_payable'
        params = [p_type]

        query = """
        select am.name as receipt_no, rp.id as partner_id, rp.name as partner_name, aml.name as ref,
        rp.mobile as phone, aml.date as date, (aml.credit-aml.debit) as amount_paid,
        aj.name ->> 'en_US' as journal_name, ap.memo as memo,
        ap.mgs_transaction_ref as mgs_transaction_ref, ap.mgs_sender_phone as mgs_sender_phone,
        aml.create_uid, ru.id as cashier_id, rup.name as cashier_name    
        from account_move_line as aml
        left join res_partner as rp on aml.partner_id=rp.id
        left join account_journal as aj on aml.journal_id=aj.id
        left join account_move as am on aml.move_id=am.id
        left join account_payment as ap on am.origin_payment_id=ap.id
        left join account_account as aa on aml.account_id=aa.id
        left join res_users ru on aml.create_uid = ru.id
        join res_partner rup on ru.partner_id = rup.id
        where aml.parent_state = 'posted' and aa.account_type = %s
        and aj.type in ('bank', 'cash')
        """

        if p_type == 'asset_receivable':
            query += """ and aml.credit > 0 """
        else:
            query += """ and aml.debit > 0 """

        if date_from:
            params.append(date_from)
            query += """ and aml.date >= %s"""
        if date_to:
            params.append(date_to)
            query += """ and aml.date <= %s"""
        if partner_id:
            query += f" and aml.partner_id = {partner_id}"
        if journal_id:
            query += f" and aml.journal_id = {journal_id}"
        if user_id:
            query += f" and aml.create_uid = {user_id}"
        if company_id:
            query += f" and aml.company_id = {company_id}"
        if mgs_sender_phone:
            query += f" and ap.mgs_sender_phone ilike '{mgs_sender_phone}'"
        if mgs_transaction_ref:
            query += f" and ap.mgs_transaction_ref ilike '{mgs_transaction_ref}'"

        self.env.cr.execute(query, tuple(params))
        res = self.env.cr.dictfetchall()

       
        if report_type == "summary":
            if group_by_option == "account":
                grouped = {}
                for r in res:
                    journal = r["journal_name"] or "Unknown"
                    cashier = r["cashier_name"] or "Unknown"
                    grouped.setdefault(journal, {})
                    grouped[journal].setdefault(cashier, {"total": 0, "total_receipts": 0})

                    grouped[journal][cashier]["total"] += r["amount_paid"]
                    grouped[journal][cashier]["total_receipts"] += 1
                    _logger.info(grouped)
                return grouped

            elif group_by_option == "cashier":
                grouped = {}
                for r in res:
                    cashier = r["cashier_name"] or "Unknown"
                    journal = r["journal_name"] or "Unknown"
                    grouped.setdefault(cashier, {})
                    grouped[cashier].setdefault(journal, {"total": 0, "total_receipts": 0})

                    grouped[cashier][journal]["total"] += r["amount_paid"]
                    grouped[cashier][journal]["total_receipts"] += 1
                        
                _logger.info(grouped)
                return grouped
            else:
                grouped = {}
                for r in res:
                    journal = r["journal_name"] or "Unknown"
                    cashier = r["cashier_name"] or "Unknown"
                    grouped.setdefault(journal, {})
                    grouped[journal].setdefault(cashier, {"total": 0})
                    grouped[journal][cashier]["total"] += r["amount_paid"]
                _logger.info(grouped)
                return grouped

        else:
            if group_by_option == "cashier":
                grouped = {}
                for r in res:
                    cashier = r["cashier_name"] or "Unknown"
                    grouped.setdefault(cashier, []).append(r)
                return grouped
            elif group_by_option == "account":
                grouped = {}
                for r in res:
                    journal = r["journal_name"] or "Unknown"
                    grouped.setdefault(journal, []).append(r)
                return grouped
            else:
                return res


    @api.model
    def _get_report_values(self, docids, data=None):
        model = self.env.context.get('active_model')
        docs = self.env[model].browse(self.env.context.get('active_id'))

        return {
            'doc_ids': self.ids,
            'doc_model': model,
            'docs': docs,
            'date_from': data['form']['date_from'],
            'date_to': data['form']['date_to'],
            'partner_id': data['form']['partner_id'],
            'journal_id': data['form']['journal_id'],
            'user_id': data['form']['user_id'],
            'company_id': self.env['res.company'].search([('id', '=', data['form']['company_id'][0])]),
            'payment_type': data['form']['payment_type'],
            'mgs_sender_phone': data['form']['mgs_sender_phone'],
            'mgs_transaction_ref': data['form']['mgs_transaction_ref'],
            'lines': self._lines,
        }




