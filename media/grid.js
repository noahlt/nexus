$(document).ready(function() {

	function is_nonlocal(event) {
		return event.ctrlKey || event.shiftKey
		|| (!$.browser.msie && event.button == 1); // not IE; chrome fix
	}

	var TAG_NORMAL = $("#alltags").width();
	var TAG_EXPANDED = TAG_NORMAL + 13;
	var IFRAME = $("iframe").size() > 0; // XXX
	var STATIC_FRONTPAGE = $("#config_static").size() > 0; // XXX
	State.init(TAG_NORMAL, TAG_EXPANDED, IFRAME, STATIC_FRONTPAGE);

	function hash_of(url) { // IE6 YET AGAIN
		return url.substring(url.indexOf("#"));
	}

	$("a.list-hider").live("click", function(event) {
		event.preventDefault();
		$(".alist").show("slow");
		$(".list-hider").hide();
	});

	$("a.poll").live("click", function(event) {
		if (is_nonlocal(event))
			return;
		event.preventDefault();
		var choice_id = hash_of($(this).attr("href")).substring(8); // #choice_
		State.submit_poll(choice_id, $(this));
	});

	$("a.poll_results_only").live("click", function(event) {
		if (is_nonlocal(event))
			return;
		event.preventDefault();
		var poll_id = hash_of($(this).attr("href")).substring(6); // #poll_
		State.get_poll(poll_id, $(this));
	});

	$("a.embeddable").live("click", function(event) {
		if (is_nonlocal(event))
			return;
		event.preventDefault();
		State.current().enter($(this));
		State.scrollup();
	});

	$(".paginator .pagelink a").live("click", function(event) {
		if (is_nonlocal(event))
			return;
		event.preventDefault();
		State.current().page($(this).attr("id").substring(2)).enter($("#" + $(this).attr("id") + " a"));
		State.scrollup();
	});

	$("#goto_top").live("click", function() {
		window.scroll(0,0);
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
		setVisible("none");
		new State(window.location.hash).noqueue().enter();
	}

	/* HISTORY BEGINS - all State changes must be done */
	State.init_history_monitor();

	$("#tags li").not("#alltags").click(function(event) {
		if (is_nonlocal(event))
			return;
		event.preventDefault();
		if ($(this).hasClass("useless") && !$(this).hasClass("activetag"))
			$("#tags .activetag").not("#alltags").removeClass("activetag");
		tagslug = $(this).attr("id");
		if (!$(".results").is(":visible"))
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
		if (is_nonlocal(event))
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
