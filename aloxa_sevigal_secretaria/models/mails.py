# -*- coding: utf-8 -*-
#################################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 Solucións Aloxa S.L. <info@aloxa.eu>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#################################################################################
#===============================================================================
# # REMOTE DEBUG
#import pydevd
# 
# # ...
# 
# # breakpoint
#pydevd.settrace("10.0.3.1")
#===============================================================================
import pytz
import datetime
from openerp import models, fields, api

class mail_mail(models.Model):
    _name='mail.mail'
    _inherit='mail.mail'
    
    '''
    Metodo utilizado para cargar valores por defecto cuando este definido llamada_id en el contexto
    Usado para cargar los valores predefinidos en el formulario de envio de email desde la llamada
    '''
    @api.model
    def default_get(self, fields):
    #def default_get(self, cr, uid, fields, context=None):
        #pydevd.settrace("192.168.3.1")
        res = super(mail_mail, self).default_get(fields)
        #res = super(mail_mail, self).default_get(cr, uid, fields, context)
        subject = ''
        email_to = ''
        email_from = ''
        body_html = ''        
        if 'llamada_id' in self.env.context:
            llamada = self.env['crm.phonecall'].search([('id', '=', self.env.context['llamada_id'])])
            if llamada:
                subject = llamada.name or 'Llamada Sevigal'
                email_to = llamada.partner_id.email if llamada.partner_id else ''
                email_from = self.env.user.company_id.email if self.env.user.company_id.email else 'info@sevigal.com'                
                
                #Fecha y hora normalizadas 
                timezone = pytz.timezone(self._context.get('tz') or 'UTC')                               
                fecha_hora = pytz.UTC.localize(datetime.datetime.strptime(llamada.date,'%Y-%m-%d %H:%M:%S')).astimezone(timezone)
                fecha_hora = fecha_hora.strftime('%d %b, %Y %H:%M:%S')
                
                body_html = '<h3>' + llamada.name + '</h3><br>'
                body_html += '<b>Fecha/Hora: </b>' + str(fecha_hora) + '<br>' if fecha_hora else ''                
                body_html += '<b>Emisor: </b>' + llamada.telefono_emisor + '<br>' if llamada.telefono_emisor else ''
                body_html += '<b>Mensaje: </b>' + llamada.description if llamada.description else ''
                res.update({'subject':subject,
                            'email_to':email_to,
                            'email_from':email_from,
                            'body_html':body_html
                            })
        elif 'servicio_id' in self.env.context and 'modelo' in self.env.context:
            modelo = self.env.context['modelo']
            servicio = self.env[modelo].search([('id', '=', self.env.context['servicio_id'])])
            if servicio:
                subject = servicio.name or 'Servicio Sevigal'
                email_to = servicio.partner_id.email if servicio.partner_id else ''
                email_from = self.env.user.company_id.email if self.env.user.company_id.email else 'info@sevigal.com'
                
                #Fecha y hora normalizadas
                timezone = pytz.timezone(self._context.get('tz') or 'UTC')                          
                fecha_hora = pytz.UTC.localize(datetime.datetime.strptime(servicio.create_date,'%Y-%m-%d %H:%M:%S')).astimezone(timezone)
                fecha_hora = fecha_hora.strftime('%d %b, %Y %H:%M:%S')
                
                body_html = '<h3>' + subject + '</h3><br>'
                body_html += '<b>Fecha/Hora: </b>' + str(fecha_hora) + '<br>' if fecha_hora else None                
                body_html += '<b>Mensaje: </b>' + self.env.context['descripcion'] if self.env.context['descripcion'] else ''
                res.update({'subject':subject,
                            'email_to':email_to,
                            'email_from':email_from,
                            'body_html':body_html
                            })            
        
        return res    
            
    '''
    Metodo asociado al boton enviar del formulario de redaccion del email.
    Si se usa directamente sobreescritura de send da un error al crear usuarios y enviar email de confirmacion
    Por ese motivo se crea el metodo enviar y IMPORTANTE, se sustituye el boton enviar del formulario de 
    redaccion de email por uno similar pero con name=enviar para que invoque este metodo y no send
    '''
    @api.multi    
    def enviar(self):
        #pydevd.settrace("10.0.3.1")
        success = super(mail_mail, self).send()
        if 'llamada_id' in self.env.context:
            llamada = self.env['crm.phonecall'].search([('id', '=', self.env.context['llamada_id'])])
            if llamada and not llamada.email_enviado:
                llamada.registrar_consumo_producto_pack('Email')
                llamada.email_enviado = True           
        return success
            
mail_mail()