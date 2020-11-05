# -*- coding: utf-8 -*-
# Copyright 2019 ePayco.co
# - Reison Torres <reison.torres@gmail.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.tools import image_resize_images, image_resize_image, ustr

class PaymentIcon(models.Model):
    _name = 'epayco.payment.icon'
    _description = 'Payment Icon'

    name = fields.Char(string='Name')
    acquirer_ids = fields.Many2many('payment.acquirer', string="Acquirers", help="List of Acquirers supporting this payment icon.")
    image = fields.Binary(
        "Image", attachment=True,
        help="This field holds the image used for this payment icon, limited to 1024x1024px")

    image_payment_form = fields.Binary(
        "Image displayed on the payment form", attachment=True)

    @api.multi
    def create(self, vals):
        if 'image' in vals:
            image = ustr(vals['image'] or '').encode('utf-8')
            vals['image_payment_form'] = image_resize_image(image, size=(45, 30))
            vals['image'] = image_resize_image(image, size=(64, 64))
        return super(PaymentIcon, self).create(vals)

    @api.multi
    def write(self, vals):
        if 'image' in vals:
            image = ustr(vals['image'] or '').encode('utf-8')
            vals['image_payment_form'] = image_resize_image(image, size=(45, 30))
            vals['image'] = image_resize_image(image, size=(64, 64))
        return super(PaymentIcon, self).write(vals)
