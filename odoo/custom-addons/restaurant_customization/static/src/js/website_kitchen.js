odoo.define('restaurant_customization.kitchen', function (require) {
    'use strict';

    var base = require('web_editor.base');
    var core = require('web.core');
    var utils = require('web.utils');
    var _t = core._t;
    var ajax = require('web.ajax')
    
    $('.btn_progress').click(function (event){
        var self = $(this);
        var value = {};
        var line_id = $(this).data('line-id');
        value = {
            'line_id': line_id,
            'status':'progress',
        }
        ajax.jsonRpc("/kitchen/status", 'call', {'val':value}).then(function (data) {
            location.reload();
        });
    });

    $('.btn_done').click(function (event){
        var self = $(this);
        var value = {}
        var line_id = $(this).data('line-id');
        value = {
            'line_id': line_id,
            'status':'done',
        }
        ajax.jsonRpc("/kitchen/status", 'call', {'val':value}).then(function (data) {
            location.reload();
        });;
    });


});
