$(document).ready(function() {

	if (window.location.pathname == "/test")
		return;

	var TAG_NORMAL = $("#alltags").width();
	var TAG_EXPANDED = TAG_NORMAL + 13;
	var IFRAME = $("iframe").size() > 0;
	State.init(TAG_NORMAL, TAG_EXPANDED, IFRAME, function() {
		$("a").filter(".list-hider").unbind().click(function(event) {
			event.preventDefault();
			$(".alist").show("slow");
			$(".list-hider").hide();
		});
		$("a").filter(".poll").unbind().click(function(event) {
			if (event.ctrlKey || event.shiftKey)
				return;
			event.preventDefault();
			var choice_id = $(this).attr("id").substring(7); // choice_
			State.submit_poll(choice_id);
		});
		$("a").filter(".embeddable").unbind().click(function(event) {
			if (event.ctrlKey || event.shiftKey)
				return;
			event.preventDefault();
			State.current().enter($(this));
			State.scrollup();
		});
		$(".paginator .pagelink").unbind().click(function(event) {
			if (event.ctrlKey || event.shiftKey)
				return;
			event.preventDefault();
			State.current().page($(this).attr("id").substring(2)).enter($("#" + $(this).attr("id") + " a"));
			State.scrollup();
		});
		$("#goto_top").unbind().click(function() {
			window.scroll(0,0);
		});
	});

	// delete noscript compatibility links
	$(".paginator .pagelink a").map(function() {
		var stripped = $(this).attr("href").substring($(this).attr("href").search("#"));
		$(this).attr("href", stripped);
	});

	// redirect to hash id if possible for better functionality
	if (window.location.pathname != "/") {
		location.replace("/" + new State(window.location.pathname));
		return;
	}

	var selecting_dates = false;
	var down = false;
	$("#tags #alltags").width(TAG_EXPANDED);
	$("#tags").disableTextSelect();
	$("#dates").disableTextSelect();

	if (window.location.hash.length > 1) { // permalink and not lone '#'
		$(".results").hide();
		new State(window.location.hash).noqueue().enter();
	}

	/* HISTORY BEGINS - all State changes must be done */
	State.init_history_monitor();

	$("#tags li").not("#alltags").click(function(event) {
		if (event.ctrlKey || event.shiftKey)
			return;
		event.preventDefault();
		if ($(this).hasClass("useless") && !$(this).hasClass("activetag"))
			$("#tags .activetag").not("#alltags").removeClass("activetag");
		tagslug = $(this).attr("id");
		if ($(".embed").is(":visible"))
			$(this).removeClass("activetag");
		$(this).removeClass("useless").toggleClass("activetag");
		State.current().enter();
		State.scrollup();
	});

	$("#tags #alltags").click(function(event) {
		event.preventDefault();
		$("#dates li").removeClass("activedate");
		selecting_dates = false;
		$("#tags li").removeClass("useless");
		$("#tags .activetag").removeClass("activetag");
		State.current().enter();
		State.scrollup();
	});

	$("#tags li a").click(function(event) {
		if (event.ctrlKey || event.shiftKey)
			return;
		event.preventDefault();
	});

	$("#dates h3").click(function(event) {
		event.preventDefault();
		var min = ($(this).text().substring(5) - 1) + "08";
		var max = $(this).text().substring(5) + "07"; // year_
		var some_newly_selected = false;
		if (!State.select_dates(min, max)[0])
			$("#dates li").removeClass("activedate");
		State.current().enter();
	});

	$("#dates li li").mousedown(function() {
		if (!selecting_dates) {
			if ($(this).hasClass("activedate"))
				down = $(this).attr("id");
			else
				down = false;
			$("#dates li").removeClass("activedate");
			$(this).addClass("activedate");
			selecting_dates = true;
		}
	});

	$("#dates li li").mousemove(function() {
		if (selecting_dates)
			$(this).addClass("activedate");
	});

	$("#dates li").mouseup(function() {
		if (down == $(this).attr("id")) {
			$(this).removeClass("activedate");
		} else if (selecting_dates) {
			$(this).addClass("activedate");
		}
		if (selecting_dates) {
			selecting_dates = false;
			State.current().enter();
		}
	});

	$(document).mouseup(function(event) {
		if (selecting_dates) {
			selecting_dates = false;
			State.current().enter();
		}
	});

	if ($.browser.msie) {
		$('#tags li').animate({'width':'+=0'}); // hover only works after this...
		$('#tags li').hover(function() {
			if (!$(this).hasClass("useless"))
				$(this).css('filter','alpha(opacity=80)');
			else
				$(this).css('cursor','default');
		}, function() {
			$(this).css('filter','alpha(opacity=100)');
			$(this).css('cursor','pointer');
		});
	}
});
