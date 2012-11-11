var timeout;
var clientkey;
var currenttype;

$(document).ready(function(){
	clientkey = $('#clientkey').val();

	$('#editphasetype').click(function(){openmodal('phasetype')});
	$('#editsetuptype').click(function(){openmodal('setuptype')});
	$('#edittempotype').click(function(){openmodal('tempotype')});
	
	$('#cancel').click(function(){$('#edittype').modal('hide');});
	$('#typeform').submit(addtype);
	$('#removetype').click(removetype);
	
	$('tr').bind('change keyup',send);
	
	$(document).ajaxStart(function(){
		$('button').attr('disabled','disabled');
	});

	$('#special').click(function(){$('#specialwindow').modal('show')});

	$('.deletebtn').click(function(){ return confirm('Delete ?')});
});

function ajaxfinished(){
	$('button').removeAttr('disabled');
}


function openmodal(type) {
	currenttype = type;
	$('#types').children().remove();
	$('#types').append($('.'+type).first().children().clone());
	$('#edittype').modal('show');
}

function addtype(e) {
	var val = $('#newtypename').val();
	$.post(
		'/types/add/'+currenttype,
		{'name':val},
		function(key){
			$('select.'+currenttype+', select#types').each(function(i,v){
				$(v).append($('<option value="'+key+'">'+val+'</option>'));
			});
			ajaxfinished();
		}
	);
	$('#newtypename').val('');
	// $('#edittype').modal('hide');
	
	return false;
}

function removetype(e) {
	var key = $('#types').val();
	$.post('/types/del/',{'key':key},function(){ajaxfinished();});
	$('option[value="'+key+'"]').remove();
	// $('#edittype').modal('hide');
}


function send (e) {
	clearTimeout(timeout);
	var ms = 500;
	if (e.type == 'change') ms = 0;
	timeout = setTimeout(function(){
		var data = {};
		$(e.currentTarget).find("input,select").each(function(i,v){
			data[v.name] = v.value;
		});
		$.post('/program/'+clientkey,data,function(html){
			console.log(html);
			ajaxfinished();
		});
	},ms);
	
	// var canadd = true;
	// $('select[name="phase"]').each(function(i,v){
	// 	canadd &= v.value != '';
	// });
	// if (canadd) {
	// 	addline();
	// }
}

// function addline(){
	// var content = $('tr:last').clone();
	// content.find('input,select').each(function(i,v){
		// v.value = '';
	// });
	// content.find()
	// $('tr:last').after(content);
// }

// function move(e,mod) {
	// var row = e.parentUntil('tbody');
	// key = row.find('input[name="key"]').val();
	// $.get(
		// '/program/'+clientkey,
		// {'mod':mod,'move':key}
	// );
// }
