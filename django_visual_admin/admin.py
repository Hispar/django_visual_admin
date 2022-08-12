APP_CONFIGURATION = {
    'Users': {
        'slug': 'users',
        'label': 'Usuarios',
    },
    'Cookbook': {
        'slug': 'cookbook',
        'label': 'Cookbook',
    }
}

MODEL_CONFIGURATION = {
    'User': 'Users',
    'Group': 'Users',
    # 'Ingredient': 'Cookbook',
    # 'Recipe': 'Cookbook',
}

CONFIGURATION = [
    {
        'Users': {
            'models': ['User', 'Group'],
            'slug': 'users',
            'label': 'Usuarios'
        }
    },
    {
        'Cookbook': {
            'models': ['Recipe', 'Ingredient']
        }
    },
]
