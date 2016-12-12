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


{
    "name": "Módulo de Secretaría Virtual para Sevigal",
    "version": "0.1",
    "category": "",
    "icon": "/aloxa_sevigal_secretaria/static/src/img/icon.png",
    "depends": [
                'base',                
                'crm',
                'document',
                'website',
                'website_forum',
                'account_analytic_analysis',
                'product_pack',
                'portal',
                'analytic',
                ],
    "author": "Solucións Aloxa S.L.",
    "description": "Módulo de Secretaría Virtual para Sevigal",
    "init_xml": [],
    "data": ['data/ir.module.category.csv',
             'data/res.groups.csv',
             'data/forum.forum.csv',
             'data/sevigal.opciones.csv',
             'data/ir.rule.csv',
             'views/opciones.xml',
             'views/servicios.xml',
             'views/llamadas.xml',
             'views/actions.xml',
             'views/menus.xml',
             'views/contratos.xml',
             'views/productos.xml',
             'views/clientes.xml',
             'views/mails.xml',
             'views/mensajes.xml',
             'views/avisos.xml',
             'views/usuarios.xml',
             'views/inherit_report_invoice.xml',
             'views/inherit_invoice_form.xml',
             'workflows.xml',
             'security/ir.model.access.csv',
             'data/ir.ui.menu.csv',
             ],
    "demo_xml": [],
    "installable": True,
    "active": False,
}
