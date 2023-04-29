# -*- coding: utf-8 -*-
{
    'name': "Custom Discount",

    'summary': """
        custom_discount""",

    'description': """
        custom_discount
    """,

    'author': "Melia",
    'website': "https://github.com/meliaprisca",

    'category': 'Accounting',
    'version': '1.0',

    # any module necessary for this one to work correctly
    'depends': [
            'base',
            'account'
            ],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        # 'data/keda_material_data.xml',
        'views/account_move.xml',
        'wizard/account_discount_amount.xml',
        # 'views/keda_template.xml',
    ],
}
