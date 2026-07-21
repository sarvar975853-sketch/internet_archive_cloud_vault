// loader.js — Minimal stealth layer
// Exposes utility functions for ad rendering.

(function() {
    "use strict";

    // Random ID generator for containers
    function _rid() {
        var chars = "abcdefghijklmnopqrstuvwxyz0123456789";
        var id = "_";
        for (var i = 0; i < 8; i++) id += chars[Math.floor(Math.random() * chars.length)];
        return id;
    }

    // Expose globally
    window.__ad = { rid: _rid };

})();
