$(document).ready(function() {
    var have_articles = $("#results li h3").map(function() {
        return $(this).attr("className");
        }).get();

    $("#toggleprint").click(function(event) {
        event.preventDefault();
        if ($(this).text()[0] == 'c') {
            $("#print").hide();
            $(this).html("expand &darr;");
        } else {
            $(this).html("collapse &uarr;");
            $("#print p").show();
        }
        });

    function update_stats(stats) {
		document.getElementById('remaining').innerHTML = stats['remaining'];
		document.getElementById('total').innerHTML = stats['total'];
		document.getElementById('remainwrapper').style.display =
			stats['remaining'] > 0 ? '' : 'none';
    }

    function update_tags(subtags) {
        $("#tags li").not("#alltags").map(
            function() {
                for (var i in subtags)
                    if ($(this).attr("id") == subtags[i]) {
                        $(this).show();
                        return;
                    }
                $(this).hide();
            }
        )
    }

    function get_articles(selectedtags) {
        $.get("/ajax/more_articles",
            {"tagslugs": selectedtags, "have_articles": have_articles},
            function (responseData) {
				update_stats(responseData['stats']);
                update_tags(responseData['tags'])
                for (var i in responseData['articles']) {
                    var article = responseData['articles'][i];
                    $("#results").append(article['html']);
                    have_articles[have_articles.length] = article['slug'];
                }
                $(".new-article")
                      .show()
                      .removeClass("new-article");
              },
              "json");
    }

    function update_ui(selectedtags) {
        $.get("/ajax/stat_articles",
            {"tagslugs": selectedtags, "have_articles": have_articles},
			function(responseData) {
                update_stats(responseData['stats']);
                update_tags(responseData['tags']);
            }, "json");
    }

    // this selector may have to be changed to be more specific
    $("#grid .controllink").click(function(event) {
        event.preventDefault();
        var selectedtags = $("#tags li").filter(".activetag").not("#alltags")
            .map(function() {
                    return $(this).attr("id");
                }).get();
        get_articles(selectedtags);
        });

    $("#tags li")
        .not("#alltags")
        .click(function() {
            tagslug = $(this).attr("id");
            $(this).toggleClass("activetag");
            var selectedtags = $("#tags li").filter(".activetag")
                .map(function() {
                        return $(this).attr("id");
                    }).get();

            if ($(this).hasClass("activetag")) {
                $(this).animate({width: "+=14px", }, 200);
                $("#results li")
                    .not("."+tagslug)
                    .hide();
                $("#tags #alltags").removeClass("activetag");
                get_articles(selectedtags);

            } else {
                $(this).animate({width: "-=14px", }, 200);
                $("#results li")
                    .not("."+tagslug)
                    .filter(function(i) {
                            for (var j in selectedtags) {
                                if (!$(this).hasClass(selectedtags[j])) {
                                    return false;
                                }
                            }
                            return true;
                        })
                    .show();
                if (!$("#tags li").hasClass("activetag")) {
                    $("#tags #alltags").addClass("activetag");
                }
                update_ui(selectedtags);
            }
            });

    $("#tags #alltags").click(function() {
        $(this).addClass("activetag");
        $("#tags li").show();
        $("#tags .activetag").not("#alltags")
            .removeClass("activetag")
            .animate({width: "-=14px",}, 200);
        $("#results li").show();
        });

    $("#tags li a").click(function(event) {
            event.preventDefault();
        });

	document.onkeypress = function(e) {
		var e = window.event || e
		var keyunicode = e.charCode || e.keyCode
		if (keyunicode == 8 && !$("#alltags").hasClass("activetag")) {
			$("#alltags").click();
			return false;
		}
		return true;
	}

});
