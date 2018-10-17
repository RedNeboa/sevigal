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
import datetime
from openerp import models, fields, api

class avisos(models.Model):
    _name = 'sevigal.aviso'
    _inherit = ['ir.needaction_mixin']
    _order = 'create_date desc'

    #Fields
    name = fields.Char('Nombre')
    tipo = fields.Selection([
        ('Evento', 'Evento'),
        ('Mensaje', 'Mensaje'),
    ], readonly=True)
    event_id = fields.Many2one('calendar.event', "Calendario", readonly=True)
    mensaje_id = fields.Many2one('forum.post', "Mensaje Foro", readonly=True)
    event_write_date = fields.Datetime()
    leido = fields.Boolean('Leído')
    create_date = fields.Datetime('Creado')

    def obtener_eventos_mensajes(self):
        '''
        Recupera
        1.- Los mensajes de la web de Reuniones, Viajes y Mensajes que no hayan
            sido validados
        2.- Los eventos de calendario creados o modificados en la web por el
            cliente que tengan fecha de inicio posterior a la actual
        '''

        mensajes = self.env['forum.post'].search([('is_correct', '=', False)])
        for mensaje in mensajes:
            '''
            Si no hay ningun aviso asociado a ese mensaje se crea
            '''
            if self.search_count([('mensaje_id', '=', mensaje.id)]) == 0:
                self.create({
                    'name': mensaje.name,
                    'tipo': 'Mensaje',
                    'mensaje_id': mensaje.id,
                    'leido': False,
                })

        eventos = self.env['calendar.event'].search([
            '|', ('start_datetime', '>=', str(datetime.datetime.today())),
            ('start_date', '>=', datetime.datetime.today())])

        for evento in eventos:
            '''
            Si no hay ningun aviso asociado a ese evento se crea
            Sino, si hay un aviso ya leido pero se ha actualizado el
            event_write_date, lo cual indica que se actualizo el evento asociado,
            se vuelve a poner leido=False para que lo vuelta a mostrar
            '''
            if not isinstance(evento.id, str) and not self.search([('event_id', '=', evento.id)]):
                self.create({
                    'name': evento.name,
                    'tipo': 'Evento',
                    'event_id': evento.id,
                    'leido': False,
                    'event_write_date': evento.write_date,
                })
            else:
                aviso = self.search([
                    '&', ('event_id', '=', evento.id),
                    ('event_write_date', '!=', evento.write_date),
                ])
                if aviso:
                    aviso.write({'leido':False, 'event_write_date':evento.write_date})


    @api.model
    def _needaction_domain_get(self):
        self.obtener_eventos_mensajes()
        return [('leido', '=', False)]
