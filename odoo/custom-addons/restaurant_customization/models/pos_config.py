from odoo import fields, models


class PosConfig(models.Model):
    _inherit = 'pos.config'

    category_discount = fields.Boolean(
        string='Allow Product Category wise Discounts',
        help='Allow the cashier to give discounts by category Product.')
    pos_category_discount_ids = fields.Many2many('pos.category.discount',
                                                 'pos_config_pos_categ_disc',
                                                 'pos_config_id',
                                                 'pos_categ_disc_id',
                                                 string='Pos Category'
                                                 'Discount',
                                                 domain=[('is_allow',
                                                          '=', True)])
    discount_product_category = fields.Float(
        string='Discount Percentage', default=10,
        help='The default discount percentage')
