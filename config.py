JS_SCRIPT = """
function getRandomInt(min, max) {
    return Math.floor(Math.random() * (max - min + 1)) + min;
}

function modifyClickEvent(event) {
    if (!event._isModified) {
        // Save original values only if not already saved
        event._screenX = event.screenX;
        event._screenY = event.screenY;

        // Define properties only once
        Object.defineProperty(event, 'screenX', {
            get: function() {
                return this._screenX + getRandomInt(0, 200);
            }
        });
        Object.defineProperty(event, 'screenY', {
            get: function() {
                return this._screenY + getRandomInt(0, 200);
            }
        });

        // Mark event as modified
        event._isModified = true;
    }
}

// Store the original addEventListener method
const originalAddEventListener = EventTarget.prototype.addEventListener;

// Override the addEventListener method
EventTarget.prototype.addEventListener = function(type, listener, options) {
    if (type === 'click') {
        const wrappedListener = function(event) {
            // Modify the click event properties
            modifyClickEvent(event);

            // Call the original listener with the modified event
            listener.call(this, event);
        };
        // Call the original addEventListener with the wrapped listener
        originalAddEventListener.call(this, type, wrappedListener, options);
    } else {
        // Call the original addEventListener for other event types
        originalAddEventListener.call(this, type, listener, options);
    }
};
"""

CHALLENGE_TITLES = [
    # Cloudflare
    'Just a moment...',
    '请稍候…',
    # DDoS-GUARD
    'DDOS-GUARD',
]

CHALLENGE_SELECTORS = [
    # Cloudflare
    '#cf-challenge-running', '.ray_id', '.attack-box', '#cf-please-wait', '#challenge-spinner', '#trk_jschal_js',
    # Custom CloudFlare for EbookParadijs, Film-Paleis, MuziekFabriek and Puur-Hollands
    'td.info #js_info',
    # Fairlane / pararius.com
    'div.vc div.text-box h2'
]

CHALLENGE_BOX_SELECTORS = [
    'input[name="cf-turnstile-response"]'
]