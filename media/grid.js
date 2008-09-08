$(document).ready(function() {

	function __update_tags(taginfo) {
		$("#tags li").not("#alltags").map(
			function() {
				for (var i in taginfo) {
					if ($(this).attr("id") == taginfo[i][0]) {
						if (!taginfo[i][1])
							$(this).addClass("useless");
						else
							$(this).removeClass("useless");
						return;
					}
				}
				$(this).addClass("useless");
			}
		);
	}

	function __update_results(results) {
		$("#results li").not("#IE6_PLACEHOLDER").remove();
		for (var i in results)
			$("#results").append(results[i]);
	}

	function __update_paginator(pages) {
		$("#paginator").empty();
		if (pages['num_pages'] > 1) {
			for (var i = 1; i <= pages['num_pages']; i++) {
				if (i == pages['this_page'])
					$("#paginator").append("\n<li>" + i + "</li>");
				else
					$("#paginator").append("\n<li id=\""
					+ i + "\" class=\"pagelink\" href=\"#paginator\"><a>"
					+ i + "</a></li>");
			}
		}
		$("#paginator .pagelink").click(function(event) {
			event.preventDefault();
			update($(this).attr("id"));
		});
	}

	function update(page) {
		var selectedtags = $("#tags li").filter(".activetag").not("#alltags")
			.map(function() {
					return $(this).attr("id");
				}).get();
		$.get("/ajax/paginator",
			{"tags": selectedtags, "page": page},
			function(responseData) {
				__update_tags(responseData['tags']);
				__update_results(responseData['results']);
				__update_paginator(responseData['pages']);
			}, "json");
	}

	$("#paginator .pagelink").click(function(event) {
		event.preventDefault();
		update($(this).attr("id"));
	});

	$("#tags li").not("#alltags").click(function() {
		if ($(this).hasClass("useless"))
			$("#tags .activetag").not("#alltags")
				.removeClass("activetag")
				.width($(this).width()); // XXX
		tagslug = $(this).attr("id");
		$(this).removeClass("useless");
		$(this).toggleClass("activetag");
		if ($(this).hasClass("activetag")) {
			$(this).width($(this).width() + 13);
			$("#tags #alltags").removeClass("activetag");
		} else {
			$(this).width($(this).width() - 13);
			if (!$("#tags li").hasClass("activetag"))
				$("#tags #alltags").addClass("activetag");
		}
		update(1);
	});

	$("#tags #alltags").click(function() {
		$(this).addClass("activetag");
		$("#tags li").removeClass("useless");
		$("#tags .activetag").not("#alltags")
			.removeClass("activetag")
			.width($(this).width() - 13); // XXX
		update(1);
	});

	$("#tags li a").click(function(event) {
		event.preventDefault();
	});

	document.onkeypress = function(x) {
		var e = window.event || x;
		var keyunicode = e.charCode || e.keyCode;
		if (keyunicode == 8 && !$("#alltags").hasClass("activetag")) {
			$("#alltags").click();
			return false;
		}
		return true;
	};
});
