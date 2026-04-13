# Импортируем все роутеры из обработчиков
from . import start
from . import catalog
from . import cart
from . import order
from . import bonuses
from . import reviews
from . import contest
from . import admin
from . import analytics

__all__ = [
    'start',
    'catalog',
    'cart',
    'order',
    'bonuses',
    'reviews',
    'contest',
    'admin',
    'analytics'
]
