// https://www.w3.org/WAI/tutorials/menus/flyout/
function setMouseOutTimeout(event) {
	let target = event.target;
	target.timer = setTimeout(function(event){
		target.className = "has-submenu";
	}, 1000);
	target.removeEventListener("mouseleave", setMouseOutTimeout, false);
}

var menuItems = document.querySelectorAll('li.has-submenu');
Array.prototype.forEach.call(menuItems, function(el, i){
	el.addEventListener("mouseenter", function(event){
		this.className = "has-submenu open";
		clearTimeout(this.timer);

		if (window.screen.availWidth > 767) {
			this.addEventListener("mouseleave", setMouseOutTimeout);
		}
	});
});

var menuItems = document.querySelectorAll('li.has-submenu');
Array.prototype.forEach.call(menuItems, function(el, i){
	var activatingA = el.querySelector('a');
	var btn = el.querySelector('button');

	btn.addEventListener("click",  function(event){
		if (this.parentNode.className == "has-submenu") {
			this.parentNode.className = "has-submenu open";
			this.parentNode.querySelector('ul').setAttribute('aria-expanded', "true");
			this.parentNode.querySelector('ul').setAttribute('aria-hidden', "false");
		} else {
			this.parentNode.className = "has-submenu";
			this.parentNode.querySelector('ul').setAttribute('aria-expanded', "false");
			this.parentNode.querySelector('ul').setAttribute('aria-hidden', "true");
		}
		event.preventDefault();
	});
});

// https://stackoverflow.com/questions/1248081/how-to-get-the-browser-viewport-dimensions
var menu = document.getElementById("menu"); 
var menu_toggle = document.getElementById("menu-toggle"); 
if (window.innerWidth <= 767) {
	menu.setAttribute("aria-expanded", "false");
	menu.parentNode.style.display = "none"; 
}

window.addEventListener("resize", function(event) {
	console.log(screen.width);
	if (window.innerWidth <= 767) {
		menu.setAttribute("aria-expanded", "false");
		menu.parentNode.style.display = "none"; 
	} else {
		menu.setAttribute("aria-expanded", "true");
		menu.parentNode.style.display = "block"; 
	}
}, true);

menu_toggle.addEventListener("click", function(event) {
	if (menu.parentNode.style.display == "none") {
		menu.setAttribute("aria-expanded", "true");
		menu.parentNode.style.display = "block"; 
	} else {
		menu.setAttribute("aria-expanded", "false");
		menu.parentNode.style.display = "none"; 
	}
});
