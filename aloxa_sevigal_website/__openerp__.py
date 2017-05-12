# -*- coding: utf-8 -*-
#################################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2014 Solucións Aloxa S.L. <info@aloxa.eu>
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
    'name': "Portal Web de Clientes para Sevigal",

    'summary': """Modulo website de Sevigal""",

    'description': """
        Portal web para clientes
    """,

    'author': "Solucions Aloxa S.L.",
    'website': "http://www.aloxa.eu",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'Theme/Creative',
    "icon": "/aloxa_sevigal_website/static/src/img/LogoSevigal.png",    
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'calendar',
        'website_forum',
        'aloxa_sevigal_secretaria',
        'bus_enhanced',
        'web_auto_refresh',
        'jsonrpc_keys',
        'web_calendar',
    ],

    # always loaded
    'data': [        
        'views/templates.xml',
        'views/forum.xml',
        'views/forum_mobile.xml'
        #'security/ir.model.access.csv',
    ],
    # only loaded in demonstration mode
    'demo': [        
    ],
    'installable': True,
    'application': True,
}