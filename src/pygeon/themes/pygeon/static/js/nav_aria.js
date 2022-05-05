// https://www.a11y-101.com/development/nested-navigation
if (!Element.prototype.closest) {
    Element.prototype.closest = function(s) {
        var el = this;
        if (!document.documentElement.contains(el)) return null;
            do {
                if (el.matches(s)) return el;
                el = el.parentElement || el.parentNode;
            } while (el !== null && el.nodeType === 1);
            return null;
    };
}

/*
/ walk through all links
/ watch out whether they have an 'aria-haspopup'
/ as soon as a link has got the 'focus' (also key), then:
/ set nested UL to 'display:block;'
/ set attribute 'aria-hidden' of this UL to 'false'
/ and set attribute 'aria-expanded' to 'true'
*/

var opened;

// resets currently opened list style to CSS based value
// sets 'aria-hidden' to 'true'
// sets 'aria-expanded' to 'false'
function reset() {
    if (opened) {
        opened.style.display = '';
        opened.setAttribute('aria-hidden', 'true');
        opened.setAttribute('aria-expanded', 'false');
    }
}

// sets given list style to inline 'display: block;'
// sets 'aria-hidden' to 'false'
// sets 'aria-expanded' to 'true'
// stores the opened list for later use
function open(el) {
    el.style.display = 'block';
    el.setAttribute('aria-hidden', 'false');
    el.setAttribute('aria-expanded', 'true');
    opened = el;
}

// event delegation
// reset navigation on click outside of list
document.addEventListener('click', function(event) {
    if (!event.target.closest('[aria-hidden]')) {
        reset();
    }
});

// event delegation
document.addEventListener('focusin', function(event) {
    // reset list style on every focusin
    reset();

    // check if a[aria-haspopup="true"] got focus
    var target = event.target;
    var hasPopup = target.getAttribute('aria-haspopup') === 'true';
    if (hasPopup) {
        open(event.target.nextElementSibling);
        return;
    }

    // check if anchor inside sub menu got focus
    var popupAnchor = target.parentNode.parentNode.previousElementSibling;
    var isSubMenuAnchor = popupAnchor && popupAnchor.getAttribute('aria-haspopup') === 'true';
    if (isSubMenuAnchor) {
        open(popupAnchor.nextElementSibling);
        return;
    }
})
