# -*- coding: utf-8 -*-
# (c) 2016 Serv. Tecnol. Avanzados - Pedro M. Baeza
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp import api, fields, models
from dateutil.relativedelta import relativedelta


class AccountAnalyticAccount(models.Model):
    _inherit = "account.analytic.account"

    @api.model
    def _prepare_invoice(self, contract):
        invoice = super(AccountAnalyticAccount, self)._prepare_invoice(contract)
        next_date = fields.Date.from_string(
            contract.recurring_next_date or fields.Date.today())
        interval = contract.recurring_interval
        end_date = next_date - relativedelta(days=1)
        start_date = next_date
        if contract.recurring_rule_type == 'daily':
            start_date = next_date - relativedelta(days=interval)
        elif contract.recurring_rule_type == 'weekly':
            start_date = next_date - relativedelta(weeks=interval)
        elif contract.recurring_rule_type == 'monthly':
            start_date = next_date - relativedelta(months=interval)
        else:
            start_date = next_date - relativedelta(years=interval)
        invoice.update({
            'invoice_date_start': start_date,
            'invoice_date_end': end_date
        })
        return invoice
