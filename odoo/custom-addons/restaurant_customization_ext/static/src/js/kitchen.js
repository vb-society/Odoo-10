odoo.define('restaurant_customization_ext.kitchen', function (require) {
    'use strict';

    var bus = require('bus.bus').bus;
    
    var CHANNEL_NAME = 'orderscreen.auto_refresh';
    bus.off('notification');
    bus.on("notification", this, function(notification){
        for (var i = 0; i < notification.length; i++) {
            var channel = notification[i][0];
            var message = notification[i][1];
            on_notification_do(channel, message);
        }
    });
    bus.start_polling();

    var on_notification_do = function (channel, message) {
        var channel = JSON.parse(channel);
        var error = false;
        if (Array.isArray(channel) && channel[1] === CHANNEL_NAME) {
            try {
                if(window.location.href.indexOf('/orderscreen') > -1 || 
                   window.location.href.indexOf('/kitchenscreen') > -1){
                    window.location.reload();
                    $('#kitchen_notify')[0].play();
                }
            } catch (err) {
                error = err;
                console.error(err);
            }
        }
    }

});
