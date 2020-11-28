# -*- coding: utf-8 -*-

import base64
from odoo import fields, models, api, _
from reportlab.graphics.barcode import createBarcodeDrawing
from odoo.exceptions import ValidationError, UserError
from odoo.addons.website.models.website import slug


class Product(models.Model):
    _inherit = "product.template"

    is_table_order = fields.Boolean(string="Is Table Order")


class restaurant_table(models.Model):
    _inherit = 'restaurant.table'

    barcode_url = fields.Char(compute='_compute_barcode_url', string='QR Encoded Message')
    qr_image = fields.Binary('Table Barcode')

    def get_image(self, value, width, hight, hr, code='QR'):
        options = {}
        if hr:
            options['humanReadable'] = True
        try:
            ret_val = createBarcodeDrawing(code, value=str(value), **options)
        except ValidationError as e:
            raise ValueError(e)
        return base64.encodestring(ret_val.asString('jpg'))

    def _compute_barcode_url(self):
        dom_name = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        for record in self:
            if record.floor_id and record.floor_id.pos_config_id:
                if dom_name:
                    domain_nm = dom_name
                else:
                    domain_nm = 'localhost:8069'
                record.barcode_url = "%s/table/%s" % (domain_nm, slug(record))
                image = self.get_image(record.barcode_url, code='QR', width=150, hight=150, hr=True)
                record.write({'qr_image': image})

    barcode_url = fields.Char(compute='_compute_barcode_url', string='QR Encoded Message')
    qr_image = fields.Binary('Table Barcode')


class PosOrder(models.Model):
    _inherit = "pos.order"
    is_table_order = fields.Boolean(string="Is Table Order")
    token = fields.Char(string='Token')

    @api.model
    def _order_fields(self, ui_order):
        res = super(PosOrder, self)._order_fields(ui_order)
        res.update({
            'is_table_order': ui_order.get('is_table_order') or False,
            'token': ui_order.get('token') or ''
            })
        return res

    @api.model
    def create(self, values):
        res = super(PosOrder, self).create(values)
        if res.is_table_order:
            table_os = self.env['table.order'].search([('token', '=', res.token)])
            if table_os:
                table_os.write({'state': 'done'})
                for line in table_os:
                    if line.state == 'confirm':
                        line.state = 'done'
        return res


class TableOrder(models.Model):
    _name = "table.order"
    _description = "Table Orders"
    _order = "id desc"
    _rec_name = "token"

    def _default_session(self):
        return self.env['pos.session'].sudo().search([('state', '=', 'opened'), ('user_id', '=', self.env.uid)], limit=1)

    def _default_pricelist(self):
        return self._default_session().config_id.pricelist_id

    active = fields.Boolean(default=True)
    token = fields.Char(string='Token Ref', readonly=True)
    company_id = fields.Many2one('res.company', string='Company', required=True, readonly=True, default=lambda self: self.env.user.company_id)
    table_id = fields.Many2one('restaurant.table', string='Table')
    state = fields.Selection(
        [('draft', 'New'), ('done', 'Done'), ('cancel', 'Cancel')], copy=False, default='draft')
    date_order = fields.Datetime(string='Order Date', readonly=True, index=True, default=fields.Datetime.now)
    amount_tax = fields.Float(compute='_compute_amount_all', string='Taxes', digits=0)
    amount_total = fields.Float(compute='_compute_amount_all', string='Total', digits=0)
    lines = fields.One2many('table.order.line', 'order_id', string='Order Lines', readonly=True, copy=True)
    is_table_order = fields.Boolean(string="Is Table Order", default=True)
    pricelist_id = fields.Many2one('product.pricelist', string='Pricelist', required=True, readonly=True, default=_default_pricelist)

    @api.model
    def _amount_line_tax(self, line, fiscal_position_id):
        taxes = line.tax_ids.filtered(lambda t: t.company_id.id == line.order_id.company_id.id)
        price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
        taxes = taxes.compute_all(price, line.order_id.pricelist_id.currency_id, line.qty, product=line.product_id.sudo(), partner=False)['taxes']
        return sum(tax.get('amount', 0.0) for tax in taxes)

    @api.depends('lines.price_subtotal_incl', 'lines.discount')
    def _compute_amount_all(self):
        for order in self:
            currency = order.pricelist_id.currency_id
            order.amount_tax = currency.round(sum(self._amount_line_tax(line, False) for line in order.lines))
            amount_untaxed = currency.round(sum(line.price_subtotal for line in order.lines))
            order.amount_total = order.amount_tax + amount_untaxed

    @api.model
    def get_table_order_lists(self, table_id=None):
        domain = [('active', '=', True), ('is_table_order', '=', True), ('state', '=', 'draft')]
        if table_id:
            domain += [('table_id', '=', table_id)]
        orders = self.search(domain)
        orders_data = []
        for rec in orders:
            data = {
            }
            order_lines = []
            data.update({
                 'id': rec.id,
                 'token': rec.token,
                 'is_table_order': rec.is_table_order,
                 'table_id': rec.table_id.id,
                 'table_name': rec.table_id.name,
                 'state': rec.state,
                 'date_order': rec.date_order,
                 'amount_tax': rec.amount_tax,
                 'amount_total': rec.amount_total,
                 'line': []
                })
            for line in rec.lines:
                if line.state != 'draft':
                    order_lines += [{'id': line.id, 'state': line.state, 'product_id': line.product_id.id, 'name': line.product_id.name, 'qty': line.qty, 'price': line.price_subtotal_incl, 'note': line.note}]
            if order_lines:
                data.update({
                    'line': order_lines
                    })
            orders_data += [data]
        return orders_data

    def get_table_order_select_lists(self):
        data_line = []
        data = {
            'token': None,
            'is_table_order': None,
            'line': []
        }
        for rec in self:
            data.update({
                 'id': rec.id,
                 'token': rec.token,
                 'is_table_order': rec.is_table_order,
                 'table_id': rec.table_id.id
                })
            for line in rec.lines:
                if line.state != 'draft':
                    data_line += [{'id': line.id, 'product_id': line.product_id.id, 'qty': line.qty, 'state': line.state, 'linked_line_id': line.linked_line_id.id, 'note': line.note}]
        if data_line:
            data.update({
                'line': data_line
                })
        return data

    @api.model
    def get_list_of_table_order(self):
        tables_ids = self.search([('state', '=', 'draft')]).mapped('table_id').ids
        tables_conts = []
        if tables_ids:
            for tid in tables_ids:
                cont = self.search_count([('state', '=', 'draft'), ('table_id', '=', tid)])
                tables_conts += [{'table_id': tid, 'ocount': cont}]
        return tables_conts

    @api.model
    def change_table_accept_all_order(self, order_id):
        if order_id:
            order_id = self.browse(int(order_id))
            line_ids = order_id.lines.filtered(lambda l: l.state in ['draft', 'confirm'])
            line_ids.write({'state': 'ordered'})
        return True

    @api.model
    def change_table_cance_all_order(self, order_id):
        if order_id:
            order_id = self.browse(int(order_id))
            order_id.lines.write({'state': 'cancel'})
            order_id.write({'state': 'cancel'})
        return True


class TableOrderLine(models.Model):
    _name = 'table.order.line'
    _description = "Lines of Table Orders"
    _rec_name = "product_id"

    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.user.company_id)
    product_id = fields.Many2one('product.product', string='Product', domain=[('sale_ok', '=', True)], required=True, change_default=True)
    price_unit = fields.Float(string='Unit Price', digits=0)
    qty = fields.Float('Quantity', default=1)
    price_subtotal = fields.Float(compute='_compute_amount_line_all', digits=0, string='Subtotal w/o Tax')
    price_subtotal_incl = fields.Float(compute='_compute_amount_line_all', digits=0, string='Subtotal')
    discount = fields.Float(string='Discount (%)', digits=0, default=0.0)
    order_id = fields.Many2one('table.order', string='Order Ref', ondelete='cascade')
    tax_ids = fields.Many2many('account.tax', string='Taxes', readonly=True)
    state = fields.Selection(
        [('draft', 'New'), ('confirm', 'Confirm'),
         ('ordered', 'Ordered'), ('prepared', 'Prepared'),
         ('served', 'Served'), ('done', 'Done'), ('cancel', 'Canceled')], copy=False, default='draft')
    linked_line_id = fields.Many2one(
        'table.order.line', string='Linked Order Line', domain="[('order_id', '!=', order_id)]",
        ondelete='cascade')
    modifier_line_ids = fields.One2many('table.order.line', 'linked_line_id', string='Modifier Linked')
    note = fields.Char('Note added by the Customer.')

    @api.depends('price_unit', 'tax_ids', 'qty', 'discount', 'product_id')
    def _compute_amount_line_all(self):
        for line in self:
            # fpos = line.order_id.fiscal_position_id
            tax_ids_after_fiscal_position = line.tax_ids
            price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            taxes = tax_ids_after_fiscal_position.compute_all(price, line.order_id.pricelist_id.currency_id, line.qty, product=line.product_id.sudo(), partner=False)
            line.update({
                'price_subtotal_incl': taxes['total_included'],
                'price_subtotal': taxes['total_excluded'],
            })

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id.sudo():
            if not self.order_id.pricelist_id.sudo():
                raise UserError(
                    _('You have to select a pricelist in the sale form !\n'
                      'Please set one before choosing a product.'))
            price = self.order_id.pricelist_id.sudo().get_product_price(
                self.product_id.sudo(), self.qty or 1.0, False)
            self._onchange_qty()
            self.tax_ids = self.product_id.sudo().taxes_id.filtered(lambda r: not self.company_id or r.company_id == self.company_id)
            tax_ids_after_fiscal_position = self.tax_ids
            self.price_unit = self.env['account.tax']._fix_tax_included_price_company(price, self.product_id.sudo().taxes_id, tax_ids_after_fiscal_position, self.company_id)

    @api.onchange('qty', 'discount', 'price_unit', 'tax_ids')
    def _onchange_qty(self):
        if self.product_id.sudo():
            if not self.order_id.pricelist_id:
                raise UserError(_('You have to select a pricelist in the sale form !'))
            price = self.price_unit * (1 - (self.discount or 0.0) / 100.0)
            self.price_subtotal = self.price_subtotal_incl = price * self.qty
            if (self.product_id.sudo().taxes_id):
                taxes = self.product_id.sudo().taxes_id.compute_all(price, self.order_id.pricelist_id.sudo().currency_id, self.qty, product=self.product_id.sudo(), partner=False)
                self.price_subtotal = taxes['total_excluded']
                self.price_subtotal_incl = taxes['total_included']

    @api.model
    def get_table_order_line_state_ordered(self, lines=None):
        if lines:
            tlines = self.browse(lines)
            for tline in tlines:
                tline.state = 'ordered'
        return True

    @api.model
    def change_table_order_state(self, line_id, change_state):
        if line_id and change_state:
            line_id = self.browse(int(line_id))
            line_id.write({'state': change_state})
            notifications = []
            table_order_line_message = 'Yes Got it'
            vals = {'user_id': self.env.uid,
                    'table_order_line_message': table_order_line_message,
                    }
            notifications.append([(self.env.cr.dbname, 'table.order.line', self.env.uid), {'table_order_line_message': vals}])
            self.env['bus.bus'].sendmany(notifications)


class Ir_Sequence(models.Model):
    _inherit = 'ir.sequence'

    @api.model
    def _cron_generate_seuance_table(self):
        sqno = self.env.ref('qrcode_table.seq_web_table_order')
        if sqno:
            sqno.write({'number_next': 1})