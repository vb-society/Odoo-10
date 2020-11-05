# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
from odoo.addons.bus.controllers.main import BusController
from odoo.http import request
import json

CHANNEL_NM_SYNCH = "pos.order.synch"
CHANNEL_NM_SYNCH_STATUS = "pos.order.synch.status"


class PosOrderSynch(models.Model):
    _name = 'pos.order.synch'
    _description = 'Order Synch'
    _display_name = 'order_uid'

    order_uid = fields.Char(string="Order", index=True)
    order_data = fields.Text('Order JSON format')
    write_date = fields.Datetime('Last Updated', default=fields.Datetime.now)
    pos_id = fields.Many2one('pos.session', string='POS')

    @api.model
    def update_orders(self, action, data_dict):
        if not action:
            return False
        json_data = json.loads(data_dict)
        remove_line_flag = False
        notifications = []
        for row in json_data:
            uid = row.get('uid')
            order_count = self.search_count([('order_uid', 'ilike', uid)])
            if order_count:
                action = 'update'
                remove_line_flag = action == 'remove_line'
            if action == "add":
                if not row.get('lines', []):
                    continue
                order = self.create({
                    'order_data': json.dumps(row),
                    'order_uid': uid,
                })
                notifications.append([
                    (self._cr.dbname, 'pos.order.synch'), {
                        'order_uid': uid,
                        'order_data': order.order_data,
                        'order_status': 'new_order'
                    }
                ])
            elif action == "update":
                orders = self.search([('order_uid', 'ilike', uid)])
                for order in orders:
                    if remove_line_flag:
                        row['lines'] = []

                    order.write({
                        'order_data': json.dumps(row),
                        'write_date': fields.Datetime.now()
                    })
                    notifications.append([
                        (self._cr.dbname, 'pos.order.synch'), {
                            'order_uid': order.order_uid,
                            'order_data': order.order_data,
                            'order_status': 'update_order'
                        }
                    ])
        if notifications:
            self.env['bus.bus'].sendmany(notifications)
        return True

    @api.model
    def synch_all(self):
        result = []
        for order in self.search([], order="create_date"):
            result.append({
                'order_data': order.order_data,
                'order_uid': order.order_uid,
            })
        return result

    @api.model
    def remove_order(self, order_ids):
        unique_list = list(set(filter(lambda a: a, order_ids)))
        recs = self.search([('order_uid', 'in', unique_list)])
        recs.unlink()
        self.env['bus.bus'].sendmany([
            [(self._cr.dbname, 'pos.order.synch'), {
                'order_uid': order_ids[0], 'order_data': {},
                'order_status': 'remove_order'
            }]
        ])
        return recs.ids

    @api.model
    def orderline_state(self, uid, line_id, state):
        orders = self.search([('order_uid', 'ilike', uid)])
        for order in orders:
            data = json.loads(order.order_data)
            for line in data.get('lines', []):
                if line['id'] == line_id:
                    line['state'] = state

            order.write({'order_data': json.dumps(data), 'write_date': fields.Datetime.now()})
        self.env['bus.bus'].sendmany([[(self._cr.dbname, 'pos.order.synch'), {
                        'order_uid': orders.order_uid, 'order_data': orders.order_data,
                        'order_status': 'orderline_state'}]])
        return True


class PosSessionBusController(BusController):

    def _poll(self, dbname, channels, last, options):
        if request.session.uid:
            channels = list(channels)
            channels.append((request.db, 'pos.order.synch'))
        return super(PosSessionBusController, self)._poll(dbname, channels, last, options)
