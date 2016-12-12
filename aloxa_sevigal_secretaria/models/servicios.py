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

class servicio(models.Model):
    _name = 'sevigal.servicio'
    
    @api.multi
    def registrar_consumo_servicio(self):       
        #pydevd.settrace("192.168.3.1")
        for res in self:
            '''
            Buscar el contrato y añadir la linea como linea de facturacion periodica
            '''
            contrato = self._obtener_contrato_partner_servicio()
            
            if contrato and 'product_id' in self.env.context and \
               'cantidad_servicio' in self.env.context:
                product_id = self.env.context['product_id']
                cantidad = self.env.context['cantidad_servicio']
                product = self.env['product.product'].search([('id','=',product_id)])
                linea_invoice = contrato.obtener_line_factu_recurr_no_pack(product)
                linea_invoice[0].quantity += cantidad
                
                res.linea_fact_recurr_id = linea_invoice[0].id
                res.registrado = True              

    
    '''
    Envia un mensaje de registro del servicio el partner
    '''    
    def notificar(self, texto, descripcion):
        #pydevd.settrace("192.168.3.1")
        opciones = self.env['sevigal.opciones'].search([('nombre','=','Default')])
        if opciones:
            foro = opciones.foro_notificaciones_id
        if foro and self.partner_id:            
            menvals = {'name':texto,
                       'forum_id':foro.id,
                       'tipo':'Notificacion',
                       'partner_id':self.partner_id.id,
                       'content':'<h3>' + texto + '</h3> <p>' + descripcion + '</p>',
                       'is_correct':True}
            if self.env.user.id == 1 or self.env.user.karma > 0:            
                mensaje = self.env['forum.post'].create(menvals)
            else:
                raise osv.except_osv(('Error en el envío de la Notificación'),
                                     ('No tiene suficiente karma en el foro para enviar mensaje...'))
        else:
                raise osv.except_osv(('Error en el envío de la Notificación'),
                                     ('No se ha podido localizar el foro asociado al mensaje de notificación...'))
            
    '''
    Devuelve el contrato de facturacion periodica del cliente del servicio
    Un cliente deberia tener un contrato y este a su vez una linea de facturacion recurrente para el pack
    del cliente
    '''
    def _obtener_contrato_partner_servicio(self):
        partner = self.partner_id
        if partner:
            contrato = self.env['account.analytic.account'].search([('partner_id','=',partner.id)])
            if contrato:
                contrato = contrato[0]
                return contrato               

        return False          
 
    #Fields
    name = fields.Char('Nombre')
    descripcion = fields.Text('Descripción')
    product_id = fields.Many2one('product.product', 'Producto', required=True)
    llamada_id = fields.Many2one('crm.phonecall', 'Llamada')
    registrado = fields.Boolean('Registrado')
    mail_enviado = fields.Boolean('Email Enviado')
    partner_id = fields.Many2one('res.partner', 'Cliente')
    linea_fact_recurr_id = fields.Many2one('account.analytic.invoice.line',
                                           'Registrado', readonly=True)
    
servicio()

class llamada_realizada(models.Model):
    _name = 'sevigal.llamada.realizada'
    _inherit = 'sevigal.servicio'
    
    @api.multi
    def get_name(self):
        for res in self:
            res.name = 'Llamada Realizada a: ' + res.telefono if res.telefono else ''
    
    @api.multi
    def registrar_consumo_servicio(self):
        super(llamada_realizada, self).registrar_consumo_servicio()
        self.notificar()
    
    '''
    Invoca al padre para notificacion de la llamada realizada, previo establecimiento
    del texto y la descripcion del mensaje
    '''
    def notificar(self, texto = '', descripcion = ''):        
        texto = 'Llamada Realizada a ' + self.telefono if self.telefono else ''
        descripcion = self.descripcion if self.descripcion else ''
        super(llamada_realizada, self).notificar(texto, descripcion)
    
    '''
    Envio de email para notificar la llamada
    '''
    @api.multi
    def enviar_email(self, modelo=''):
        for res in self:
            res.mail_enviado = True            
            return  {
                'type': 'ir.actions.act_window',
                'name': 'Enviar Email Servicio',            
                #'domain': ['&', ('res_model','=','project.task'), ('res_id','=',context['task_id'])],            
                'res_model': 'mail.mail',
                'context': {'servicio_id': res.id, 'modelo':'sevigal.llamada.realizada', 'descripcion': res.descripcion},                            
                'view_type': 'form',
                'view_mode': 'form',            
                'target': 'new',               
                'nodestroy': True,
            }
                
    #Fields
    name = fields.Char(compute=get_name, string='Nombre')
    #duracion = fields.Integer('Duración')
    duracion = fields.Float('Duración')
    #product_id = fields.Many2one('product.product', 'Producto')
    #descripcion = fields.Text('Descripción')
    telefono = fields.Char('Teléfono', size=20)     
    
llamada_realizada()

class llamada_transferida(models.Model):
    _name = 'sevigal.llamada.transferida'
    _inherit = 'sevigal.servicio'
    
    #Fields
    #duracion = fields.Integer('Duración')
    duracion = fields.Float('Duración')
    #product_id = fields.Many2one('product.product', 'Producto')
    #descripcion = fields.Text('Descripción')
    telefono = fields.Char('Teléfono', )    
    
llamada_transferida()

class fax2mail(models.Model):
    _name = 'sevigal.fax2mail'
    _inherit = 'sevigal.servicio'
    
    #Fields
    email = fields.Char('Email')
    #product_id = fields.Many2one('product.product', 'Producto')
    #descripcion = fields.Text('Descripción')
    telefono = fields.Char('Teléfono', size=20)
    
    '''
    Para los Fax2Mails se da un comportamiento hibrido entre registro de llamada y computo de servicio.
    En este metodo se localiza linea de pack para Fax2Mail y se imputa el consumo, creando linea adicional
    cuando se agote
    '''
    @api.multi
    def registrar_consumo_servicio(self):
        #pydevd.settrace("192.168.3.1")
        for res in self:
            '''
            Buscar el contrato y añadir la linea como linea de facturacion periodica
            '''
            contrato = self._obtener_contrato_partner_servicio()
            
            if contrato:
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
                                    if pcline.product_id.tipo_producto_pack == 'Fax2Mail':
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
                                                
                                        res.registrado = True
                                        return
                '''
                Cuando no tengamos el Fax2Mail en el pack lo procesamos como una linea normal
                de contrato
                '''               
                if contrato and 'product_id' in self.env.context:
                    product_id = self.env.context['product_id']                    
                    product = self.env['product.product'].search([('id','=',product_id)])
                    linea_invoice = contrato.obtener_line_factu_recurr_no_pack(product)
                    linea_invoice[0].quantity += 1
                    
                    res.linea_fact_recurr_id = linea_invoice[0].id                                                   
                             
                res.registrado = True       
    
fax2mail()

class servicio_exclusivo(models.Model):
    _name = 'sevigal.servicio.exclusivo'
    _inherit = 'sevigal.servicio'
    
    #Fields
    unidades = fields.Integer('Unidades')
    

servicio_exclusivo()

#------------------------------------------- class digitalizacion(models.Model):
    #------------------------------------------ _name = 'sevigal.digitalizacion'
    #--------------------------------------------- _inherit = 'sevigal.servicio'
#------------------------------------------------------------------------------ 
    #------------------------------------------------------------------- #Fields
#------------------------------------------------------------------------------ 
#-------------------------------------------------------------- digitalizacion()
#------------------------------------------------------------------------------ 
#-------------------------------------------------- class reserva(models.Model):
    #------------------------------------------------- _name = 'sevigal.reserva'
    #--------------------------------------------- _inherit = 'sevigal.servicio'
#------------------------------------------------------------------------------ 
    #------------------------------------------------------------------- #Fields
#------------------------------------------------------------------------------ 
#--------------------------------------------------------------------- reserva()

