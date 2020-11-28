odoo.define('qrcode_table.pos', function(require) {
    "use strict";
    require('bus.BusService');
    var session = require('web.session');
    var core = require('web.core');
    var screens = require('point_of_sale.screens');
    var gui = require('point_of_sale.gui');
    var models = require('point_of_sale.models');
    var rpc = require('web.rpc');
    var floors = require('pos_restaurant.floors');
    var chrome = require('point_of_sale.chrome');
    var QWeb = core.qweb;
    var _lt = core._lt;

    var _super_order = models.Order.prototype;
    models.Order = models.Order.extend({
        initialize: function(attr, options) {
            _super_order.initialize.apply(this, arguments);
            this.is_table_order = false;
            this.token = false;
        },
        set_is_table_order: function(is_table_order) {
            this.is_table_order = is_table_order;
            this.trigger('change', this);
        },
        get_is_table_order: function() {
            return this.is_table_order;
        },
        set_token_table: function(token) {
            this.token = token;
            this.trigger('change', this);
        },
        get_token_table: function() {
            return this.token;
        },
        get_line_all_ready_exit: function(line_id) {
            var self = this;
            var orderlines = self.orderlines.models;
            var flag = false;
            _.each(orderlines, function(line) {
                if (line_id == line.table_order_line_id) {
                    flag = true;
                }
            });
            return flag;
        },
        saveChanges: function() {
            var self = this;
            _super_order.saveChanges.apply(this, arguments);
            if (self.orderlines) {
                if (self.orderlines.models) {
                    var lines = $.map(self.orderlines.models, function(n) {
                        return n.table_order_line_id;
                    });
                    if (lines) {
                        var orderd_st = rpc.query({
                            model: 'table.order.line',
                            method: 'get_table_order_line_state_ordered',
                            args: [lines],
                        }).then(function(orders_ap) {

                        });
                    }
                }
            }

        },
        export_as_JSON: function() {
            var json = _super_order.export_as_JSON.apply(this, arguments);
            json.is_table_order = this.get_is_table_order();
            json.token = this.get_token_table();
            return json;
        },
    });
    var _super_orderline = models.Orderline.prototype;
    models.Orderline = models.Orderline.extend({
        initialize: function(attr, options) {
            _super_orderline.initialize.apply(this, arguments);
            this.table_order_line_id = false;
            this.linked_line_id = false;
        },
        set_table_order_line_id: function(table_order_line_id) {
            this.table_order_line_id = table_order_line_id;
            this.trigger('change', this);
        },
        get_table_order_line_id: function() {
            return this.table_order_line_id;
        },
        set_linked_line_id: function(linked_line_id) {
            this.linked_line_id = linked_line_id;
            this.trigger('change', this);
        },
        get_linked_line_id: function() {
            return this.linked_line_id;
        },

    });
    var TableOrderListWiget = screens.ScreenWidget.extend({
        template: 'TableOrderListWiget',
        show: function() {
            var self = this;
            this._super();
            this.table_id = false;
            if(self.pos.table && self.pos.table.id){
                this.table_id = parseInt(self.pos.table.id);
            }
            rpc.query({
                model: 'table.order',
                method: 'get_table_order_lists',
                args: [this.table_id],
            }).then(function(orders_ap) {
                self.renderElement();
                var orders = orders_ap
                self.render_order_list(orders);
                self.$('.table_order_list_contents').delegate('.table_order_client_line .resume_order_cl', 'click', function(event) {
                    self.line_select(event, $(this), parseInt($(this).data('id')));
                });
                self.$('.table_order_list_contents').delegate('.table_order_client_line .btn_accept_all_order', 'click', function(event) {
                    self._onClickAcceptAllOrder(event, parseInt($(this).data('id')));
                });
                self.$('.table_order_list_contents').delegate('.table_order_client_line .btn_cancel_all_order', 'click', function(event) {
                    self._onClickCancelAllOrder(event, parseInt($(this).data('id')));
                });
                self.$('.table_order_list_contents').delegate('.table_order_client_line .btn_send_to_kitchen_order', 'click', function(event) {
                    self._onClickSendToKitchenOrder(event, parseInt($(this).data('id')));
                });
                self.$('.table_order_list_contents').delegate('.table_order_client_line td.td_clickable', 'click', function(event) {
                    var line_id = $(this).closest('tr').data('id');
                    $('.table_order_client_line').removeClass('highlight');
                    $('.table_order_list_product').addClass('tr-hide');
                    $(this).closest('tr').toggleClass('highlight');
                    $('tr[data-parent_id~="'+line_id+'"]').toggleClass('tr-hide');
                });
            });
        },
        renderElement: function() {
            var self = this;
            this._super();
            this.$('.back').click(function() {
                self.gui.current_screen.hide();
                self.gui.show_screen(self.gui.startup_screen);
                // self.gui.back();
            });

        },
        render_order_list: function(tableorders) {
            if (tableorders) {
                var orderlist = QWeb.render('TableOrderLine', { widget: this, tableorders: tableorders });
                $(this.el).find('.table_order_list_contents').html(orderlist);
                $(this.el).find('.btn_table_order_state').click(_.bind(this.clickTableOrderStateButton, this));
            }

        },
        clickTableOrderStateButton: function(event) {
            var self = this;
            var id = event.currentTarget.dataset.id;
            var state = event.currentTarget.dataset.state;
            rpc.query({
                model: 'table.order.line',
                method: 'change_table_order_state',
                args: [id, state],
            }).then(function(line) {
                self.show();
            });
            return true
        },
        line_select: function(event, $line, id) {
            var self = this;
            var order = rpc.query({
                model: 'table.order',
                method: 'get_table_order_select_lists',
                args: [
                    [id]
                ],
            }).then(function(result) {
                console.log("self", self);
                if (result) {
                    var table = self.pos.tables_by_id[result.table_id]
                    var order = self.pos.get_order();
                    if(!order){
                        self.pos.set_table(table);
                        order = self.pos.add_new_order();
                    }
                    order.set_is_table_order(result.is_table_order);
                    order.set_token_table(result.token);
                    _.each(result.line, function(line) {
                        var product = self.pos.db.get_product_by_id(line.product_id);
                        var is_line_exit = order.get_line_all_ready_exit(line.id);
                        if (!is_line_exit) {
                            order.add_product(product, { quantity: line.qty, merge: false });
                            var od_line = order.get_selected_orderline();
                            if (line.linked_line_id) {
                                od_line.set_linked_line_id(true);
                            }
                            od_line.set_table_order_line_id(line.id);
                            od_line.set_note(line.note);
                        }
                    });
                    self.gui.back();
                }
            });
        },
        start: function() {
            var self = this;
            this._super();
            self.call('bus_service', 'updateOption', 'table.order', session.uid);
            self.call('bus_service', 'onNotification', self, self._onNotification);
            self.call('bus_service', 'startPolling');
        },
        _onNotification: function(notifications) {
            var self = this;
            for (var notif of notifications) {
                if (notif[1].table_order_display) {
                    var user_id = notif[1].table_order_display.user_id;
                    var n = new Noty({
                        theme: 'light',
                        text: notif[1].table_order_display.table_order_message || 'You have new order',
                        timeout: false,
                        layout: 'topRight',
                        type: 'success',
                        closeWith: ['button'],
                        // buttons: [
                        //     Noty.button('Mark As Read', 'btn btn-warning', function() {
                        //         n.close();
                        //     })
                        // ],
                        sounds: {
                            sources: ['/qrcode_table/static/lib/noty/lib/done-for-you.mp3'],
                            volume: 1,
                            conditions: ['docVisible']
                        },
                    });
                    n.show();
                }
            }
        },
        _onClickAcceptAllOrder(event, id){
            var self = this;
            rpc.query({
                model: 'table.order',
                method: 'change_table_accept_all_order',
                args: [id],
            }).then(function(result) {
                self.pos.set_table(null);
                self.pos.table = null;
                self.gui.current_screen.hide();
                self.show();
            });
        },
        _onClickCancelAllOrder(event, id){
            var self = this;
            rpc.query({
                model: 'table.order',
                method: 'change_table_cance_all_order',
                args: [id],
            }).then(function(result) {
                self.pos.set_table(null);
                self.pos.table = null;
                self.gui.current_screen.hide();
                self.show();
            });
        },
        _onClickSendToKitchenOrder(event, id){
            var self = this;
            self.pos.set_table(null);
            self.pos.table = null;
            self.gui.current_screen.hide();
            self.show();
        },
    });
    gui.define_screen({
        'name': 'tableorderlist',
        'widget': TableOrderListWiget,
        'condition': function() {
            return true;
        },
    });

    var TableOrderButton = screens.ActionButtonWidget.extend({
        template: 'TableOrderButton',
        button_click: function() {
            this.pos.set_table(null);
            this.pos.table = null;
            this.gui.show_screen('tableorderlist');
        },
    });

    screens.define_action_button({
        'name': 'tableorderlist',
        'widget': TableOrderButton,
        'condition': function() {
            return true;
        },
    });
    var _super_TableWidget = floors.TableWidget.prototype;
    var TableWidget = floors.TableWidget.include({
        get_custom_table_orders: function(table) {

        },
        renderElement: function() {
            // this.t_order_count = 0;
            this._super();
            // var self = this;
            // var order = rpc.query({
            //     model: 'table.order',
            //     method: 'get_list_of_table_order',
            //     args: [],
            // }).then(function(result){
            //     // self.t_order_count = result;
            //     // self._super();
            // });
            // var orders = this.get_table_orders(table);

        }
    });

    var HeaderTableOrderButtonWidget = chrome.HeaderButtonWidget.extend({
        start: function() {
            return this._super();
        },
    });
    chrome.Chrome.include({
        table_orders_button_widget: {
            'name': 'table_orders_button',
            'widget': HeaderTableOrderButtonWidget,
            'prepend': '.pos-rightheader',
            'args': {
                label: _lt('Table Orders'),
                action: function() {
                    this.chrome.return_to_table_orderlist_screen();
                }
            }
        },
        return_to_table_orderlist_screen: function() {
            this.pos.set_table(null);
            this.pos.table = null;
            this.gui.show_screen('tableorderlist');
        },
        build_widgets: function() {
            var self = this;
            self.widgets.push(self.table_orders_button_widget);
            this._super();
        },
    });
});