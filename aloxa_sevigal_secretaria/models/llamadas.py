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
from openerp import models, fields, api
from openerp.osv import osv

class calendar_event(models.Model):
    _name = 'calendar.event'
    _inherit = 'calendar.event'
    
    '''
    Metodo de workflow de registro de apunte en agenda
    '''
    def registrar_apunte(self):
        if self.phonecall_id:
            self.phonecall_id.registrar_apunte_agenda()
        
calendar_event()

class llamada(models.Model):
    _name = 'crm.phonecall'
    _inherit = 'crm.phonecall'
    
    ESTADOS = [('Respondida', 'Respondida'), ('Registrada', 'Registrada'), ('Cancelada', 'Cancelada')]
    
    ESTADOS_REPLEGADOS = ['Cancelada']
    
    @api.model
    def state_groups(self, present_ids, domain, **kwargs):
        replegado = {key: (key in self.ESTADOS_REPLEGADOS) for key, _ in self.ESTADOS}
        return self.ESTADOS[:], replegado

    _group_by_full = {
        'state': state_groups
    }
    
    def _read_group_fill_results(self, cr, uid, domain, groupby,
                                  remaining_groupbys, aggregated_fields,
                                  count_field, read_group_result,
                                  read_group_order=None, context=None):
         """
         The method seems to support grouping using m2o fields only,
         while we want to group by a simple status field.
         Hence the code below - it replaces simple status values
         with (value, name) tuples.
         """
         if groupby == 'state':
             ESTADOS_DICT = dict(self.ESTADOS)
             for result in read_group_result:
                 state = result['state']
                 result['state'] = (state, ESTADOS_DICT.get(state))
    
         return super(llamada, self)._read_group_fill_results(
             cr, uid, domain, groupby, remaining_groupbys, aggregated_fields,
             count_field, read_group_result, read_group_order, context
         )
    '''
    Metodo invocado en el envio de SMS, asociado al pack
    '''
    @api.multi 
    def enviar_sms(self):
        #pydevd.settrace("10.0.3.1")
        if not self.sms_enviado:
            self.registrar_consumo_producto_pack('SMS')
            self.sms_enviado = True
    '''
    Metodo invocado en el envio de email, asociado al pack
    '''
    @api.multi
    def enviar_email(self):
        return  {
            'type': 'ir.actions.act_window',
            'name': 'Enviar Email',            
            #'domain': ['&', ('res_model','=','project.task'), ('res_id','=',context['task_id'])],            
            'res_model': 'mail.mail',
            'context': {'llamada_id': self.id},                            
            'view_type': 'form',
            'view_mode': 'form',            
            'target': 'new',               
            'nodestroy': True,
        }
        
        #=======================================================================
        # if not self.email_enviado:
        #     self.registrar_consumo_producto_pack('Email')
        #     self.email_enviado = True
        #     '''
        #     Envio de email automatico de la llamada al cliente
        #     '''
        #     if self.partner_id and self.partner_id.email:
        #         mail_vals = {'subject':self.name + ', ' + unicode(self.date),
        #                      'email_from':'info@sevigal.com',
        #                      'email_to':self.partner_id.email,
        #                      'body_html':'Llamada recibida de ' + self.telefono_emisor if self.telefono_emisor else '' +\
        #                                  ', ' + self.description if self.description else '',
        #                      }
        #         mail = self.env['mail.mail'].create(mail_vals)
        #         mail.send()
        #=======================================================================

    '''
    Metodo invocado al crear una reunion dese una llamada (apunte de agenda)
    '''    
    def registrar_apunte_agenda(self):
        #pydevd.settrace("10.0.3.1")
        '''
        Esta transicion hace que se registre la llamada a efectos de facturacion y control
        de pack de servicios de Sevigal.
        '''        
        self.registrar_consumo_producto_pack('Apunte Agenda')
    
    '''
    Metodo invocado en a transicion de Registro de llamada
    '''    
    def registrar_llamada(self):
        #pydevd.settrace("10.0.3.1")
        '''
        Esta transicion hace que se registre la llamada a efectos de facturacion y control
        de pack de servicios de Sevigal.
        '''        
        self.registrar_consumo_producto_pack('Llamada')
        self.registrar_notificacion_llamada()
        '''
        Registrar las llamadas transferidas asociadas a la llamada
        '''
        self.registrar_llamadas_transferidas()
        '''
        Registrar los fax2mails asociados a la llamada
        '''
        self.registrar_fax2mails()        

                                        
    def registrar_consumo_producto_pack(self, tipo_producto):
        '''
        Se descontara del numero de elementos del producto del pack el producto consumido y se procesara el desbordamiento
        del producto al alcanzar el numero maximo de unidades de producto del pack
        Tambien se programara una alerta cuando este proximo el agotamiento de las unidades de producto del pack
        1.- Localizar el contrato asociado al cliente
        2.- Por cada linea de producto (product.product) del Contrato localizar el Pack asociado
        3.- Descontar la unidad de producto del pack
        4.- Controlar el desbordamiento
        5.- Registrar Oportunidades de ampliacion de pack en CRM
        '''
        contrato = self._obtener_contrato_partner_llamada()
        if contrato:
            #Lineas de facturacion recurrente del contrato
            inv_lines = contrato.recurring_invoice_line_ids
            if inv_lines:
                for line in inv_lines:
                    '''
                    Tomo de las lineas aquella que este asociada a un producto
                    marcado como pack
                    '''
                    if line.product_id and line.product_id.pack:
                        pack_lines_contrato = line.pack_line_consumido_ids
                        #pack_lines = line.product_id.pack_line_ids
                        ctdad_producto_pack = 0
                        ctdad_producto_consumido = 0                  
                        #Obtencion del numero de elementos del pack consumidos y disponibles
                        for pcline in pack_lines_contrato:
                            if pcline.product_id and pcline.product_id.tipo_producto_pack:
                                if pcline.product_id.tipo_producto_pack == tipo_producto:
                                    ctdad_producto_consumido = pcline.consumido
                                    ctdad_producto_pack = pcline.disponible                                    
                                    if ctdad_producto_consumido < ctdad_producto_pack:
                                        pcline.consumido += 1
                                        '''
                                        Control del numero que el numero de producto de pack consumido alcance
                                        el numero de unidades de aviso. En caso afirmativo se creara una
                                        oportunidad de ampliacion de pack para ese cliente
                                        '''
                                        opciones = self.env['sevigal.opciones'].search([('nombre','=','Default')])
                                        if opciones:
                                            uni_aviso = opciones.unidades_aviso_expiracion_pack
                                            if ctdad_producto_pack - ctdad_producto_consumido == uni_aviso:
                                                contrato._crear_oportunidad_agotamiento_pack(self.partner_id, pcline.product_id)
                                                 
                                    else:
                                        linea = contrato.obtener_line_factu_recurr_no_pack(pcline.product_id)
                                        if linea:
                                            linea[0].quantity += 1
    
    def registrar_llamadas_transferidas(self):
        if self.llamada_transferida_ids:
            contrato = self._obtener_contrato_partner_llamada()
            '''
            Para cada llamada transferida registramos en la linea de facturacion asociada al tipo de
            llamada transferida la duracion en minutos, que se agregara al total de minutos consumidos
            de esa linea en el campo cantidad (quantity) 
            '''
            for transferida in self.llamada_transferida_ids:                
                if contrato:
                    linea = contrato.obtener_line_factu_recurr_no_pack(transferida.product_id)
                    if linea:
                        linea[0].quantity += transferida.duracion
                        
    def registrar_fax2mails(self):
        if self.fax2mail_ids:
            contrato = self._obtener_contrato_partner_llamada()
            '''
            Para cada fax2mail registramos en la linea de facturacion asociada al tipo de
            fax2mail 
            '''
            for fax2mail in self.fax2mail_ids:                
                if contrato:
                    self.registrar_consumo_producto_pack('Fax2Mail')                        
                                            
    def registrar_notificacion_llamada(self):
        #pydevd.settrace("192.168.3.1")
        opciones = self.env['sevigal.opciones'].search([('nombre','=','Default')])
        if opciones:
            foro = opciones.foro_notificaciones_id
        if foro and self.partner_id:
            texto = '<h3>Llamada de ' + self.telefono_emisor if self.telefono_emisor else ''
            texto += '</h3>' + self.description if self.description else ''
            menvals = {'name':self.name or '',
                       'forum_id':foro.id,
                       'tipo':'Notificacion',
                       'partner_id':self.partner_id.id,
                       'content':texto,
                       'is_correct':True}
            if self.env.user.id == 1 or self.env.user.karma > 0:            
                mensaje = self.env['forum.post'].create(menvals)
            else:
                raise osv.except_osv(('Error en el envío de la Notificación'),
                                     ('No tiene suficiente karma en el foro para enviar mensaje...'))
        else:
                raise osv.except_osv(('Error en el envío de la Notificación'),
                                     ('No se ha podido localizar el foro asociado al mensaje de notificación...'))            
                #===============================================================
                # return {'warning': {
                #         'title':'Error en el envío de la Notificación',
                #         'message': 'No tiene suficiente karma en el foro para enviar mensaje...',
                #         }}
                #===============================================================
                           
        
    
    '''
    Devuelve el contrato de facturacion periodica del cliente de la llamada
    Un cliente deberia tener un contrato y este a su vez una linea de facturacion recurrente para el pack
    del cliente
    '''
    def _obtener_contrato_partner_llamada(self):
        partner = self.partner_id
        if partner:
            #Para los partners que sean contactos de una empresa tomamos el contrato de la empresa
            if partner.parent_id:
                partner = partner.parent_id
            contrato = self.env['account.analytic.account'].search([('partner_id','=',partner.id)])
            if contrato:
                contrato = contrato[0]
                return contrato               

        return False
    
#     '''
#     Crea la oportunidad cuando se alcanza el consumo de advertencia de pack de un cliente
#     '''
#     def _crear_oportunidad_agotamiento_pack(self, partner, producto):
#         '''
#         TODO: Ver la posibilidad de comprobar que ya se ha creado una oportunidad para
#         ese pack para el agotamiento de otro producto
#         '''
#         #Creacion de la oportunidad para el partner
#         #pydevd.settrace("10.0.3.1")
#         description = 'El pack de ' + partner.name + ' a punto de agotar'
#         description += ' ' + producto.tipo_producto_pack + 's' if producto.tipo_producto_pack else ''
#         self.env['crm.lead'].create({'name':description,
#                                      'type':'opportunity',
#                                      'partner_id':partner.id,
#                                      'phone':partner.phone if partner.phone else '',
#                                      'email':partner.email if partner.email else '',
#                                      })
            
    #Fields
    state = fields.Selection(ESTADOS, string='Estado', default='Respondida')
    sms_enviado = fields.Boolean('SMS enviado', default=False)
    email_enviado = fields.Boolean('Email enviado', default=False)
    telefono_emisor = fields.Char('Teléfono Emisor')
    llamada_transferida_ids = fields.One2many('sevigal.llamada.transferida','llamada_id','Llamadas Transferidas')
    fax2mail_ids = fields.One2many('sevigal.fax2mail','llamada_id','Fax2Mails')
    
llamada()
