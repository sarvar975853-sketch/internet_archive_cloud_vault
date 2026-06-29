// ads.js — Banner 728x90 + Banner 300x250 (iframe) + Popunder
(function() {
    "use strict";

    // ── Ad Keys ───────────────────────────────────────────────────────
    var _banner728 = { key: "5a7b0a08c8d19f0201beca066b7c994a" };
    var _banner300 = { key: "5d6b20159bd5c960d515174e6fe72027" };
    var _popunderSrc = "https://pl30083381.effectivecpmnetwork.com/ac/44/8b/ac448bab40fa3ad3b352611f4e725982.js";

    // ── 1. Top Banner 728x90 ──────────────────────────────────────────
    function _renderBanner728() {
        var slot = document.getElementById("ad-top");
        if (!slot) return;
        window.atOptions = {
            key: _banner728.key,
            format: "iframe",
            height: 90,
            width: 728,
            params: {}
        };
        var s = document.createElement("script");
        s.src = "https://www.highperformanceformat.com/" + _banner728.key + "/invoke.js";
        s.async = true;
        slot.appendChild(s);
    }

    // ── 2. Sidebar Banner 300x250 (isolated iframe) ───────────────────
    function _renderBanner300() {
        var slot = document.getElementById("ad-sidebar-slot");
        if (!slot) return;

        // Create an iframe so atOptions doesn't collide with the 728x90 banner
        var iframe = document.createElement("iframe");
        iframe.width = 300;
        iframe.height = 250;
        iframe.frameBorder = "0";
        iframe.scrolling = "no";
        iframe.style.border = "none";
        iframe.style.overflow = "hidden";

        // srcdoc gives the iframe its own window, its own atOptions
        iframe.srcdoc =
            '<!DOCTYPE html><html><head><meta charset="UTF-8"></head><body style="margin:0;padding:0;">' +
            '<script>window.atOptions={' +
            "key:'" + _banner300.key + "'," +
            "format:'iframe'," +
            "height:250," +
            "width:300," +
            "params:{}" +
            '};</script>' +
            '<script src="https://www.highperformanceformat.com/' + _banner300.key + '/invoke.js" async></script>' +
            '</body></html>';

        slot.appendChild(iframe);
    }

    // ── 3. Popunder on first click ────────────────────────────────────
    function _popunder() {
        var clicked = false;
        document.addEventListener("click", function() {
            if (clicked) return;
            clicked = true;
            var s = document.createElement("script");
            s.src = _popunderSrc;
            document.head.appendChild(s);
        }, { once: true });
    }

    // ── 4. Anti-adblock watcher ───────────────────────────────────────
    function _watch() {
        var observer = new MutationObserver(function(mutations) {
            mutations.forEach(function(m) {
                m.removedNodes.forEach(function(n) {
                    if (n.nodeType === 1 && n.id === "ad-top") {
                        setTimeout(_renderBanner728, 3000);
                    }
                });
            });
        });
        observer.observe(document.body, { childList: true, subtree: true });
    }

    // ── Boot ──────────────────────────────────────────────────────────
    function _boot() {
        _renderBanner728();
        _renderBanner300();
        _popunder();
        _watch();
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", _boot);
    } else {
        _boot();
    }

})();
