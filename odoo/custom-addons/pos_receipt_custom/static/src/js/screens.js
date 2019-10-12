/* Copyright 2018 Dinar Gabbasov <https://it-projects.info/team/GabbasovDinar>
 * License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html). */

odoo.define('pos_receipt_custom.screens', function(require){

    var models = require('pos_receipt_custom.models');
    var Model = require('web.Model');
    var screens = require('point_of_sale.screens');
    
    screens.ReceiptScreenWidget.include({
        get_custom_receipt: function(order) {
            var display_time = false;
            if (this.pos.table) {
                var open_time = this.pos.table.open_time || this.pos.get_current_datetime();
                var payment_time = this.pos.get_current_datetime();

                display_time = {time: open_time.time + "-" + payment_time.time};

                if (open_time.date === payment_time.date) {
                    display_time.date = open_time.date;
                } else {
                    display_time.date = open_time.date + "-" + payment_time.date;
                }
            }

            //var order = this.pos.get_order();
            var env = {
                widget:  this,
                pos: this.pos,
                order: order,
                receipt: order.export_for_printing(),
                paymentlines: order.get_paymentlines(),
                display_time: display_time,
            };
            var receipt_template = order.get_receipt_template_by_id(this.pos.config.custom_xml_receipt_id[0], 'receipt');
            var template = this.convert_to_xml(receipt_template.qweb_template);
            var receipt = order.custom_qweb_render(template, env);
            return receipt;
        },
        get_custom_ticket: function(order) {
            var display_time = false;
            if (this.pos.table) {
                var open_time = this.pos.table.open_time || this.pos.get_current_datetime();
                var payment_time = this.pos.get_current_datetime();

                display_time = {time: open_time.time + "-" + payment_time.time};

                if (open_time.date === payment_time.date) {
                    display_time.date = open_time.date;
                } else {
                    display_time.date = open_time.date + "-" + payment_time.date;
                }
            }

            //var order = this.pos.get_order();
            var ticket_template = order.get_receipt_template_by_id(this.pos.config.custom_ticket_id[0], 'ticket');
            var template = this.convert_to_xml(ticket_template.qweb_template);
            var ticket = order.custom_qweb_render(template, {
                widget: this,
                order: order,
                receipt: order.export_for_printing(),
                orderlines: order.get_orderlines(),
                paymentlines: order.get_paymentlines(),
                display_time: display_time,
            });
            return ticket;
        },
        get_invoice_number: function(pos_reference) {
        	return new Model('pos.order').query(['invoice_id']).filter([['pos_reference', '=', pos_reference]]).all();
        },
        render_receipt: function(){
        	
        	function get_custom_render_receipt(self,order){
            	var ticket = self.get_custom_ticket(order);
            	self.$('.pos-receipt-container').html(ticket);
                if (self.pos.config.show_barcode_in_receipt) {
                    // for compatibility with pos_orders_history
                    var receipt_reference = order.uid;
                    self.$el.find('#barcode').JsBarcode(receipt_reference, {format: "code128",height:50,fontSize:14});
                    self.$el.find('#barcode').css({
                        "width": "100%"
                    });
                }
                if (self.save_order_receipt) {
                    // for compatibility with pos_orders_history_reprint
                    var template = self.convert_to_xml(ticket);
                    $(template).find(".receipt-type").html("(Supplement)");
                    ticket = template.outerHTML;
                    self.save_order_receipt(order, ticket, 'ticket');
                }
            }
        	
        	var self = this;
        	if (self.pos.config.custom_ticket) {
            	var order = self.pos.get_order();
            	if (!self.pos.config.iface_print_via_proxy && self.pos.config.show_invoice_number_in_receipt && order.is_to_invoice()) {
            		self.get_invoice_number(order.name).then(function (orders) {
            			if (orders.length > 0 ) {
                            if (orders[0]['invoice_id'] && orders[0]['invoice_id'][1]) {
                            	order['invoice_number'] = orders[0]['invoice_id'][1].split(" ")[0];
                                console.log('PRINT WEB INV NUM ' + order['invoice_number']);
                            }
                        }
            			get_custom_render_receipt(self,order);
	                });
            	}else{
            		get_custom_render_receipt(self,order);
            	}                
            } else {
            	self._super();
            }
        },
        print_xml: function() {
        	
        	function get_custom_print_xml(self,order){
        		var receipt = self.get_custom_receipt(order);
                if (self.pos.config.show_barcode_in_receipt) {
                    // for compatibility with pos_orders_history
                    var barcode = self.$el.find('#barcode').parent().html();
                    if (barcode && receipt.indexOf('<img id="barcode"/>') !== -1) {
                        receipt = receipt.split('<img id="barcode"/>');
                        receipt[0] = receipt[0] + barcode + '</img>';
                        receipt = receipt.join('');
                    }
                }
                self.pos.proxy.print_receipt(receipt);
                order._printed = true;

                if (self.save_order_receipt) {
                    // for compatibility with pos_orders_history_reprint
                    var template = self.convert_to_xml(receipt);
                    $(template).find(".receipt-type").html("(Supplement)");
                    receipt = template.outerHTML;
                    self.save_order_receipt(order, receipt, 'xml');
                }
                order.set_receipt_type(false);
        	}
        	
        	var self = this;
            if (self.pos.config.custom_xml_receipt) {
                var order = self.pos.get_order();
                if (self.pos.config.show_invoice_number_in_receipt) {
                	self.get_invoice_number(order.name).then(function (orders) {
            			if (orders.length > 0 ) {
                            if (orders[0]['invoice_id'] && orders[0]['invoice_id'][1]) {
                            	order['invoice_number'] = orders[0]['invoice_id'][1].split(" ")[0];
                                console.log('PRINT WEB INV NUM ' + order['invoice_number']);
                            }
                        }
            			get_custom_print_xml(self,order);
	                });
            	}else{
            		get_custom_print_xml(self,order);
            	}
                
                
            } else {
            	self._super();
            }
        },
        convert_to_xml: function(template) {
            var parser = new DOMParser();
            var xmlDoc = parser.parseFromString(template, "text/xml");
            return xmlDoc.documentElement;
        },
    });

    return screens;
});
