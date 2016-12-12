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
from openerp.osv import osv
from openerp import models, fields, api

'''
Modelo que extiende res.partner para agregar campos al modelo para gestion de llamadas
'''
class res_partner(models.Model):
    _name = 'res.partner'
    _inherit = 'res.partner'
    
    @api.multi
    def get_cuentas_cliente(self):
        for res in self:
            if res.bank_ids:
                res.cuenta_ids = res.bank_ids
                
    @api.multi
    def get_contrato_cliente(self):
        for res in self:
            contrato = self.env['account.analytic.account'].search([('partner_id','=',res.id)])
            if contrato:
                contrato = contrato[0]
                res.contrato_id = contrato.id
                
    '''
    Metodo que crea usuario al activar la opcion desde boton en form cliente
    '''
    @api.multi 
    def crear_usuario(self):
        #pydevd.settrace("192.168.3.1")
        if self.name and self.email:
            #Crea el usuario con el mismo nombre, login el email y karma para publicar en foro
            user = self.env['res.users'].create({'name':self.name,
                                          'login':self.email,
                                          'partner_id':self.id,
                                          'karma':100,
                                          })
            #Tomamos los grupos del usuario a partir de sus ids externos
            #Grupo de portal de Odoo
            extid_portal_group = self.env['ir.model.data'].search(['&',
                                                                 ('module','=', 'base'),
                                                                 ('name','=','group_portal')])
            if extid_portal_group:
                portal_group = self.env['res.groups'].search([('id','=',extid_portal_group.res_id)])            
            
            
            #Grupo de clientes (partners) de sevigal
            extid_partner_group = self.env['ir.model.data'].search(['&',
                                                                 ('module','=', 'aloxa_sevigal_secretaria'),
                                                                 ('name','=','sevigal_partner_group')])
            if extid_partner_group:
                partner_group = self.env['res.groups'].search([('id','=',extid_partner_group.res_id)])
            
      
            #Grupo de empleados
            extid_base_user_group = self.env['ir.model.data'].search(['&',
                                                                 ('module','=', 'base'),
                                                                 ('name','=','group_user')])
            if extid_base_user_group:
                base_user_group = self.env['res.groups'].search([('id','=',extid_base_user_group.res_id)])                                
            
            #Metemos al usuario como miembro del grupo Portal y Sevigal/Cliente
            if partner_group:
                partner_group.users += user
                portal_group.users += user           
            
            #Quitamos al usuario del grupo de HR (Empleado) para que no vea el menu de Odoo
            if base_user_group:
                base_user_group.users -= user
                
            
            self.usuario_portal = True
        else:
            raise osv.except_osv(('Error en la creación de usuario'),
                                 ('Indique la dirección de email para login en área privada...'))
    
    #Fields
    inicio_vacas = fields.Date('Inicio Vacaciones')
    fin_vacas = fields.Date('Fin Vacaciones')
    tratamiento = fields.Text('Tratamiento Contestación')
    ver_cuenta = fields.Char('Dar Cuenta a')
    cuenta_ids = fields.One2many('res.partner.bank', compute=get_cuentas_cliente)
    protocolo_ids = fields.One2many('sevigal.protocolo', 'partner_id', string='Protocolos')
    llamada_realizada_ids = fields.One2many('sevigal.llamada.realizada', 'partner_id', 'Llamadas Realizadas')
    fax2mail_ids = fields.One2many('sevigal.fax2mail', 'partner_id', 'Llamadas Realizadas')
    servicio_exclusivo_ids = fields.One2many('sevigal.servicio.exclusivo', 'partner_id', 'Servicios Exclusivos')
    contrato_id = fields.Many2one('account.analytic.account', 'Contrato', compute=get_contrato_cliente)
    usuario_portal = fields.Boolean('Usuario Portal', default=False)
    telefono_ids = fields.One2many('sevigal.telefono', 'partner_id', 'Teléfonos Adicionales')
    
res_partner()

class telefono_adicional_cliente(models.Model):
    _name='sevigal.telefono'
    
    #Fields
    descripcion = fields.Char('Descripción')
    numero = fields.Char('Número', size=14)
    partner_id = fields.Many2one('res.partner', 'Cliente')
    
telefono_adicional_cliente()

class protocolos_cliente(models.Model):
    _name='sevigal.protocolo'
     
    #Fields
    #name = fields.Char('Nombre', size=120)
    protocolo= fields.Selection([('Transferir_si','Transferir'),
                                 ('Email_si','Email'),
                                 ('Direccion_si','Direccion'),
                                 ('Apunte_si', 'Apunte')],string='Protocolo')
    condicion = fields.Char('Condicion', size=120)
    destino = fields.Char('Destino', size=120)   
    partner_id = fields.Many2one('res.partner')
 
protocolos_cliente()
