# -*- coding: utf-8 -*-
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
#from datetime import datetime, timedelta

'''
Modelo que sobreescribe product.product (Variantes)
'''
class product_product(models.Model):
    _name = 'product.product'
    _inherit = 'product.product'
    
    @api.model
    def default_get(self, fields):
        #pydevd.settrace("192.168.3.1")
        data = super(product_product, self).default_get(fields)
        if 'view_llamada_realizada' in self.env.context:            
            data['tipo_producto_servicio'] = ('Llamada Realizada','Llamada Realizada')
        elif 'view_fax2mail' in self.env.context:
            data['tipo_producto_servicio'] = ('Fax2Mail','Fax2Mail')
        elif 'view_servicio_exclusivo' in self.env.context:
            data['tipo_producto_servicio'] = ('Servicio Exclusivo','Servicio Exclusivo')
            
        return data  
    
    
    #Fields
    tipo_producto_pack = fields.Selection([('Llamada','Llamada'),
                                           ('SMS','SMS'),
                                           ('Email','Email'),
                                           ('Apunte Agenda','Apunte Agenda'),
                                           ('Fax2Mail','Fax2Mail')], 'Tipo de producto en Pack')
    tipo_producto_servicio = fields.Selection([('Llamada Transferida','Llamada Transferida'),
                                               ('Llamada Realizada','Llamada Realizada'),
                                               ('Fax2Mail','Fax2Mail'),
                                               ('Servicio Exclusivo','Servicio Exclusivo'),], 
                                               'Tipo de producto en Servicio')
    #Redefine el field del padre, preseleccionando la opcion
    pack_price_type = fields.Selection([('Detailed - Fixed Price','Detailed - Fixed Price'),],
                                       string='Tipo Precio Pack', default='Detailed - Fixed Price')

    contrato = fields.Boolean('En Contrato?')
    
product_product()

'''
Modelo que registra los elementos disponibles en un pack de cliente y el consumo de los productos
de ese pack
'''
class product_pack_contrato(models.Model):
    _name = 'product.pack.contrato'
    _rec_name = 'name_quantity'
    
    @api.one
    def get_name_quantity(self):
        #pydevd.settrace("10.0.3.1")
        if self.product_id:
            self.name_quantity = self.product_id.name + ': ' + unicode(self.consumido) +\
                                 ' de ' + unicode(self.disponible)
        else:
            self.name_quantity = ''
    
    #Fields

    name_quantity = fields.Char(compute=get_name_quantity, string='Consumo del Producto')
    product_id = fields.Many2one('product.product', 'Producto')
    disponible = fields.Float('Cantidad Disponible')
    consumido = fields.Float('Cantidad Consumida')
    
product_pack_contrato()