# -*- coding: utf-8 -*-
# Python imports

# 3rd Party imports

# App imports


APP_CONFIGURATION = {
    'Users': {
        'slug': 'users',
        'label': 'Usuarios',
    }
}

MODEL_CONFIGURATION = {
    'User': 'Users',
    'Group': 'Users',
}

CONFIGURATION = [
    {
        'Users': {
            'models': ['User', 'Group'],
            'slug': 'users',
            'label': 'Usuarios'
        }
    },
    # {
    #     'Cookbook': {
    #         'models': ['Recipe', 'Ingredient']
    #     }
    # },
]
