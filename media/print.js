$(document).ready(function() {
	$(".articlelink").click(function(event) {
		event.preventDefault();
        var id = "." + $(this).attr("id");
		var target = $(id).filter("div");
		if (target.hasClass("visible")) {
            $(id).removeClass("visible");
			target.hide();
		} else {
			$(".visible").removeClass("visible");
			$(".hidden-snippet").hide();
            $(id).addClass("visible").show();
		}
	});
});
