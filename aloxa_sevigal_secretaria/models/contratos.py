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
import time
#from datetime import time

'''
Modelo que sobreescribe product.pack.line y establece el rec_name para
que aparezca el producto y la cantidad asociada
'''
class pack_line(models.Model):
    _name = 'product.pack.line'
    _inherit = 'product.pack.line'
    _rec_name = 'name_quantity'
    
    @api.one
    def get_name_quantity(self):
        #pydevd.settrace("10.0.3.1")
        if self.product_id:
            self.name_quantity = self.product_id.name + ': ' + unicode(self.quantity)
        else:
            self.name_quantity = ''
    
    #Fields
    name_quantity = fields.Char(compute=get_name_quantity)
pack_line()

'''
Modelo que sobreescribe account.analytic.invoice.line para agregar el campo
pack_line_consumido_ids
Este campo establece las unidades de productos incluidos en el pack que el cliente
ha consumido
'''
class contrato_invoice_line(models.Model):
    _name = 'account.analytic.invoice.line'
    _inherit = 'account.analytic.invoice.line'
    
    '''
    Al crear un registro se inicializa pack_line_consumido_ids
    '''
    @api.model
    def create(self, values):        
        line = super(contrato_invoice_line, self).create(values)
        '''
        Publicamos datos del field pack_line_consumido_ids a partir de los datos el pack
        asociado al producto de la invoice_line creada
        '''
        if line.product_id:
            '''
            Tomo del product.product asociado las lineas del pack
            Por cada linea del pack creo una nueva asociada al mismo
            product.product (el del pack) con cantidad a 0
            Estos elementos se agregaran al campo pack_line_consumido_ids
            y contabilizaran las unidades de producto de pack consumido
            '''
            pack_line_model = self.env['product.pack.contrato']
            pack_lines = line.product_id.pack_line_ids
            pack_lines_consumido = list()
            #pydevd.settrace("10.0.3.1")
            for pl in pack_lines:
                if pl.product_id:
                    product = pl.product_id
                    pll = pack_line_model.create({'product_id':pl.product_id.id,
                                                  'disponible':pl.quantity,
                                                  'consumido':0})
                    pack_lines_consumido.append(pll.id)
                    
            line.pack_line_consumido_ids = pack_lines_consumido   
        
        return line
    
    '''
    Sobreescribimos el write para controlar los cambios en el product_id de la 
    linea del pack
    '''
    @api.multi
    def write(self, values):
        #pydevd.settrace("10.0.3.1")
        success = super(contrato_invoice_line, self).write(values) 
        if 'product_id' in values:
            if self.pack_line_consumido_ids:
                for pl in self.product_id.pack_line_ids:
                    for ppl in self.pack_line_consumido_ids:
                        if pl.product_id.id == ppl.product_id.id:
                            ppl.disponible = pl.quantity
                            break
        return success
    
    #===========================================================================
    # '''
    # Sobreescribimos el product_id_change para establecer el precio a partir de la tarifa del cliente
    # '''
    # @api.multi
    # def product_id_change(self, product, uom_id, qty=0, name='', partner_id=False, price_unit=False, pricelist_id=False, company_id=None):
    #     
    #     res = super(contrato_invoice_line, self).product_id_change(product, uom_id, qty, name, partner_id, price_unit, pricelist_id, company_id)
    #     
    #     '''
    #     Obtenemos el precio de tarifa a partir del cliente
    #     '''
    #     #pydevd.settrace("192.168.3.1")
    #     if partner_id and product:
    #         partner = self.env['res.partner'].browse(partner_id)
    #         producto = self.env['product.product'].browse(product)
    #         if partner.property_product_pricelist and partner.property_product_pricelist.version_id:
    #             version_tarifa = partner.property_product_pricelist.version_id[0]
    #             if version_tarifa.items_id:
    #                 for item in version_tarifa.items_id:
    #                     if item.product_id and item.product_id.id == producto.id:
    #                         price_pricelist = item.price_surcharge or producto.lst_price        
    #                         res['value']['price_unit'] = price_pricelist
    #     
    #     return res
    #===========================================================================
    '''
    Metodo que resetea los datos de consumo de las lineas de pack asociadas
    a un contrato
    '''
    def resetear_consumo_pack(self):
        if self.pack_line_consumido_ids:
            for line in self.pack_line_consumido_ids:
                line.consumido = 0
    
    '''
    Metodo invocado desde el boton Modificar Pack de la linea de facturacion periodica
    '''
    @api.multi
    def modificar_pack(self):        
        
        return  {
            'type': 'ir.actions.act_window',
            'name': 'Modificar Pack',            
            #'domain': ['&', ('res_model','=','project.task'), ('res_id','=',context['task_id'])],            
            'res_model': 'account.analytic.invoice.line',
            'res_id': self.id,
            #'context': {'task_id': self.id},                            
            'view_type': 'form',
            'view_mode': 'form',            
            'target': 'new',               
            'nodestroy': True,
        }
    
    '''
    Metodo para marcar una linea como de producto de tipo pack
    Util para ocultar el boton Modificar Pack
    '''
    @api.multi
    def is_pack_line(self):
        for res in self:
            if not res.product_id.pack:
                res.pack_line = False
            else:
                res.pack_line = True
    
    #===========================================================================
    # @api.multi
    # def get_servicio(self):
    #     for res in self:
    #         if res.servicio and res.servicio_model:
    #             servicio = self.env[res.servicio_model].search([('id','=',res.servicio)])
    #             res.servicio_id = servicio.id
    #===========================================================================
    
    #===========================================================================
    # @api.multi
    # def product_id_change(self, product, uom_id, qty=0, name='', partner_id=False, price_unit=False, pricelist_id=False, company_id=None):
    #     pydevd.settrace("10.0.3.1")
    #     super(contrato_invoice_line, self).product_id_change(product, uom_id, qty, name, partner_id, price_unit, pricelist_id, company_id)
    #     
    #     if self.pack_line_consumido_ids:
    #         for pl in self.product_id.pack_line_ids:
    #             for ppl in self.pack_line_consumido_ids:
    #                 if pl.product_id.id == ppl.product_id.id:
    #                     ppl.disponible = pl.quantity
    #                     break
    #===========================================================================


    #Fields
    pack_line_consumido_ids = fields.Many2many('product.pack.contrato', string='Items del pack')
    pack_line = fields.Boolean(compute=is_pack_line)
    #servicio = fields.Integer('Id Servicio')
    #servicio_model = fields.Char('Modelo Servicio')
    #servicio_id = fields.Many2one(compute=get_servicio, string="Servicio")

contrato_invoice_line()

'''
Modelo que sobreescribe account.analytic.account
'''
class contrato(models.Model):
    _name = 'account.analytic.account'
    _inherit = 'account.analytic.account'
    
    '''
    Metodo que obtiene para el producto pasado como argumento la linea correspondiente
    de facturacion recurrente del contrato
    '''
    @api.one
    def obtener_line_factu_recurr_no_pack(self, producto, nueva=False):
        '''
        Si ya existe una linea de facturacion en el contrato para el producto de tipo_producto que
        se haya excedido su consumo del limite del pack se devuelve esa linea
        '''
        lineas_contrato = self.env['account.analytic.invoice.line'].search([('analytic_account_id', '=', self.id)])
        if not nueva:
            for linea in lineas_contrato:
                if linea.product_id.id == producto.id:
                    return linea
        '''
        Sino existe la linea, se crea
        '''
        return self.env['account.analytic.invoice.line'].create(
                        {
                         'analytic_account_id':self.id,
                         'product_id':producto.id,
                         'name':producto.name,
                         'price_unit':producto.lst_price,
                         'uom_id':producto.product_tmpl_id.uom_id.id,
                         'quantity': 0
                         })
    
    '''
    Metodo heredado que ejecuta la logica de creacion periodica de facturas recurrentes
    ''' 
    @api.model
    def _cron_recurring_create_invoice(self):
        current_date =  time.strftime('%Y-%m-%d')
        contract_ids = self.search([('recurring_next_date','<=', current_date),
                                    ('state','=', 'open'),
                                    ('recurring_invoices','=', True),
                                    ('type', '=', 'contract')])
        #Llamada a la implementacion del padre
        invoice_ids = super(contrato, self)._cron_recurring_create_invoice()
        
        #=======================================================================
        # '''
        # Mete el IRPF en cada linea de las facturas generadas obtenido del partner asociado a la compañia
        # TODO La logica no funciona bien, los tax_ids traen un monton de valores y no es posible localizar el que hay que aplicar
        # '''
        # pydevd.settrace("192.168.3.1")
        # if self.env.user.company_id.partner_id.property_account_position:
        #     posicion = self.env.user.company_id.partner_id.property_account_position
        #     if posicion.tax_ids:
        #         tax = posicion.tax_ids[0]
        #         if tax.tax_src_id:
        #             for invoice_id in invoice_ids:
        #                 invoice = self.env['account.invoice'].search([('id','=',invoice_id)])
        #                 for line in invoice.invoice_line:
        #                     line.invoice_line_tax_id += tax.tax_src_id        
        #=======================================================================
               
        self._reiniciar_lineas_contratos(contract_ids)   
             
        return invoice_ids
    
    '''
    Metodo que elimina y reinicia las lineas de facturacion recurrente del contrato
    '''    
    def _reiniciar_lineas_contratos(self, contract_ids):
        #pydevd.settrace("192.168.3.1")
        context = self.env.context or {}
        if contract_ids:
            list_contract_ids = []
            for ci in contract_ids:
                list_contract_ids.append(ci.id) 
            self.env.cr.execute('SELECT company_id, array_agg(id) as ids FROM account_analytic_account WHERE id IN %s GROUP BY company_id', (tuple(list_contract_ids),))
            for company_id, ids in self.env.cr.fetchall():
                for contract in self.search([('id','in',ids)]):
                #for contract in self.browse(context=dict(context, company_id=company_id, force_company=company_id)):
                    lineas_contrato = self.env['account.analytic.invoice.line'].search([('analytic_account_id', '=', contract.id)])
                    for linea in lineas_contrato:                        
                        if linea.product_id:
                            if linea.product_id.pack:
                                #Pone a 0 las lineas de pack
                                linea.resetear_consumo_pack()
                            elif not linea.product_id.contrato:
                                #Borramos linea cuando sea una linea de un producto de pack desbordado
                                linea.unlink()
                            elif linea.product_id.contrato:
                                #Pone a 0 las lineas de productos de servicios en el contrato
                                linea.quantity = 0
                                
    '''
    Crea la oportunidad cuando se alcanza el consumo de advertencia de pack de un cliente
    '''
    def _crear_oportunidad_agotamiento_pack(self, partner, producto):
        '''
        TODO: Ver la posibilidad de comprobar que ya se ha creado una oportunidad para
        ese pack para el agotamiento de otro producto
        '''
        #Creacion de la oportunidad para el partner
        #pydevd.settrace("10.0.3.1")
        description = 'El pack de ' + partner.name + ' a punto de agotar'
        description += ' ' + producto.tipo_producto_pack + 's' if producto.tipo_producto_pack else ''
        self.env['crm.lead'].create({'name':description,
                                     'type':'opportunity',
                                     'partner_id':partner.id,
                                     'phone':partner.phone if partner.phone else '',
                                     'email':partner.email if partner.email else '',
                                     })                                
        
contrato()