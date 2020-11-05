odoo.define('vpcs_pos_kitchen.models', function(require) {
    "use strict";

    var models = require('point_of_sale.models');
    var Gui = require('point_of_sale.gui');

    models.PosModel.prototype.models.push({
        model: 'pos.order.synch',
        fields: ['order_uid', 'order_data', 'write_date', 'pos_id'],
        loaded: function(self, synch_orders) {
            self.db.synch_orders = synch_orders;
        },
    });

    var PosCategory = _.find(models.PosModel.prototype.models, function(p) {
        if (p.model == 'pos.category') {
            return true;
        }
        return false;
    });
    PosCategory.fields.push('color');
    var _super_loaded = PosCategory.loaded;
    PosCategory.loaded = function(self, categories) {
        var new_categ = [];
        var category_by_id = {};
        for(var i=0, len = categories.length; i < len; i++){
            category_by_id[categories[i].id] = categories[i];
        }
        var allowed_categ_ids = [];
        _.each(self.config.categ_ids, function(cat_id) {
            var categ = _.where(categories, {'id': cat_id});
            if (categ.length) {
                categ = categ[0];
                allowed_categ_ids.push(cat_id);
                new_categ.push(categ);
                _.each(categ.child_id, function(_child_id){
                    allowed_categ_ids.push(_child_id);
                    new_categ.push(category_by_id[_child_id]);
                });
            }
        });

        if (!self.config.categ_ids.length) {
            new_categ = categories;
            allowed_categ_ids = _.pluck(categories, "id");
        }
        self.db.allowed_categ_ids = allowed_categ_ids;
        self.db.add_categories(new_categ);
    };

    var ProductProduct = _.find(models.PosModel.prototype.models, function(p) {
        if (p.model == 'product.product') {
            return true;
        }
        return false;
    });
    var _super_loaded = ProductProduct.loaded,
        _super_domain = ProductProduct.domain;
    ProductProduct.domain = function(self) {
        return _super_domain.concat([['pos_categ_id', 'in', self.db.allowed_categ_ids]]);
    };
    ProductProduct.loaded = function(self, products) {
        var categories = self.db.category_by_id;
        _.each(products, function(prod) {
            prod.bgcolor = 'white';
            if (prod.pos_categ_id.length) {
                var categ = categories[prod.pos_categ_id[0]];
                if (categ) {
                    prod.bgcolor = categ.color;
                }
            }
        });
        _super_loaded(self, products);
    };

    Gui.Gui.include({
        play_sound: function(sound) {
            var src = '';
            if (sound === 'error') {
                src = "/point_of_sale/static/src/sounds/error.wav";
            } else if (sound === 'bell') {
                src = "/point_of_sale/static/src/sounds/bell.wav";
            } else if (sound === 'tin') {
                src = "/vpcs_pos_kitchen/static/src/sounds/tin.mp3";
            } else {
                console.error('Unknown sound: ', sound);
                return;
            }
            $('body').append('<audio src="' + src + '" autoplay="true"></audio>');
        },
    });
});
