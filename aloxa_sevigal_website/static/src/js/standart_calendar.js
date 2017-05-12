/**
 * CALENDARIO
 */
openerp.website.if_dom_contains('#calendar', function(){
	
	$('#calendar').fullCalendar({
		lang: 'es',
		header: {
			left: 'prev,next today',
			center: 'title',
			right: 'month,agendaWeek,agendaDay'
		},
		editable: true,
		eventLimit: true, // allow "more" link when too many events
		droppable: true,
		selectHelper: true,
		selectable: true,
		unselectAuto: false,
		defaultView: get_responsive_calendar_view(),
		timezone: 'local',
		/*eventRender: function(event, el) {
			console.log("Color Evento: " + event.color)
		},*/
		
		// Callbacks
        eventDrop: function (event, _delta, _revertFunc) {
            uc_event(event, _revertFunc);
        },
        eventResize: function (event, _delta, _revertFunc) {
        	var diffdays = event.end.diff(event.start, 'day');
			event.allDay = (!event.end.hasTime()&&diffdays==1);
        	uc_event(event, _revertFunc);
        },
		eventClick: function(event) {
			$modal = $('#modalCalendarNewEvent');
			$modal.data('start_date', event.start);
			if (!event.end) {
				event.end = event.start;
				event.end.add(1, 'days');
			}
			$modal.data('end_date', event.end);
			$modal.data('title', event.title);
			$modal.data('allday', event.allDay);
			$modal.data('id', event.id);
			$modal.modal('show');
		},
		select: function (start_date, end_date) {
			if (start_date.isBefore(moment().utc()))
			{
				$('#calendar').fullCalendar('unselect');
				return;
			}
			
			var diffdays = end_date.diff(start_date, 'day');
			$modal = $('#modalCalendarNewEvent');
			$modal.data('start_date',start_date);
			$modal.data('end_date', end_date);
			$modal.data('allday', (!end_date.hasTime()&&diffdays==1));
			$modal.data('title', '');
			$modal.data('id', -1);
			$modal.modal('show');
        }
	});
	
	// Poner la vista mas adecuada al tamaño de la pantalla
	$(window).resize(function(){
		$('#calendar').fullCalendar('changeView', get_responsive_calendar_view());
	});
	
	// VENTANA NUEVO/MODIFICAR EVENTO
	$('#modalCalendarNewEvent').modal({
		'show':false,
		'backdrop': false
	});

	$('#modalCalendarNewEvent').on('hide.bs.modal', function(e){
		$('#calendar').fullCalendar('unselect');
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
	$('#modalCalendarNewEvent #event-delete').on('click', function(){
		id = $modal.data('id');
		title = $modal.data('title');
		if (confirm("¿Seguro que quiere borrar el evento '"+title+"'?\n\nEsta acción no se puede deshacer."))
		{
			delete_event(id);
			$('#modalCalendarNewEvent').modal('hide');
		}
	});
	
	// DATE TIME PICKERS
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
	
	// Cargar Calendario
	refresh_calendar_events();
	
});

/**
 * OBTENER VISTA OPTIMA PARA EL CALENDARIO
 */
function get_responsive_calendar_view()
{
	var win = $(window);
	if (win.width() < 600)
		return 'agendaDay';
	else if (win.width() < 1200)
		return 'agendaWeek';
	return 'month';
}


/**
 * RPC
 */
// Actualizar o crear evento
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
// Obetener eventos
function refresh_calendar_events()
{
	openerp.jsonRpc('/calendario/get_events', 'call', {}).then(function(data){
		if (!data['error'])
		{
			for (i in data)
			{
				data[i].start = moment.utc(data[i].start);
				data[i].end = moment.utc(data[i].end);
			}
			
			$('#calendar').fullCalendar('removeEvents');
	        $('#calendar').fullCalendar('addEventSource', data);         
	        $('#calendar').fullCalendar('rerenderEvents');
		}
	});
}
// Borrar evento
function delete_event(event_id)
{
	openerp.jsonRpc('/calendario/delete_event', 'call', {'id':event_id}).then(function(data){
		if (!data['error'])
			refresh_calendar_events();
	});
}
