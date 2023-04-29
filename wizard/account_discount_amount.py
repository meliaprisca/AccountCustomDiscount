from odoo import models, fields, api, _
import openpyxl
import base64
from io import BytesIO
import csv
import pytz
from io import StringIO
from datetime import datetime, time
from odoo.tools.translate import _
from odoo.exceptions import except_orm, UserError
from xlrd import open_workbook
from odoo.exceptions import UserError


class AccountDiscountAmountLine(models.TransientModel):
    
    _name = 'account.discount.amount.line'

    discount_line = fields.Many2one('account.discount.amount', string='Kasir')
    product_id = fields.Many2one('product.product', 'Product')
    account_id = fields.Many2one('account.account', 'Account')
    labell = fields.Char(string='Label')
    price_unit = fields.Float(string='Price Unit')
    quantity = fields.Float(string='Quantity')
    tax_id = fields.Many2one('account.tax',string="Taxes",)
    discount_amount = fields.Float(string='Discount')
    price_subtotal = fields.Float(string='Subtotal')

class AccountDiscountAmount(models.TransientModel):

    _name = 'account.discount.amount'

    file_xlsx = fields.Binary(string="File", required=True)
    discount_new = fields.Float(string='Discount Amount')
    state = fields.Selection([('import', 'Importing File'), ('view', 'View Items'), ('done', 'Done')],string='State', default='import')
    # state = fields.Selection([('import', 'Importing File'), ('error', 'View Errors'), ('view', 'View Items'), ('done', 'Done')],string='State', default='import')
    # invoice_line_ids = fields.One2many('account.move.line', 'move_id', string='Invoice lines',)
    invoice_line_ids = fields.One2many('account.discount.amount.line', 'discount_line', string='Invoice lines',)

    def action_discount_amount_wizard(self):
        ids_to_change = self._context.get('active_ids')
        active_model = self._context.get('active_model')
        print(self._context.get('active_id'),'AAAAAAAAAAAAAAAAAAAAAAA')
        
    def import_customer(self):
        try:
            wb = openpyxl.load_workbook(filename=BytesIO(base64.b64decode(self.file_xlsx)), read_only=True)
            ws = wb.active
            for record in ws.iter_rows(min_row=2, max_row=None, min_col=None,max_col=None, values_only=True):
                val ={
                    'product_id': self.env['product.product'].search([('name', '=', record[4])]).id,
                    'name': record[5],
                    # 'account_id': self.env['account.account'].search([('name', '=', record[6])]).id,
                    'price_unit': record[7],
                    'quantity': record[8],
                    'taxes': record[9],
                    'discount_amount': record[10],
                    }
                self._context.get('active_ids').invoice_line_ids.append([0, 0, val])
        except:
            raise UserError(_('Please insert a valid file'))

    def import_customer_new(self):
        try:
            wb = open_workbook(filename=self.file_xlsx)
        except FileNotFoundError:
            raise UserError(_('Please insert a valid file'))
        
        sheet = wb.sheet_by_index(0)
        vals = []
        for row in range(sheet.nrows):
            if row >=1 :
                row_vals = sheet.row_values(row)
                val ={
                    'product_id': self.env['product.product'].search([('name', 'ilike', row_vals[4])]).id,
                    'labell': row_vals[5],
                    # 'account_id': self.env['account.account'].search([('name', '=', record[6])]).id,
                    'price_unit': row_vals[7],
                    'quantity': row_vals[8],
                    # 'taxes': row_vals[9],
                    'discount_amount': row_vals[10],
                    }
                vals.append([0, 0, val])
            
        self.invoice_line_ids = vals
        self.write({'state': 'view',})
        return {
                'name': _('View Items'),
                'type': 'ir.actions.act_window',
                'res_model': self._name,
                'view_mode': 'form',
                'target': 'new',
                'context': self._context,
                'res_id': self.id,
            }

    def import_file(self):

        result = ''
        all_datas = []
        try:
            data = base64.b64decode(self.file_xlsx)
            wb = open_workbook(file_contents=data)
            sheet = wb.sheet_by_index(0)
        except:
            raise except_orm(_('Error'), _('An error occurred while reading the file. Please '
                                           'check if the format is correct.'))
        product_obj = self.env['product.product']
        account_obj = self.env['account.account']
        tax_obj = self.env['account.tax']
        i=0
        datas = []
        for row_no in range(sheet.nrows):
            row = list(
                map(lambda row: isinstance(row.value, bytes) and row.value.encode('utf-8') or str(row.value),
                    sheet.row(row_no)))
            if i!=0:
                product = (product_obj.search(
                        [('name', 'ilike', row[4])],limit=1)).id
                row_change = row[6][0:6]
                account = (account_obj.search(
                        [('code', 'ilike', row_change)],limit=1)).id
                tax = (tax_obj.search(
                        [('name', 'ilike', row[9])],limit=1)).id
                if not product:
                    result += _('Error in line %d: Product is not '
                                'found.\n') % (i)
                if self.discount_new == 0.00:
                    data = {
                        'product_id': product,
                        'labell': row[5],
                        'account_id': account,
                        'price_unit': float(row[7]),
                        'quantity': float(row[8]),
                        'tax_id': tax,
                        'discount_amount': float(row[10]),
                        'price_subtotal': (float(row[7]) * float(row[8]) ) - float(row[10]),
                        }
                if self.discount_new > 0.00:
                    data = {
                        'product_id': product,
                        'labell': row[5],
                        'account_id': account,
                        'price_unit': float(row[7]),
                        'quantity': float(row[8]),
                        'tax_id': tax,
                        'discount_amount': self.discount_new,
                        'price_subtotal': (float(row[7]) * float(row[8]) ) - self.discount_new,
                        }
                datas.append((0, 0, data))

            i+=1
        self.update({
            'invoice_line_ids': datas
            })

        
        if result == '':
                result = _('There were no errors found for this file.'),
        self.write({'state': 'view',})
        return {
                'name': _('View Items'),
                'type': 'ir.actions.act_window',
                'res_model': self._name,
                'view_mode': 'form',
                'target': 'new',
                'context': self._context,
                'res_id': self.id,
            }

    def view_items(self):
        self.write({'state': 'view'})
        return {
            'name': _('View Items'),
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'view_mode': 'form',
            'target': 'new',
            'context': self._context,
            'res_id': self.id,
        }
    
    def done(self):
        move_record=self.env['account.move'].search([('id','=',self._context.get('active_id'))])
        for line in move_record.invoice_line_ids:
            # correction_line = self.invoice_line_ids
            for correction_line in self.invoice_line_ids:
                if line.product_id.id==correction_line.product_id.id:
                        line.update(
                            {
                                'name': correction_line.labell,
                                'price_unit': correction_line.price_unit,
                                'quantity': correction_line.quantity,
                                'discount_amount': correction_line.discount_amount,
                                'price_subtotal': correction_line.price_subtotal,
                                # 'price_subtotal': (correction_line.price_unit * correction_line.quantity) - correction_line.discount_amount,
                            }
                        )
                        move_record.update(
                            {
                                'amount_untaxed': sum(line.mapped('price_subtotal')),
                                'amount_total': sum(line.mapped('price_subtotal')) + move_record.amount_tax,
                            }
                        )
        for journal_line in move_record.line_ids:
            for correction_line in self.invoice_line_ids:
                if journal_line.name == correction_line.labell:
                    journal_line.update({
                        'credit': (correction_line.price_unit * correction_line.quantity) - correction_line.discount_amount,
                    })
                if journal_line.account_id.user_type_id.id == 1:
                    journal_line.update({
                        'debit': (correction_line.price_unit * correction_line.quantity) - correction_line.discount_amount + move_record.amount_tax,
                    })

                # else:
                #     line.create(
                #             {
                #                 'move_id': self._context.get('active_id'),
                #                 'product_id': correction_line.product_id.id,
                #                 'name': correction_line.labell,
                #                 'price_unit': correction_line.price_unit,
                #                 'quantity': correction_line.quantity,
                #                 'discount_amount': correction_line.discount_amount,
                #             }
                #         )
        # for line in move_line:
        #     lines = []
        #     for correction_line in self.invoice_line_ids:
        #         val = {
        #                 'move_id': self._context.get('active_id'),
        #                 'product_id': correction_line.product_id.id,
        #                 'name': correction_line.labell,
        #                 'price_unit': correction_line.price_unit,
        #                 'quantity': correction_line.quantity,
        #                 'discount_amount': correction_line.discount_amount,
        #             }
        #         lines.append([0, 0, val])
        #     line.update({
        #         'invoice_line_ids': lines
        #     })