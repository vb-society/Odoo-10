odoo.define('vpcs_pos_kitchen.pos_synch', function(require) {
    "use strict";

    var PosDB = require('point_of_sale.DB');
    var models = require('point_of_sale.models');

    var Model = require('web.DataModel');
    var PosSynch = new Model('pos.order.synch');

    var core = require('web.core');
    var QWeb = core.qweb;

    PosDB.include({
        remove_order: function(order_id) {
            this._super.apply(this, arguments);
            this.pos_synch_remove([order_id]);
        },
        reload_orders: function(){
            var self = this;
            return PosSynch.call('synch_all', []).then(function(result) {
                self.synch_orders = result;
                return result;
            }).fail(function(error, event) {
                event.preventDefault();
                return;
            });
        },
        pos_synch_update: function(action, orders) {
            var self = this;
            var uid = orders[0].uid
            if (action == 'add') {
                orders = _.filter(orders, function(order) {
                    return order && order.lines.length;
                })
            }
            if (!orders.length) {
                action = 'remove_line';
                orders = [{
                    'uid': uid,
                    'lines': []
                }];
            }
            var json_orders = JSON.stringify(orders);
            return PosSynch.call('update_orders', [action, json_orders], ).then(function(result) {
                return result;
            }).fail(function(error, event) {
                event.preventDefault();
                return;
            });
        },

        pos_synch_remove: function(order_uids) {
            if (!order_uids.length) {
                return;
            }
            return PosSynch.call('remove_order', [order_uids], )
                .then(function(result) {
                    return result;
                })
                .fail(function(error, event) {
                    event.preventDefault();
                    console.error('Failed to remove orders : ', order_uids);
            });
        },

        pos_synch_all_parsed: function(orders) {
            var self = this;
            orders = _.filter(orders, function(_order){return _order.order_data;});

            var parsed_orders = [];
            _.each(orders, function(order) {
                var parsed_row = $.parseJSON(order.order_data);
                var already_added = _.where(parsed_orders, {'uid': parsed_row.uid});
                if (already_added.length){
                    return;
                } 
                var orderlines = [];
                var prod_ids = _.keys(self.product_by_id);
                _.each(parsed_row.lines, function(oline) {
                    if(oline.state == 'done') return;
                    var prod_id = oline.product_id;
                    if (prod_id && _.indexOf(prod_ids, prod_id.toString()) > -1) {
                        oline.product = self.product_by_id[prod_id];
                        orderlines.push(oline);
                    }
                });
                if (!orderlines.length) {
                    return;
                }
                if (parsed_row.partner_id) {
                    parsed_row.partner = self.partner_by_id[parsed_row.partner_id];
                }
                parsed_row.orderlines = _.sortBy(orderlines, "id");
                parsed_orders.push(parsed_row);
            });
            return parsed_orders;
        },

        pos_orderline_state: function(uid, line_id, state) {
            var self = this;
            if (!uid || !line_id || !state) {
                return;
            }
            return PosSynch.call('orderline_state', [uid, line_id, state], ).then(function(result) {
                return result;
            }).fail(function(error, event) {
                event.preventDefault();
                console.error('Failed to POS Synch Orderline State : ', uid, state);
            });
        }
    });

    var _super_posmodel = models.PosModel;
    models.PosModel = models.PosModel.extend({
        initialize: function(attributes, options) {
            var self = this;
            _super_posmodel.prototype.initialize.apply(this, arguments);
            this.priority_by_key = _.extend({}, {
                'low': 'Low',
                'normal': 'Normal',
                'high': 'High',
            });
        },
        delete_current_order: function() {
            var order = this.get_order();
            this.db.pos_synch_remove([order.uid]);
            _super_posmodel.prototype.delete_current_order.apply(this, arguments);
        },
    });

    var _super_order = models.Order.prototype;
    models.Order = models.Order.extend({
        initialize: function(attributes, options) {
            _super_order.initialize.apply(this, arguments);
            this.priority = 'normal';
            this.priority_display = this.pos.priority_by_key[this.priority];
            this.order_to_kitchen = false;
        },
        set_priority: function(priority) {
            this.priority = priority;
            this.trigger('change', this);
        },
        get_priority: function() {
            return this.priority;
        },
        send_to_kitchen: function() {
            if (!this.orderlines.length) {
                return;
            }
            this.update_to_kitchen();
        },
        update_to_kitchen: function() {
            var action = "add";
            if (this.order_to_kitchen) {
                action = "update";
            }
            var line_models = [];
            for(var i=0; i < this.orderlines.models.length; i++){
                var order_line = this.orderlines.models[i];
                if (order_line.printable() && !order_line.order_to_kitchen) {
                    if (! order_line.get_state()) {
                        order_line.set_state('new');
                    }
                    line_models.push(order_line.export_as_JSON());
                };
            }
            var order = this.export_as_JSON();
            order.lines = line_models;
            this.pos.db.pos_synch_update(action, [order]);
        },
        export_as_JSON: function() {
            var data = _super_order.export_as_JSON.apply(this, arguments);
            data.priority = this.priority;
            return data;
        },
        init_from_JSON: function(json) {
            this.priority = json.priority;
            _super_order.init_from_JSON.call(this, json);
        },
        export_for_printing: function(){
            var r = _super_order.export_for_printing.call(this);
            return _.extend(r, {
                'priority': this.get_priority(),
                'priority_display': this.priority_display,
            });
        },
    });

    var _super_orderline = models.Orderline.prototype;
    models.Orderline = models.Orderline.extend({
        initialize: function(attr, options) {
            _super_orderline.initialize.call(this, attr, options);
            this.state = this.state || "";
            this.has_qty_change = false;
        },
        set_state: function(state) {
            this.state = state;
            this.trigger('change', this);
        },
        get_state: function(state) {
            return this.state;
        },
        set_qty_change: function(flag){
            this.has_qty_change = flag
            this.trigger('change', this);
        },
        get_has_qty_change: function(){
            return this.has_qty_change;
        },
        can_be_merged_with: function(orderline) {
            var res = _super_orderline.can_be_merged_with.apply(this, arguments);
            if (orderline.get_state() !== this.get_state()) {
                res = false;
            }
            return res;
        },
        clone: function() {
            var orderline = _super_orderline.clone.call(this);
            orderline.state = this.state;
            return orderline;
        },
        export_as_JSON: function() {
            var json = _super_orderline.export_as_JSON.call(this);
            json.state = this.state;
            return json;
        },
        init_from_JSON: function(json) {
            _super_orderline.init_from_JSON.apply(this, arguments);
            this.state = json.state;
        },
    });
});
