// https://www.w3.org/WAI/tutorials/menus/flyout/
var menuItems = document.querySelectorAll('li.has-submenu');
var timer;
Array.prototype.forEach.call(menuItems, function(el, i){
	el.addEventListener("mouseover", function(event){
		this.className = "has-submenu open";
		clearTimeout(timer);
	});
	el.addEventListener("mouseout", function(event){
		timer = setTimeout(function(event){
			var opened_submenu = document.querySelector(".has-submenu.open");
			if(opened_submenu) {
				opened_submenu.className = "has-submenu";
			}
		}, 1000);
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
