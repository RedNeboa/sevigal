/*
 * ODOO
 */
var _t = openerp._t;

/*
 * EXTENDER JQUERY CON METODOS UTILES
 */
$.fn.is_on_screen = function(){

    var win = $(window);

    var viewport = {
        top: win.scrollTop(),
        left: win.scrollLeft()
    };
    viewport.right = viewport.left + win.width();
    viewport.bottom = viewport.top + win.height();

    var bounds = this.offset();
    bounds.right = bounds.left + this.outerWidth();
    bounds.bottom = bounds.top + this.outerHeight();

    return (!(viewport.right < bounds.left || viewport.left > bounds.right || viewport.bottom < bounds.top || viewport.top > bounds.bottom));
};
$.fn.is_top_on_screen = function(){

    var win = $(window);

    var viewport = {
        top: win.scrollTop(),
        left: win.scrollLeft()
    };
    viewport.right = viewport.left + win.width();
    viewport.bottom = viewport.top + win.height();

    var bounds = this.offset();
    bounds.right = bounds.left + this.outerWidth();
    bounds.bottom = bounds.top + this.outerHeight();

    return (!(viewport.right < bounds.left || viewport.left > bounds.right || viewport.bottom < bounds.top || viewport.top > bounds.top));
};

/**
 * GENERAL
 */
$(function(){

	// MENU PEGAJOSO
	/*$(window).on("load resize scroll",function(e){
	    if (!$(".menu-principal").is_top_on_screen())
	    {
	    	$(".menu-principal").addClass("navbar-fixed-top");
	    	$(".website_forum").css("margin-bottom", ($(".menu-principal").height()+parseInt($(".menu-principal").css("margin-bottom"))*2)+"px");
	    }

	    if ($(".website_forum").is_on_screen())
	    {
	    	$(".menu-principal").removeClass("navbar-fixed-top");
	    	$(".website_forum").css("margin-bottom", "initial");
	    }
	});*/

	// Nuevo Menu
    //stick in the fixed 100% height behind the navbar but don't wrap it
	$('#slide-nav.navbar-inverse').after($('<div class="inverse" id="navbar-height-col"></div>'));
	$('#slide-nav.navbar-default').after($('<div id="navbar-height-col"></div>'));

	// Enter your ids or classes
	var toggler = '.navbar-toggle';
	var pagewrapper = '#page-content';
	var navigationwrapper = '.navbar-header';
	var menuwidth = '100%'; // the menu inside the slide menu itself
	var slidewidth = '80%';
	var menuneg = '-100%';
	var slideneg = '-80%';

 	$("#slide-nav").on("click", toggler, function(e){
 		var selected = $(this).hasClass('slide-active');

 		$('#slidemenu').stop().animate({
 			left: selected ? menuneg : '0px'
        });

        $('#navbar-height-col').stop().animate({
            left: selected ? slideneg : '0px'
        });

        $(pagewrapper).stop().animate({
            left: selected ? '0px' : slidewidth
        });

        $(navigationwrapper).stop().animate({
            left: selected ? '0px' : slidewidth
        });

        $(this).toggleClass('slide-active', !selected);
        $('#slidemenu').toggleClass('slide-active');
        //$('#page-content, .navbar, body, .navbar-header').toggleClass('slide-active');
    });

    /*var selected = '#slidemenu, #page-content, body, .navbar, .navbar-header';
    $(window).on("resize", function(){
        if ($(window).width() > 767 && $('.navbar-toggle').is(':hidden')){
            $(selected).removeClass('slide-active');
        }
    });*/


	// Borrar Contacto
	$(document).on('click', '.remove-contact', function(ev){
		var contact_id = $(this).data('id');
		remove_contact(contact_id);
	});
	$(document).on('submit', 'form#ncontact', function(ev){
		var phone = $('#nphone').val();
		var desc = $('#ndesc').val();

		$(this).attr("disabled", "disabled");
		add_contact(phone, desc);
		return false;
	});

	// Archivar Mensajes
    $('.archive_question').on('click', function (ev) {
        ev.preventDefault();
        var $link = $(ev.currentTarget);
        openerp.jsonRpc($link.data('href'), 'call', {}).then(function (data) {
            if (data) {
                $link.addClass("forum_favourite_question");
                $link.find('span').text(_t('Archivado'));
            } else {
                $link.removeClass("forum_favourite_question");
                $link.find('span').text(_t('Archivar'));
            }
        });
    });

  // Respuesta Correcta
  $('.accept_answer').on('click', function (ev) {
      ev.preventDefault();
      var $link = $(ev.currentTarget);
      openerp.jsonRpc($link.data('href'), 'call', {}).then(function (data) {
          if (data) {
              $link.addClass("oe_answer_true");
              $link.removeClass("oe_answer_false");
          } else {
              $link.removeClass("oe_answer_true");
              $link.addClass("oe_answer_false");
          }
      });
  });
});

/**
 * CONTACTOS
 */
function remove_contact(id)
{
	var ev = {'id': id};
	openerp.jsonRpc('/_remove_contact/', 'call', ev).then(function(data){
		if (data['success'])
			$('#contact-'+data['success']).remove();
	});
}
function add_contact(phone, desc)
{
	if (!phone)
		return;

	var ev = {'phone': phone, 'description': desc};
	openerp.jsonRpc('/_add_contact/', 'call', ev).then(function(data){
		$("#modalNewPhoneNumber button[type='submit']").removeAttr("disable");
		if (data['success'])
		{
			$('#nphone').val('');
			$('#ndesc').val('');

			var strElm = "<tr id='contact-"+data['success']+"'>";
			strElm += "<td>"+phone+"</td>";
			strElm += "<td>"+desc+"</td>";
			strElm += "<td class='text-right'><a class='remove-contact btn btn-xs' data-id='"+data['success']+"' href='#' title='Borrar Contacto'><i class='fa fa-remove'></i></a></td>";
			strElm += "</tr>";
			$('#table-phones').append(strElm);
			$("#modalNewPhoneNumber").modal('hide');
		}
	});
}

/**
 * INDICADOR DE ALERTAS SIN LEER
 */
openerp.website.if_dom_contains('#unread_alerts_badge', function(){
	// Mostrar alertas no leidas
	refresh_unread_alerts_count();
	setInterval("refresh_unread_alerts_count()", 4500);
});

/** CARGAR CKEDITOR **/
openerp.website.if_dom_contains('#content', function(){
	CKEDITOR.replace("content");
	if ($('textarea.load_editor_sevigal').length) {
	    var editor = CKEDITOR.instances['content'];
	    if (typeof editor !== 'undefined')
	    	editor.on('instanceReady', CKEDITORLoadComplete);
	}

    function CKEDITORLoadComplete(){
        "use strict";
        $('.cke_button__link').attr('onclick','website_forum_IsKarmaValid(33,30)');
        $('.cke_button__unlink').attr('onclick','website_forum_IsKarmaValid(37,30)');
        $('.cke_button__image').attr('onclick','website_forum_IsKarmaValid(41,30)');
        $('#box-cke').removeClass('block-sevigal-simple bg-default');
    }
});

/**
 * SISTEMA DE AVISOS DE ALERTAS NO LEIDAS
 */
function refresh_unread_alerts_count()
{
	openerp.jsonRpc('/_get_unread_alerts_count', 'call', {}).then(function(data){
		if (!data['error'])
		{
			if (data['num'] == 0)
			{
				$('#unread_alerts_badge').css('display','none');
				$('#bell-icon').removeClass('bell-anim');
			}
			else
			{
				var num = data['num'];
				var last_id = data['last_id'];

				$('#unread_alerts_badge').text(num);
				$('#unread_alerts_badge').css('display','inline');
				$('#bell-icon').addClass('bell-anim');

				if (last_id != Cookies.get('last_unread_alert_id'))
				{
					Cookies.set('last_unread_alert_id', last_id);
					bootbox.dialog({
						message: "<p class='text-center' style='color:#800000;'>Tiene <strong>"+num+"</strong> alertas sin leer</p>",
						title: "Alertas sin leer",
						buttons: {
							success: {
								label: "Ver Alertas",
								className: "btn-primary",
								callback: function() {
									window.location.href = "/alertas";
								}
							},
							cancel: {
								label: "Entendido",
								className: "btn-default",
								callback: function() { }
							}
						}
					});
				}
			}
		}
	});
}

/**
 * TRANSFORMA UN EVENT A UN OBJETO JSON PARA ENVIAR
 */
function get_event_data(event)
{
    var data = {
    	id: event.id,
      allday: event.allDay,
      title: event.title,
      description: event.description,
    };

    //Bug when we move an all_day event from week or day view, we don't have a dateend or duration...
    if (event.end == null || _.isUndefined(event.end))
    {
    	date_end = event.start.clone();
    	date_end.add(2, 'hours');
    }
    else
    	date_end = event.end;

    if (event.allDay) {
      data['start'] = event.start.clone().local().format("YYYY-MM-DD");
      data['stop'] = date_end.clone().local().format("YYYY-MM-DD");
    } else {
      // Strange conversion to truncate UTC... need exists a better way to do this...
      data['start'] = moment(event.start.format("YYYY-MM-DD HH:mm:ss"), "YYYY-MM-DD HH:mm:ss").utc().format("YYYY-MM-DD HH:mm:ss");
      data['stop'] = moment(date_end.format("YYYY-MM-DD HH:mm:ss"), "YYYY-MM-DD HH:mm:ss").utc().format("YYYY-MM-DD HH:mm:ss");
    }

    return data;
}
