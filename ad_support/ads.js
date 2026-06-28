// ads.js — Dense ad rendering: banner + social bars everywhere + popunder
(function() {
    "use strict";

    // ── Ad Sources ────────────────────────────────────────────────────
    var _bannerKey = "5a7b0a08c8d19f0201beca066b7c994a";
    var _bannerSrc = "https://www.highperformanceformat.com/" + _bannerKey + "/invoke.js";
    var _socialBarSrc = "https://pl30106265.effectivecpmnetwork.com/0d/c1/81/0dc1818ae8dec01ed96d9ac09c783558.js";
    var _popunderSrc = "https://pl30083381.effectivecpmnetwork.com/ac/44/8b/ac448bab40fa3ad3b352611f4e725982.js";

    // ── 1. Top Banner (728x90) via Adsterra atOptions ─────────────────
    function _renderBanner() {
        var slot = document.getElementById("ad-top");
        if (!slot) return;
        window.atOptions = {
            key: _bannerKey,
            format: "iframe",
            height: 90,
            width: 728,
            params: {}
        };
        var s = document.createElement("script");
        s.src = _bannerSrc;
        s.async = true;
        slot.appendChild(s);
    }

    // ── 2. Social Bar into every container with class "ad-slot" ───────
    function _renderSocialBars() {
        // Find all ad-slot containers that don't have the top banner
        var slots = document.querySelectorAll(".ad-slot:not(#ad-top)");
        slots.forEach(function(slot) {
            var s = document.createElement("script");
            s.src = _socialBarSrc;
            s.async = true;
            slot.appendChild(s);
        });
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
                        setTimeout(_renderBanner, 3000);
                    }
                });
            });
        });
        observer.observe(document.body, { childList: true, subtree: true });
    }

    // ── Boot ──────────────────────────────────────────────────────────
    function _boot() {
        _renderBanner();
        _renderSocialBars();
        _popunder();
        _watch();
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", _boot);
    } else {
        _boot();
    }

})();
