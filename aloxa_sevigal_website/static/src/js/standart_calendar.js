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
		//timezone: 'local',
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
			$modal.data('start_date', event.start.clone().utc());
			if (!event.end) {
				event.end = event.start;
				if (!event.allDay) {
					event.end.add(1, 'days');
				}
			}
			$modal.data('end_date', event.end.clone().utc());
			$modal.data('title', event.title || '');
			$modal.data('allday', event.allDay);
			$modal.data('desc', event.description || '');
			$modal.data('id', event.id);
			$modal.modal('show');
		},
		select: function (start_date, end_date) {
			if (start_date.isBefore(moment()))
			{
				$('#calendar').fullCalendar('unselect');
				alert('No se pueden crear eventos en el pasado!');
				return;
			}

			end_date.subtract(1, 'm');

			var diffdays = end_date.clone().startOf('day').diff(start_date.clone().startOf('day'), 'day');
			$modal = $('#modalCalendarNewEvent');
			$modal.data('start_date', start_date.clone().utc());
			$modal.data('end_date', end_date.clone().utc());
			$modal.data('allday', !diffdays);
			$modal.data('title', '');
			$modal.data('desc', '');
			$modal.data('id', -1);
			$modal.modal('show');
    },
		dayMousedown: function(ev) {
			if (date.isBefore(moment().utc())) {
				$(this).css('background-color', 'red');
			}
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

	$('#modalCalendarNewEvent #event-allday').on('change', function(e){
		$('#event-starts').data("DateTimePicker").format(e.target.checked?'DD/MM/YYYY':'DD/MM/YYYY H:mm');
		$('#event-ends').data("DateTimePicker").format(e.target.checked?'DD/MM/YYYY':'DD/MM/YYYY H:mm');
	});
	$('#modalCalendarNewEvent').on('hide.bs.modal', function(e){
		$('#calendar').fullCalendar('unselect');
	});
	$('#modalCalendarNewEvent').on('show.bs.modal', function(e){
		$modal = $(this);
		start_date = $modal.data('start_date');
		end_date = $modal.data('end_date');

		title = $modal.data('title');
		desc = $modal.data('desc');
		id = $modal.data('id');
		allday = $modal.data('allday');
		is_new = (id===-1);

		var $dtpEnd = $modal.find('#event-ends');
		var $dtpStart = $modal.find('#event-starts');
		$dtpEnd.data("DateTimePicker").minDate(false);
		$dtpStart.data("DateTimePicker").maxDate(false);
		$dtpStart.data("DateTimePicker").date(start_date);
		$dtpEnd.data("DateTimePicker").date(end_date);

		$modal.find('#event-name').val(title);
		$modal.find('#event-desc').val(desc);
		$modal.find('#event-allday').prop('checked', allday).change();
		$modal.find('.modal-title').text(is_new?'Nuevo Evento':'Modificar Evento');
		$modal.find('button.btn-primary').text(is_new?'Crear':'Modificar');
		$modal.find('#event-delete').css('display', is_new?'none':'inline');
		setTimeout(function(){ $modal.find('#event-name').focus(); }, 500);
	});
	$('#modalCalendarNewEvent .btn-primary').on('click', function(){
		$modal = $('#modalCalendarNewEvent');

		start_date = $modal.find('#event-starts').data("DateTimePicker").date().clone();
		end_date = $modal.find('#event-ends').data("DateTimePicker").date().clone();
		title = $modal.find('input#event-name').val();
		desc = $modal.find('input#event-desc').val();
		allday = $modal.find('input#event-allday').prop('checked');
		id = $modal.data('id');

		ev_vals = {
			'id': id,
			'start': start_date,
			'end': end_date,
			'allDay': allday,
			'title': title,
			'description': desc,
		};
		if (allday) {
			ev_vals['end'] = start_date;
		}
		uc_event(ev_vals);
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
    	useCurrent: false, //Important! See issue #1075
			format: 'DD/MM/YYYY H:mm'
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
