/**
 * CALENDARIO
 */
openerp.website.if_dom_contains('#calendar', function(){
	
	// Cargar Calendario
	refresh_calendar_events();
	
	$(document).on('click', '.delete-event', function(ev){
		var $this = $(this);
		var event_id = $this.data('event-id');
		console.log(event_id);
		
		if (confirm("¿Seguro que quiere borrar el evento?\n\nEsta acción no se puede deshacer."))
			delete_event(event_id);
		
		ev.preventDefault();
	});
	
	// Ventana Nuevo Evento
	$(document).on('click', '#event-new', function(){
		window.scrollTo(0, 0); // Para que el datepicker se muestre correctamente
		$modal = $('#modalCalendarNewEvent');
		$modal.data('start_date', moment());
		$modal.data('end_date', moment().add(2, 'hours'));
		$modal.data('title', '');
		$modal.data('allday', true);
		$modal.data('id', -1);
		$modal.modal('show');
	});
	
	$('#modalCalendarNewEvent').modal({
		'show':false,
		'backdrop': false
	});
	$('#modalCalendarNewEvent').on('show.bs.modal', function(e){
		$modal = $(this);
		start_date = $modal.data('start_date');
		end_date = $modal.data('end_date');
		
		start_date = start_date;
		end_date = end_date;
		
		title = $modal.data('title');
		id = $modal.data('id');
		allday = $modal.data('allday');
		is_new = (id===-1);
		
		$modal.find('#event-name').val(title);
		$modal.find('#event-starts').data("DateTimePicker").date(start_date);
		$modal.find('#event-ends').data("DateTimePicker").date(end_date);
		$modal.find('#event-allday').prop('checked', allday);
		
		$modal.find('.modal-title').text(is_new?'Nuevo Evento':'Modificar Evento');
		$modal.find('button.btn-primary').text(is_new?'Crear':'Modificar');
		$modal.find('#event-delete').css('display', is_new?'none':'inline');
		setTimeout(function(){ $modal.find('#event-name').focus(); }, 500);
	});
	$('#modalCalendarNewEvent .btn-primary').on('click', function(){
		$modal = $('#modalCalendarNewEvent');
		
		start_date = $modal.find('#event-starts').data("DateTimePicker").date().utc();
		end_date = $modal.find('#event-ends').data("DateTimePicker").date().utc();
		title = $modal.find('input#event-name').val();
		allday = $modal.find('input#event-allday').prop('checked');
		id = $modal.data('id');
		
		uc_event({
			'id': id,
			'start': start_date,
			'end': end_date,
			'allDay': allday,
			'title': title
		});
		$('#modalCalendarNewEvent').modal('hide');
	});
	
    $('.date').datetimepicker({
    	locale: 'es',
    	useCurrent: false //Important! See issue #1075
    });
    $("#event-starts").on("dp.change", function (e) {
        $('#event-ends').data("DateTimePicker").minDate(e.date);
    });
    $("#event-ends").on("dp.change", function (e) {
        $('#event-starts').data("DateTimePicker").maxDate(e.date);
    });
});

// Borrar Evento
function delete_event(event_id)
{
	openerp.jsonRpc('/calendario/delete_event', 'call', {'id':event_id}).then(function(data){
		if (!data['error'])
			refresh_calendar_events();
	});
}

//Actualizar o crear evento
function uc_event(event, _revertFunc)
{
	isNew = (event.id===-1);
	ev = get_event_data(event);
	openerp.jsonRpc('/calendario/uc_event', 'call', ev).then(function(data){
		if (data['error'])
		{
			if (!isNew)
				_revertFunc();
		}
		else
		{			
			refresh_calendar_events();
		}
	});
}

// Generar Lista HTML
function refresh_calendar_events()
{
	openerp.jsonRpc('/calendario/get_events', 'call', {}).then(function(data){
		if (!data['error'])
		{
			var curdate = moment().utc();
			var group_dates = {};
			
			// Generar Grupos de Fechas
			for (var i in data)
			{
				var sdate = moment(moment.utc(data[i].start).toDate());
				var edate = moment(moment.utc(data[i].end).toDate());

				if ((data[i].allDay && sdate.isBefore(curdate.clone().startOf('day'))) || edate.isBefore(curdate))
					continue;
				
				var diff_date = 0;
				if (!data[i].allDay)
					diff_date = edate.diff(sdate, 'days');
				
				for (var e=0; e<=diff_date; e++)
				{
					var base_date = sdate.clone().add(e,'days');
					var strdate = base_date.format('DD/MM/YYYY');
					if (!(strdate in group_dates))
						group_dates[strdate] = new Array();
					group_dates[strdate].push(data[i]);
				}
			}

			// Generar HTML
			var keys = Object.keys(group_dates).sort(sort_moment_dates);
			var html = "";
			for (var i in keys)
			{
				var groupdate = keys[i];
				html += "<h4 class='mobile-calendar-date'>"+groupdate+"</h4>";
				for (var e in group_dates[groupdate])
				{
					var sdate = moment(moment.utc(group_dates[groupdate][e].start).toDate());
					var edate = moment(moment.utc(group_dates[groupdate][e].end).toDate());
					
					var sdate_finish = sdate.isBefore(curdate);
					var edate_finish = edate.isBefore(curdate);
					var running = sdate_finish && !edate_finish;
					
					html += "<div class='row mobile-calendar-event' id='event-"+group_dates[groupdate][e].id+"'>";
					html += "<div class='col-md-12 bg-"+(running?"warning":"primary")+" mobile-calendar-title'>";
					html += "<strong>"+group_dates[groupdate][e].title+"</strong>";
					html += "<a class='btn btn-danger btn-xs pull-right delete-event' style='border-radius:0 !important;' href='#' data-event-id='"+group_dates[groupdate][e].id+"'><i class='fa fa-trash'></i></a>";
					html += "</div>";
					html += "<div class='col-md-6 bg-"+(sdate_finish?'danger':'success')+" mobile-calendar-start'>Inicio: "+sdate.format('DD/MM/YYYY HH:mm:ss')+"</div>";
					html += "<div class='col-md-6 bg-"+(edate_finish?'danger':'success')+" mobile-calendar-end'>Fin: "+(group_dates[groupdate][e].allDay?"Todo el día":edate.format('DD/MM/YYYY HH:mm:ss'))+"</div>";
					html += "</div>";
				}
			}
			$('#calendar').html(html);
		}
	});
}

function sort_moment_dates(a, b)
{
    var x = moment(a,'DD/MM/YYY'); 
    var y = moment(b,'DD/MM/YYY'); 
    return ((x.isBefore(y)) ? -1 : ((y.isBefore(x)) ? 1 : 0));
}
