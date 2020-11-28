# -*- coding: utf-8 -*-
# Copyright 2018, AUTHOR(S)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models, api


class POSmodifiers(models.Model):
    _name = 'pos.modifiers'
    _description = 'POS Modifiers'

    name = fields.Many2one('product.product', string='Name', required=True)
    desc = fields.Char(string='Description')
    price = fields.Float(string='Price')
    pos_categoryid = fields.Many2one('pos.category')


class Productmodifiers(models.Model):
    _name = 'product.modifiers'
    _description = 'Product Modifiers'

    name = fields.Many2one('product.product', string='Name', required=True)
    desc = fields.Char(string='Description')
    price = fields.Float(string='Price')
    product_id = fields.Many2one('product.template')


class ModifiersGroups(models.Model):
    _name = 'modifiers.groups'

    name = fields.Char(string='Toppings', required=True)
    modifier_ids = fields.Many2many('product.template', 'group_id', 'tmpl_id', string="Modifiers", domain=[('use_as_modifier', '=', True)])


class PosCateory(models.Model):
    _inherit = 'pos.category'

    is_modifier = fields.Boolean('Is Modifier Category?')
    modifier_ids = fields.One2many('pos.modifiers', 'pos_categoryid', string='Modifiers')


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    is_modifier = fields.Boolean('Is Modifier Product?')
    use_as_modifier = fields.Boolean('Use as a Modifiers?')
    modifier_ids = fields.One2many('product.modifiers', 'product_id', string='Modifiers')
    modifier_grp_ids = fields.Many2many('modifiers.groups', string="Modifiers Groups")

    # @api.onchange('pos_categ_id')
    # def _onchange_pos_categ_id(self):
    #     vals = {}
    #     if self.pos_categ_id.is_modifier:
    #         self.is_modifier = True
    #     if self.pos_categ_id.modifier_ids:
    #         for line in self.pos_categ_id.modifier_ids:
    #             vals = {
    #                 'name': line.name,
    #                 'desc': line.desc,
    #                 'price': line.price,
    #                 'product_id': self.env.context.get('params').get('id')
    #                 }
    #             self.modifier_ids = [(0, 0, vals)]
    #     else:
    #         self.modifier_ids = []

    def get_modifier(self):
        ProductProduct = self.env['product.product']
        for template in self:
            template.modifier_ids.unlink()
            modifier_ids = []
            # attribute_ids = template.attribute_line_ids.filtered(
            #     lambda x: x.attribute_id.is_modifier).mapped('attribute_id')
            #attribute_value_ids = template.attribute_line_ids.mapped('value_ids').filtered(lambda x: x.attribute_id.is_modifier)
            templates = template.modifier_grp_ids.mapped('modifier_ids')
            domain = [
                ('product_tmpl_id', 'in', templates.ids),
                # ('attribute_line_ids.attribute_id', 'in', attribute_ids.ids)
                # ('attribute_value_ids', 'in', attribute_value_ids.ids)
            ]
            for variant in ProductProduct.search(domain):
                modifier_ids.append(
                    (0, 0, {'name': variant.id, 'desc': variant.name, 'price': variant.lst_price}))
            template.modifier_ids = modifier_ids


class ProductAttribute(models.Model):
    _inherit = 'product.attribute'

    is_modifier = fields.Boolean('Is Modifier Attribute')
