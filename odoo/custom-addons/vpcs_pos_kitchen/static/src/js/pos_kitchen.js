odoo.define('vpcs_pos_kitchen.kitchen_screen', function(require) {
    "use strict";

    var bus = require('bus.bus').bus;
    var core = require('web.core');
    var PosBaseWidget = require('point_of_sale.BaseWidget');
    var chrome = require('point_of_sale.chrome');
    var gui = require('point_of_sale.gui');
    var screens = require('point_of_sale.screens');
    var models = require('point_of_sale.models');
    var session = require("web.session");

    var QWeb = core.qweb;
    var _t = core._t;

    var KitchenScreenWidget = screens.ScreenWidget.extend({
        template: 'KitchenScreenWidget',
        events: _.extend({}, screens.ScreenWidget.prototype.events, {
            'click .back': 'click_back',
            'click .refresh': 'refresh_orders',
        }),
        init: function(parent, options) {
            var self = this;
            this._super(parent, options);
            this.time_interval = false;
            this.total_orders = -1;
            this.last_update_rows = [];
        },
        show: function() {
            var self = this;
            this._super();
            self.chrome.widget.order_selector.hide();
            self.render_kitchen_orders();
            self.time_interval = setInterval(function() {
                self.loop_waiting_tm();
            }, 1000);
        },
        hide: function() {
            this.chrome.widget.order_selector.show();
            this._super();
            clearInterval(this.time_interval);
        },
        click_back: function() {
            this.gui.show_screen('products');
        },
        refresh_orders: function() {
            var self = this;
            this.pos.db.reload_orders().then(function(r) {
                self.render_kitchen_orders();
            });
        },
        render_kitchen_orders: function() {
            var self = this;
            var $dv_orders = this.$('.container-kitchen-orders');
            if (!$dv_orders.length) {
                return;
            }
            var rows = this.pos.db.pos_synch_all_parsed(this.pos.db.synch_orders);
            var visible_rows = [];
            _.each(rows, function(row) {
                var has_products = _.filter(row.orderlines, function(line) {
                    return line.product;
                });
                if (has_products) {
                    visible_rows.push(row);
                }
            });
            var bell = false;
            if (self.total_orders != -1 && self.total_orders < visible_rows.length && self.pos.gui.get_current_screen() == 'kitchen') {
                bell = true;
            } else {
                _.each(visible_rows, function(row) {
                    var _torder = _.findWhere(self.last_update_rows, {
                        'name': row.name
                    });
                    if (!_torder) {
                        return;
                    } else if (_torder.orderlines.length < row.orderlines.length) {
                        if (self.pos.gui.get_current_screen() == 'kitchen') {
                            bell = true;
                        }
                        return;
                    }
                    _.each(row.orderlines, function(line) {
                        var _tline = _.findWhere(_torder.orderlines, {
                            'id': line.id
                        });
                        if (_tline && _tline.qty < line.qty) {
                            if (self.pos.gui.get_current_screen() == 'kitchen') {
                                bell = true;
                            }
                            return;
                        }
                    });
                    if (bell) {
                        return
                    }
                });
            }
            if (bell) {
                self.gui.play_sound('tin');
            }
            self.total_orders = visible_rows.length;
            self.last_update_rows = visible_rows;
            var str_orders = $(QWeb.render('KitchenOrders', {
                widget: self,
                orders: visible_rows,
            }));
            $dv_orders.empty();
            $dv_orders.append(str_orders);
            var $btns = $dv_orders.find("button.k-state-btn");
            $btns.click(function(event) {
                var $elem = $(event.currentTarget);
                var data = $elem.data();
                $elem.addClass('active').siblings().removeClass('active');
                self.pos.db.pos_orderline_state(data.uid, data.id, data.state).then(function() {
                    if (data.state == "done") {
                        var $tr = $elem.closest('tr');
                        if ($tr.siblings().length == 0) {
                            $tr.parents('.kitchen-order').remove();
                            return;
                        }
                        $tr.remove();
                    }
                });
            });
        },
        loop_waiting_tm: function() {
            var self = this;
            var $waiting_tms = this.$("div.js_waiting_tm");
            _.each($waiting_tms, function(dv_tm) {
                var $dv_tm = $(dv_tm);
                if ($dv_tm.length) {
                    var $dv = $dv_tm[0];
                    var creation_date = $dv.dataset.creation_date;
                    var format = "YYYY-MM-DD hh:mm:ss";
                    var ms = moment(moment(), format).diff(creation_date, format);
                    var duration = moment.duration(ms);

                    var rem_tm = "";
                    if (duration.hours() > 0) {
                        rem_tm = duration.hours() + ":";
                    }
                    rem_tm += duration.minutes() + ':' + duration.seconds();
                    $dv_tm.text(rem_tm);
                }
            });
        },
    });

    gui.define_screen({
        'name': 'kitchen',
        'widget': KitchenScreenWidget,
    });

    // Add the kitchen screen to the GUI, and set it as the default screen
    chrome.Chrome.include({
        init: function() {
            var self = this;
            self._super();
            bus.on("notification", self, self.on_notification);
            var channel = JSON.stringify([session.db, 'pos.order.synch', session.uid]);
            bus.add_channel(channel);
            bus.start_polling();
        },
        build_widgets: function() {
            var self = this;
            this._super();
            if (this.pos.config.iface_is_kitchen) {
                this.gui.set_startup_screen('kitchen');
                this.gui.show_screen('kitchen');
            }
        },
        on_notification: function(notification) {
            var self = this;
            var channel = notification[0] ? notification[0][0] ? notification[0][0] : false : false;
            var message = notification[0] ? notification[0][1] ? notification[0][1] : false : false;
            if ((Array.isArray(channel) && (channel[1] === 'pos.order.synch'))) {
                if (message) {
                    var result = _.omit(message, 'order_status');
                    if (message.order_status == 'new_order') {
                        self.pos.db.synch_orders.push(result);
                    } else if (message.order_status == 'update_order') {
                        var update_orders = _.filter(self.pos.db.synch_orders, function(sync_order) {
                            return sync_order.order_uid != result.order_uid;
                        });
                        update_orders.push(result);
                        self.pos.db.synch_orders = update_orders;
                    } else if (message.order_status == 'remove_order') {
                        var update_orders = _.filter(self.pos.db.synch_orders, function(sync_order) {
                            return sync_order.order_uid != result.order_uid;
                        });
                        self.pos.db.synch_orders = update_orders;
                    } else if (message.order_status == 'orderline_state') {
                        _.each(self.pos.db.synch_orders, function(sync_order) {
                            if (sync_order.order_uid == result.order_uid) {
                                sync_order.order_data = result.order_data;
                            }
                        });
                        self.set_orderline_state(result.order_data)
                    }

                    var kitchen_screen = self.pos.gui.screen_instances ? self.pos.gui.screen_instances.kitchen : false;
                    if (kitchen_screen) {
                        kitchen_screen.render_kitchen_orders();
                    }
                }
            }
        },
        get_order_by_id: function(data) {
            var uid = data.uid;
            var orders = this.pos.get_order_list();
            for (var i = 0; i < orders.length; i++) {
                if (orders[i].uid === uid) {
                    return orders[i];
                }
            }
            return undefined;
        },
        set_orderline_state: function(result) {
            var self = this;
            var data = JSON.parse(result);
            var lines = data['lines'];
            var data = JSON.parse(result);
            var order = self.get_order_by_id(data),
                orderlines = order && order.get_orderlines() || [];
            if (!_.isEmpty(orderlines)) {
                _.each(orderlines, function(line) {
                    _.each(lines, function(l) {
                        if (line.id == l.id) {
                            line.set_state(l.state);
                        }
                    });
                    self.trigger('change', line);
                });
            }
        },
    });

    chrome.UsernameWidget.include({
        click_username: function() {
            var self = this;
            if (this.pos.config.iface_is_kitchen) {
                return;
            }
            this._super();
        }
    });

    // Show Kitchen View Button
    var BtnKitchenView = screens.ActionButtonWidget.extend({
        template: 'BtnKitchenView',
        button_click: function() {
            this.gui.show_screen('kitchen');
        },
    });

    screens.define_action_button({
        'name': 'btn_kitchen_view',
        'widget': BtnKitchenView,
        'condition': function() {
            return this.pos.config.iface_btn_kitchen;
        }
    });

    // Cooking State
    var OrderPrioritySelection = screens.ActionButtonWidget.extend({
        template: 'OrderPrioritySelection',
        button_click: function() {
            var order = this.pos.get_order();
            order.set_priority(this.el.value);
        },
    });

    screens.define_action_button({
        'name': 'popup_order_priority',
        'widget': OrderPrioritySelection,
        'condition': function() {
            return this.pos.config.iface_btn_priority;
        }
    });

    PosBaseWidget.include({
        init: function(parent, options) {
            var self = this;
            this._super(parent, options);
            if (this.gui && this.gui.screen_instances.products && this.gui.screen_instances.products.action_buttons.submit_order) {
                var submit_order = this.gui.screen_instances.products.action_buttons.submit_order;
                submit_order.button_click = function() {
                    var order = this.pos.get_order();
                    if (order.hasChangesToPrint()) {
                        order.printChanges();
                        order.saveChanges();
                        _.each(order.get_orderlines(), function(line) {
                            if (line.get_has_qty_change() && line.printable()) {
                                line.set_state('new');
                                line.set_qty_change(false);
                            }
                        });
                        order.send_to_kitchen();
                    }
                };
            }
        },
    });

    screens.NumpadWidget.include({
        clickDeleteLastChar: function() {
            var self = this;
            var order = this.pos.get('selectedOrder');
            if (order.selected_orderline != undefined && order.selected_orderline.get_state() == 'done') {
                self.gui.show_popup('alert', {
                    title: _t('Warning'),
                    warning_icon: true,
                    body: _t('Cannot remove this product, because its already served (done).'),
                });
                return false;
            }
            return self._super();
        },
        clickAppendNewChar: function(event) {
            var self = this;
            if (this.state.get('mode') == 'quantity') {
                var order = this.pos.get('selectedOrder');
                if (order.selected_orderline != undefined && order.selected_orderline.get_state() == 'done') {
                    self.gui.show_popup('alert', {
                        title: _t('Warning'),
                        warning_icon: true,
                        body: _t('Please add new line of this product, because this product already served !'),
                    });
                    return false;
                }
            }
            return this._super(event);
        }
    });

    screens.OrderWidget.include({
        renderElement: function() {
            var self = this;
            this._super();
            var order = this.pos.get_order();
            if (this.pos.config.iface_btn_priority && order) {
                this.$('.js_order_priority').val(order.priority);
            }
        },
        set_value: function(val) {
            this._super(val);
            var order = this.pos.get_order();
            var line = order.get_selected_orderline();
            if (line && line.printable()) {
                var mode = this.numpad_state.get('mode');
                if (mode === 'quantity' && val != 'remove') {
                    line.set_qty_change(true);
                }
            }
        },
    });
    return KitchenScreenWidget;
});