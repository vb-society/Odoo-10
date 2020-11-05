# -*- coding: utf-8 -*-
from odoo import api, fields, models


class Users(models.Model):
    _inherit = 'res.users'

    allow_outdoor_order = fields.Boolean(
        string='Allow Outdoor Orders Take Away',
        help='Enables Outdoor Orders\n Take Away')
    allow_outdoor_order_delivery = fields.Boolean(
        string='Allow Outdoor Orders Delivery',
        help='Enables Outdoor Orders\n Delivery')
    is_delivery_boy = fields.Boolean(string="Delivery Boy")
    is_waiter = fields.Boolean(string="Waiter")
    is_cashier = fields.Boolean(string="Cashier")
    allow_customer_recipt = fields.Boolean(
        string='Allow Cus',
        help='Enables Outdoor Orders\n1-Take Away\n2-Delivery')

    @api.onchange('is_waiter', 'is_cashier')
    def onchange_is_waiter(self):
        if self.is_waiter and not self.is_cashier:
            self.allow_outdoor_order = True
            self.allow_outdoor_order_delivery = False
        elif not self.is_waiter and self.is_cashier:
            self.allow_outdoor_order = True
            self.allow_outdoor_order_delivery = True
        elif not self.is_waiter and not self.is_cashier:
            self.allow_outdoor_order = False
            self.allow_outdoor_order_delivery = False

    @api.model
    def create(self, values):
        user = super(Users, self).create(values)
        group_waiter = self.env.ref('restaurant_customization.group_pos_waiter', False)
        if 'is_waiter' in values:
            if values.get('is_waiter', False) and not user.has_group(
                    'point_of_sale.group_pos_manager'):
                user.groups_id = [(4, group_waiter.id)]
        return user

    @api.multi
    def write(self, values):
        group_waiter = self.env.ref('restaurant_customization.group_pos_waiter', False)
        res = super(Users, self).write(values)
        if 'is_waiter' in values and not self.has_group(
                'point_of_sale.group_pos_manager'):
            if values.get('is_waiter', False):
                values.update({'groups_id': [(4, group_waiter.id)]})
            else:
                values.update({'groups_id': [(3, group_waiter.id)]})
        elif self.is_waiter:
            if not self.has_group('point_of_sale.group_pos_manager'):
                values.update({'groups_id': [(4, group_waiter.id)]})
            else:
                values.update({'groups_id': [(3, group_waiter.id)]})
        res = super(Users, self).write(values)
        return res
