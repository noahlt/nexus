$(document).ready(function() {
    var have_articles = $("#results li h3").map(function() {
        return $(this).attr("className");
        }).get();

    function update_stats(stats) {
        document.getElementById('remaining').innerHTML = stats['remaining'];
        document.getElementById('total').innerHTML = stats['total'];
        document.getElementById('remainder').style.display =
            stats['remaining'] > 0 ? '' : 'none';
    }

    function update_tags(taginfo) {
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

    function get_articles(selectedtags) {
        $.get("/ajax/more_articles",
            {"tagslugs": selectedtags, "have_articles": have_articles},
            function (responseData) {
                update_stats(responseData['stats']);
                update_tags(responseData['tags']);
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
            if ($(this).hasClass("useless")) {
                $("#tags .activetag").not("#alltags")
                    .removeClass("activetag")
					.width($(this).width()); // XXX
                $("#results li").show();
            }
            tagslug = $(this).attr("id");
            $(this).removeClass("useless");
            $(this).toggleClass("activetag");
            var selectedtags = $("#tags li").filter(".activetag")
                .map(function() {
                        return $(this).attr("id");
                    }).get();

            if ($(this).hasClass("activetag")) {
                $(this).width($(this).width() + 13);
                $("#tags #alltags").removeClass("activetag");
                get_articles(selectedtags);
                $("#results li")
                    .not("."+tagslug)
					.not("#IE6_PLACEHOLDER")
                    .hide();
            } else {
                $(this).width($(this).width() - 13);
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
        $("#tags li").removeClass("useless");
        $("#tags .activetag").not("#alltags")
            .removeClass("activetag")
			.width($(this).width() - 13); // XXX
        $("#results li").show();
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
