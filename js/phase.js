var phasekey;
var phasetimeout;
var hwtimeout;

$(document).ready(function(){
	phasekey = $('#phase').val();
	
	$('#editcat-btn').click(function(){openmodal('editcat')});
	$('#editex-btn').click(function(){openmodal('editex')});
	$('#editeq-btn').click(function(){openmodal('editeq')});
	
	$('.cancel').click(function(){$('.modalwindow').modal('hide');});

	$('#special').click(function(){$('#specialwindow').modal('show')});
	
	$('#editcat').find('form').submit(addcat);
	$('#editex').find('form').submit(addex);
	$('#editeq').find('form').submit(addeq);
	$('.remove-btn').click(remove);
	
	$('#form select, #form input').bind('change keyup',send);
	$('#hw input').keyup(sendhw);
	
	$(document).ajaxStart(function(){
		$('button').attr('disabled','disabled');
	});
	
	$('.copyfrom').click(copyfrom);
});

function ajaxfinished(){
	$('button').removeAttr('disabled');
}

function openmodal(whichone) {
	$('#'+whichone).modal('show');
	return false;
}

function addcat(e) {
	var modal = $('#')
	var name = $('#newcatname').val();
	$.post(
		'/types/add/category',
		{'name':name},
		function(key){
			$('select[name="category"]').each(function(i,v){
				$(v).append($('<option value="'+key+'">'+name+'</option>'));
			});
			ajaxfinished();
		}
	);
	$('#newcatname').val('');
	return false;
}

function addeq(e) {
	var modal = $('#editeq');
	var input = modal.find('input[name="name"]');
	var name = input.val();
	$.post(
		'/types/add/equipment',
		{'name':name},
		function(key){
			$('select[name="equipment"]').each(function(i,v){
				$(v).append($('<option value="'+key+'">'+name+'</option>'));
			});
			ajaxfinished();
		}
	);
	input.val('');
	return false;
}

function addex(e) {
	var name = $('#newexname').val();
	var catkey = $('#catchoice').val();
	$.post(
		'/types/add/exercise',
		{'name':name,'category':catkey},
		function(key){
			$('input[name="phasecatkey"][value="'+catkey+'"]').siblings('select[name="exercise"]').each(function(i,v){
				$(v).append($('<option value="'+key+'">'+name+'</option>'));
			});
			ajaxfinished();
		}
	);
	$('#newexname').val('');
	return false;
}

function remove(e) {
	var key = $(e.currentTarget).siblings('select').val();
	$.post('/types/del/',{'key':key},function(){ajaxfinished()});
	$('option[value="'+key+'"]').remove();
	return false;
}


function send(e) {
	clearTimeout(phasetimeout);
	var ms = 500;
	if (e.type == 'change') ms = 0;
	phasetimeout = setTimeout(function() {
		var cl = $(e.currentTarget).closest('td').attr('class');
		var data = {};
		$(e.currentTarget).closest('tr').children('td.'+cl).children('input, select').each(function(i,v){
			console.log(v.name);
			data[v.name] = v.value;
		});
		$.post('/phase/'+phasekey,data,function(html){
			console.log(html);
			ajaxfinished();
		});
	}, ms);
}

function sendhw(e) {
	clearTimeout(hwtimeout);
	hwtimeout = setTimeout(function(){
		var data = {};
		var form = $('#hw');
		form.find('input').each(function(i,v){
			data[v.name] = v.value;
		});
		$.post(form.attr('action'),data,function(){ajaxfinished()});
	}, 500);
}

function copyfrom(e) {
	var phasekey = $('#phasekey').val();
	var el = $(e.currentTarget);
	var id = el.siblings('input[name="clientid"]').val();
	$('#clonewindow').modal('show');
	var ul = $('#clonelist');
	var model = ul.children('li').first();
	ul.children('li').remove();
	$.get('/client/'+id,{phases:1},function(json){
		// console.log(json.length);
		$('#copyname').text(json.client);
		var p = json.phases;
		for (i=0; i<p.length; i++) {
			ul.append('<li><a href="/phase/'+phasekey+'?clone='+p[i].clientid+'&phase='+p[i].key+'">'+p[i].order+'. '+p[i].name+'</a></li>');		
		}
	},'json');
	return false;
}
