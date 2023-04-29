from odoo import models, fields, api, _
from odoo.exceptions import UserError

class AccountMove(models.Model):
    _inherit = 'account.move'

    # disc_total = fields.Monetary(string='Discount Total', compute='get_discount_total', currency_field='company_currency_id')

    # @api.depends('invoice_line_ids')
    # def get_discount_total(self):
    #     for rec in self:
    #         rec.disc_total = - 1 * sum(rec.invoice_line_ids.mapped('discount_amount'))
    
    def action_discount_amount(self):
        return {
        'name': _('Discount Amount'),
        'res_model': 'account.discount.amount',
        'view_mode': 'form',
        'context': {
            'active_model': 'account.move',
            'active_ids': self.ids,
        },
        'target': 'new',
        'type': 'ir.actions.act_window',
    }

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    discount_amount = fields.Float(string='Discount Amount')

