$(document).ready(function(){
	$('.exdone').click(exdone);
	$('.sessdone').click(sessdone);

	$('.plusbtn').click(function(e){weightbtn(e,+1)});
	$('.minusbtn').click(function(e){weightbtn(e,-1)});
});

function exdone(e) {
	var el = $(e.currentTarget);
	var exkey = el.siblings('[name="exkey"]').val()
	$.get('/train/?exdone='+exkey);
	el.toggleClass('disabled');
}

function sessdone(e) {
	var key = $(e.currentTarget).parents('div.client').children('input[name="sesskey"]').val()
	$.get('/train/?done='+key);
	$(e.currentTarget).toggleClass('disabled');
}

function weightbtn (e,delta) {
	var el = $(e.currentTarget);
	var input = el.siblings('input[name="nextweight"]');
	var w = input.val();
	if (w) {
		var exkey = el.siblings('[name="exkey"]').val();
		var newval = parseFloat(w)+parseInt(delta);
		$.get('/train/?ex='+exkey+'&next='+newval);
		input.val(newval);
	}
}
