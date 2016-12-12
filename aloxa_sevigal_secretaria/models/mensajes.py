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

'''
Modelo que extiende res.partner para agregar campos al modelo para gestion de llamadas
'''
class forum_post(models.Model):
    _name = 'forum.post'
    _inherit = 'forum.post'
    
    #Fields
    tipo = fields.Selection([('Notificacion', 'Notificación'), ('Mensaje', 'Mensaje'), ('Reunion', 'Reunión'), ('Viaje','Viaje')],
                            string="Tipo de Mensaje")
    partner_id = fields.Many2one('res.partner', 'Receptor')
    
forum_post()