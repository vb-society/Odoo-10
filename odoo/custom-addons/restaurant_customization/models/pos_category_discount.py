# -*- coding: utf-8 -*-
from odoo import fields, models


class PosCategoryDsicount(models.Model):
    _name = "pos.category.discount"
    _description = "Public Category"
    _rec_name = 'pos_category_id'

    pos_category_id = fields.Many2one(
        'pos.category', required=True, string='Parent Category', index=True)
    is_allow = fields.Boolean(string='Active')
    product_id = fields.Many2one('product.product',
                                 required=True,
                                 string='Product',
                                 domain="[('type', '=', 'service'),\
                                 ('available_in_pos','=', True)]")


class PosDiscountType(models.Model):
    _name = "pos.discount.type"

    _sql_constraints = [
        ('uniq_name', 'unique(name)', 'Discount Type already exists !'),
    ]

    name = fields.Char('Discount Type', required=True)
