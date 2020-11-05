# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request


class WebsiteOrderScreen(http.Controller):

    @http.route(['/orderscreen', '/orderscreen/page/<int:page>'],
                type='http', auth="public", website=True)
    def order_screen(self, page=0, **post):
        order_count = request.env['pos.order'].sudo(
        ).search_count([('state', '=', 'draft')])
        url = '/orderscreen'
        pager = request.website.pager(
            url=url, total=order_count, page=page, step=6, scope=7)
        pos_orders = request.env['pos.order'].sudo().search(
            [('state', '=', 'draft')], offset=pager['offset'], limit=6)
        return request.render("restaurant_customization.orderscreen",
                              {"orders": pos_orders, 'pager': pager})

    @http.route(['/kitchenscreen', '/kitchenscreen/<model("pos.order"):order>',
                 '/kitchenscreen/page/<int:page>',
                 '/kitchenscreen/<model("pos.order"):order>/page/<int:page>'],
                type='http', auth="public", website=True)
    def kitchen_screen(self, page=0, order=None, **post):
        if order:
            domain = [('order_id.state', '=', 'draft'),
                      ('order_id', '=', order.id)]
            url = '/kitchenscreen/%s' % order.id
        else:
            domain = [('order_id.state', '=', 'draft')]
            url = '/kitchenscreen'
        lines = request.env['pos.order.line'].sudo().search(domain)
        line_count = len(lines)
        pager = request.website.pager(
            url=url, total=line_count, page=page, step=9, scope=7)
        pos_lines = request.env['pos.order.line'].sudo().search(
            domain, offset=pager['offset'], limit=9)
        return request.render("restaurant_customization.kitchenscreen",
                              {"lines": pos_lines, 'pager': pager})

    @http.route(['/kitchen/status'], type='json', auth="public", website=True)
    def kitchen_status(self, **kwargs):
        value = kwargs.get('val')
        line_id = value.get('line_id', False)
        status = value.get('status', False)
        line = request.env['pos.order.line'].sudo().search(
            [('id', '=', line_id)])
        if status == 'progress':
            line.write({'kitchecn_order_state': 'in_progress'})
        if status == 'done':
            line.write({'kitchecn_order_state': 'is_done'})
        return status
