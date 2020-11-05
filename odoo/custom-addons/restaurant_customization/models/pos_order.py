# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.
from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError
import psycopg2
from functools import partial
from odoo.tools import float_is_zero
import logging
_logger = logging.getLogger(__name__)


order_status = {
    'in_queue': 'Queue',
    'in_progress': 'In Progress',
    'is_done': 'Done',
    'cancel': 'Cancel'
}


class PosOrder(models.Model):
    _inherit = "pos.order"

    table_name = fields.Char(related='table_id.name',
                             readonly=True, string='Table Name')
    order_line_status = fields.Char(String='Orderline Status')
    product_details = fields.One2many(
        'pos.order.line', 'order_id',
        compute='get_5_pos_order_line',
        string='Product Detials')
    load_more = fields.Boolean(string='load_more')
    is_send_to_kitchen = fields.Boolean(string='Is Send to Kitchen?')
    is_show_in_kitchen = fields.Boolean(
        readonly=True, string='Is show in Kitchen')
    backend_payment = fields.Boolean('Backend Payment', default=False)

    @api.multi
    def _get_is_cashier(self):
        if self._uid:
            user = self.env['res.users'].browse(self._uid)
            for order in self:
                order.is_cashier = user.is_cashier

    delivery_boy = fields.Many2one('res.users')
    order_type = fields.Selection(
        [('dine_in', "Dine In"),
         ('take_away', "Take Away"),
         ('delivery', "Delivery")],
        string="Order Type",
        default="indoor")
    chair_count = fields.Integer(string='Chairs')
    is_cashier = fields.Boolean('Is Cashier', compute='_get_is_cashier')

    @api.model
    def get_state(self, order):
        order_ref = self.sudo().search([('pos_reference', '=', order)])
        if order_ref:
            return order_ref.state

    @api.model
    def update_chair(self, order, value):
        order_ref = self.sudo().search([('pos_reference', '=', order)])
        if order_ref and order_ref.state == 'draft':
            order_ref.write({'chair_count': value})

    @api.model
    def _order_fields(self, ui_order):
        order_fields = super(PosOrder, self)._order_fields(ui_order)
        order_fields['order_type'] = ui_order.get('order_type', False)
        order_fields['delivery_boy'] = ui_order.get('delivery_boy', False)
        order_fields['chair_count'] = ui_order.get('chair_count', 0)
        return order_fields

    @api.model
    def create(self, vals):
        if (not vals.get('order_type')):
            vals.update({
                'order_type': 'dine_in'
            })
        return super(PosOrder, self).create(vals)
    
    @api.model
    def get_order(self, line):
        if line:
            line_id = self.env['pos.order.line'].sudo().search(
                [('id', '=', line)])
            if line_id:
                chair_count = line_id.order_id.chair_count
                return chair_count

    @api.model
    def check_paid_order(self, order):
        order_ref = self.sudo().search([('pos_reference', '=', order)])
        if order_ref and order_ref.state == 'paid':
            return True
        else:
            return False

    @api.model
    def check_order(self, order):
        order_ref = self.sudo().search([('pos_reference', '=', order)])
        if order_ref.state == 'paid':
            return True
        else:
            return False

    @api.model
    def check_payment(self, order):
        order_ref = self.sudo().search([('pos_reference', '=', order)])
        if order_ref.backend_payment:
            return True
        else:
            return False

    @api.model
    def compute_status(self, reference):
        values = {}
        order_ref = self.sudo().search([('pos_reference', '=', reference)])
        for ref in order_ref:
            lines = []
            for line in ref.lines:
                if line.is_show_in_kitchen:
                    lines.append((line.product_id.display_name,
                                  order_status.get(line.kitchecn_order_state)))
            values.update({ref.pos_reference: lines})
        return values

    @api.model
    def splitbill_payment(self, order, line, qty):
        pos_order = self.sudo().search([('pos_reference', '=', order)])
        if line:
            line_id = self.env['pos.order.line'].sudo().search(
                [('id', '=', line)])
            if not pos_order == line_id.order_id:
                if qty == line_id.qty:
                    line_id.unlink()
                else:
                    updated_qty = line_id.qty - qty
                    line_id.write({'qty': updated_qty})
        else:
            return pos_order.id

    @api.model
    def update_orderlines(self, order):
        lines = []
        pos_order = self.sudo().search([('pos_reference', '=', order)])
        if pos_order:
            for line in pos_order.lines:
                lines.append(line.id)
            return lines

    @api.multi
    @api.depends('lines.order_id')
    def get_5_pos_order_line(self):
        for rec in self:
            if rec.load_more:
                rec.product_details = self.env['pos.order.line'].search(
                    [('order_id', '=', rec.id)]).ids
            else:
                rec.product_details = self.env['pos.order.line'].search(
                    [('order_id', '=', rec.id)], limit=3).ids

    @api.multi
    def show_all_product(self):
        for rec in self:
            if rec.load_more:
                rec.load_more = False
            else:
                rec.load_more = True

    @api.model
    def _process_order(self, pos_order):
        prec_acc = self.env['decimal.precision'].precision_get('Account')
        pos_session = self.env['pos.session'].browse(
            pos_order['pos_session_id'])

        if pos_session.state == 'closing_control' or \
                pos_session.state == 'closed':
            pos_order['pos_session_id'] = self._get_valid_session(pos_order).id
        pos_order_obj = self.search(
            [('pos_reference', '=', pos_order['name'])])
        order = False
        if pos_order_obj:
            order = pos_order_obj
        else:
            order = self.create(self._order_fields(pos_order))
        journal_ids = set()
        for payments in pos_order['statement_ids']:
            if not float_is_zero(payments[2]['amount'],
                                 precision_digits=prec_acc):
                order.add_payment(self._payment_fields(payments[2]))
            journal_ids.add(payments[2]['journal_id'])

        if pos_session.sequence_number <= pos_order['sequence_number']:
            pos_session.write(
                {'sequence_number': pos_order['sequence_number'] + 1})
            pos_session.refresh()

        if not float_is_zero(pos_order['amount_return'], prec_acc):
            cash_journal_id = pos_session.cash_journal_id.id
            if not cash_journal_id:
                # Select for change one of the cash journals used in this
                # payment
                cash_journal = self.env['account.journal'].search([
                    ('type', '=', 'cash'),
                    ('id', 'in', list(journal_ids)),
                ], limit=1)
                if not cash_journal:
                    ''' If none, select for change one of the cash journals
                    of the POS This is used for example when a customer pays
                    by credit card an amount higher than total amount of the
                    order and gets cash back
                    '''
                    cash_journal = [
                        statement.journal_id
                        for statement in pos_session.statement_ids
                        if statement.journal_id.type == 'cash']
                    if not cash_journal:
                        raise UserError(
                            _("No cash statement found for this session."
                              "Unable to record returned cash."))
                cash_journal_id = cash_journal[0].id
            order.add_payment({
                'amount': -pos_order['amount_return'],
                'payment_date': fields.Datetime.now(),
                'payment_name': _('return'),
                'journal': cash_journal_id,
            })
        return order

    @api.multi
    def get_stage_by_sequence(self, seq):
        return self.env['pos.order.line.state'].search([
            ('sequence', '=', seq)]).id

    @api.model
    def check_update_qty_send_to_kitchen(self, orders, is_kitchen=False):
        qty_update = False
        note_update = False
        discount_update = False
        price_update = False
        submitted_references = [o['data']['name'] for o in orders]
        pos_order = self.search(
            [('pos_reference', 'in', submitted_references)])
        existing_orders = pos_order.read(['pos_reference'])
        existing_references = set([o['pos_reference']
                                   for o in existing_orders])
        order_to_save_line = [
            o for o in orders if o['data']['name'] in existing_references]

        for tmp_order in order_to_save_line:
            order_tmp = tmp_order['data']
            if is_kitchen:
                process_line = partial(
                    self.env['pos.order.line']._order_line_fields)
                order_lines = [process_line(
                    l) for l in order_tmp['lines']] \
                    if order_tmp['lines'] else False
                count_note = 0
                count_qty = 0
                for line in order_lines:
                    if line[2].get('line_id'):
                        pos_order_line = self.env['pos.order.line'].browse(
                            line[2].get('line_id'))
                        if pos_order_line.note != line[2].get('note'):
                            count_note += 1
                            if count_note == 1:
                                note_update = True
                            pos_order_line.note = line[2].get('note')
                        if pos_order_line.price_unit != line[2].get(
                                'price_unit'):
                            price_update = True
                            pos_order_line.price_unit = line[2].get(
                                'price_unit')
                        if pos_order_line.discount != line[2].get('discount'):
                            discount_update = True
                            pos_order_line.discount = line[2].get('discount')
                        if pos_order_line.qty != line[2].get('qty'):
                            count_qty += 1
                            if count_qty == 1:
                                qty_update = True
                            pos_order_line.qty = line[2].get('qty')
                return {
                    'is_note_update': note_update,
                    'is_qty_update': qty_update,
                    'is_discount_update': discount_update,
                    'is_price_update': price_update
                }

    @api.model
    def create_from_ui(self, orders, is_kitchen=False):
        # Keep only new orders
        submitted_references = [o['data']['name'] for o in orders]
        pos_order = self.search(
            [('pos_reference', 'in', submitted_references)])
        existing_orders = pos_order.read(['pos_reference'])
        existing_references = set([o['pos_reference']
                                   for o in existing_orders])
        orders_to_save = [o for o in orders if o['data']
                          ['name'] not in existing_references]
        order_to_save_line = [
            o for o in orders if o['data']['name'] in existing_references]
        process_line = partial(self.env['pos.order.line']._order_line_fields)
        order_ids = []
        line_id = []
        check_update_qty_note = {}
        qty_update = False
        note_update = False
        discount_update = False
        price_update = False
        for tmp_order in order_to_save_line:
            order_tmp = tmp_order['data']
            order_lines = [process_line(
                l) for l in order_tmp['lines']] if order_tmp[
                'lines'] else False
            if order_tmp.get('partner_id'):
                pos_order.write({'partner_id': order_tmp.get('partner_id')})
            if order_tmp.get('delivery_boy'):
                pos_order.write(
                    {'delivery_boy': order_tmp.get('delivery_boy')})
            if is_kitchen:
                if any(not line[2].get('line_id') for line in order_lines):
                    for line in order_lines:
                        if isinstance(line[2].get('line_id'), unicode):
                            if order_tmp.get('partner_id'):
                                pos_order.write(
                                    {'partner_id':
                                     order_tmp.get('partner_id')})
                            line[2]['order_id'] = pos_order.id
                            line = self.env['pos.order.line'].create(line[2])
                            order_ids.append(pos_order.id)
                            line_id.append(pos_order.lines.ids)
                for line in order_lines:
                    if line[2].get('line_id'):
                        pos_order_line = self.env['pos.order.line'].browse(
                            line[2].get('line_id'))
                        if pos_order_line.note != line[2].get('note'):
                            note_update = True
                            pos_order_line.note = line[2].get('note')
                        if pos_order_line.price_unit != line[2].get(
                                'price_unit'):
                            price_update = True
                            pos_order_line.price_unit = line[2].get(
                                'price_unit')
                        if pos_order_line.discount != line[2].get('discount'):
                            discount_update = True
                            pos_order_line.discount = line[2].get('discount')
                        if pos_order_line.qty != line[2].get('qty'):
                            qty_update = True
                            pos_order_line.qty = line[2].get('qty')
                check_update_qty_note.update({
                    'is_note_update': note_update,
                    'is_qty_update': qty_update,
                    'is_discount_update': discount_update,
                    'is_price_update': price_update
                })
            else:
                if any(not line[2].get('line_id') for line in order_lines):
                    for line in order_lines:
                        if not line[2].get('line_id'):
                            if order_tmp.get('partner_id'):
                                pos_order.write(
                                    {'partner_id': order_tmp.get(
                                        'partner_id')})
                            line[2]['order_id'] = pos_order.id
                            line = self.env['pos.order.line'].create(line[2])
                            order_ids.append(pos_order.id)
                            line_id.append(pos_order.lines.ids)
                to_invoice = tmp_order['to_invoice']
                order = tmp_order['data']
                if to_invoice:
                    self._match_payment_to_invoice(order)
                pos_order = self._process_order(order)
                order_ids.append(pos_order.id)
                line_id.append(pos_order.lines.ids)

                try:
                    pos_order.action_pos_order_paid()
                except psycopg2.OperationalError:
                    ''' do not hide transactional errors,
                    the order(s) won't be saved!'''
                    raise
                except Exception as e:
                    _logger.error(
                        'Could not fully process the POS Order: %s',
                        tools.ustr(e))

                if to_invoice:
                    pos_order.action_pos_order_invoice()
                    pos_order.invoice_id.sudo().action_invoice_open()
                    pos_order.account_move = pos_order.invoice_id.move_id

        for tmp_order in orders_to_save:
            to_invoice = False
            if not is_kitchen:
                to_invoice = tmp_order['to_invoice']
            order = tmp_order['data']
            if to_invoice:
                self._match_payment_to_invoice(order)
            pos_order = self._process_order(order)
            order_ids.append(pos_order.id)
            line_id.append(pos_order.lines.ids)

            try:
                if not is_kitchen:
                    pos_order.action_pos_order_paid()
            except psycopg2.OperationalError:
                ''' do not hide transactional errors, the order(s)
                    won't be saved!
                '''
                raise
            except Exception as e:
                _logger.error(
                    'Could not fully process the POS Order: %s', tools.ustr(e))

            if to_invoice:
                pos_order.action_pos_order_invoice()
                pos_order.invoice_id.sudo().action_invoice_open()
                pos_order.account_move = pos_order.invoice_id.move_id
        if is_kitchen:
            return [order_ids, line_id, check_update_qty_note]
        else:
            return order_ids

    @api.model
    def check_order_line_state_from_pos(self, order, order_line):
        if order_line:
            order_line = self.env['pos.order.line'].browse(order_line)
            if order_line.kitchecn_order_state != 'in_queue':
                return order_line.kitchecn_order_state

    # cancel pos order
    @api.model
    def cancel_pos_order(self, pos_reference):
        pos_order = self.sudo().search([('pos_reference', '=', pos_reference)])
        if pos_order:
            if pos_order.state == 'draft':
                pos_order.state = 'cancel'
                pos_order_line = self.env['pos.order.line'].search(
                    [('order_id', '=', pos_order.id)])
                pos_order_line.write({'kitchecn_order_state': 'cancel'})
                return {'sucess': True}
            else:
                return {'sucess': False}
        else:
            return {'sucess': False}


class PosOrderLine(models.Model):
    _inherit = "pos.order.line"

    kitchecn_order_state = fields.Selection([('in_queue', 'In Queue'),
                                             ('in_progress', 'In Progress'), (
        'is_done', 'Is Done'), ('cancel', 'Cancel')],
        string="Kitchen order state")
    order_line_state_id = fields.Many2one(
        'pos.order.line.state', string='Pos Order line state',
        group_expand='_read_group_stage_ids')
    state_sequence = fields.Integer(
        related='order_line_state_id.sequence', readonly='True')
    property_description = fields.Text(String="Property Description")
    order_name = fields.Char(
        related='order_id.pos_reference', readonly=True, string='Order Name')
    partner_id = fields.Char(
        related='order_id.partner_id.name', readonly=True, string='Customer')
    table = fields.Char(related='order_id.table_name',
                        readonly=True, string='Table')
    is_show_in_kitchen = fields.Boolean(
        readonly=True, string='Is show in Kitchen')
    note = fields.Char(string='Note')
    line_id = fields.Integer()
    order_data_id = fields.Many2one(related='order_id')
    discount_type = fields.Many2one(
        'pos.discount.type', string='Discount Type')

    @api.model
    def create(self, vals):
        pos_order_line = super(PosOrderLine, self).create(vals)
        pos_order_line.is_show_in_kitchen = \
            pos_order_line.product_id.product_tmpl_id.pos_categ_id. \
            is_show_in_kitchen
        pos_order_line.note = vals.get('note')
        if pos_order_line.is_show_in_kitchen:
            pos_order_line.order_id.is_show_in_kitchen = True
        return pos_order_line

    # cancel order line
    @api.model
    def cancel_order_line(self, line):
        orderline = self.sudo().search([('id', '=', line)])
        if orderline:
            orderline.unlink()


class PosCategory(models.Model):
    _inherit = "pos.category"

    is_show_in_kitchen = fields.Boolean(string='Is Show in Kitchen')


class PosSession(models.Model):
    _inherit = "pos.session"

    def _confirm_orders(self):
        for session in self:
            company_id = session.config_id.journal_id.company_id.id
            orders = session.order_ids.filtered(
                lambda order: order.state == 'paid')
            journal_id = self.env['ir.config_parameter'].sudo().get_param(
                'pos.closing.journal_id_%s' % company_id,
                default=session.config_id.journal_id.id)
            if not journal_id:
                raise UserError(_("You have to set a "
                                  "Sale Journal for the POS:%s") % (
                    session.config_id.name,))

            move = self.env['pos.order'].with_context(
                force_company=company_id)._create_account_move(
                session.start_at, session.name, int(journal_id), company_id)
            orders.with_context(
                force_company=company_id)._create_account_move_line(
                session, move)
            for order in session.order_ids.filtered(
                    lambda o: o.state not in ['done', 'invoiced']):
                if not order.lines:
                    order.state = 'cancel'
                if order.state in 'cancel':
                    continue
                if order.state not in ('paid'):
                    raise UserError(
                        _("You cannot confirm all orders of this "
                          "session, because they have not the 'paid' status"))
                order.action_pos_order_done()
            orders = session.order_ids.filtered(
                lambda order: order.state in ['invoiced', 'done'])
            orders.sudo()._reconcile_payments()


class pos_order_line_state(models.Model):
    _name = "pos.order.line.state"

    name = fields.Char('Name')
    sequence = fields.Integer('Sequence')


class PosConfig(models.Model):
    _inherit = "pos.config"

    floor_ids = fields.Many2many(
        'restaurant.floor',
        'pos_config_floor_rel', 'pos_config_id', 'floor_id')
