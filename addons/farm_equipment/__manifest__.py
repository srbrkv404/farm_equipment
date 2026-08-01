# -*- coding: utf-8 -*-
{
    'name': 'Учёт техники фермерского хозяйства',
    'version': '19.0.1.0.0',
    'summary': 'Учёт тракторов/комбайнов, водителей (механизаторов), моточасов и пробега',
    'description': """
Учёт сельхозтехники
====================
- Карточка техники: название, марка, ширина захвата, расход топлива (л/га или л/час)
- Привязка техники к механизатору (водителю)
- Статус техники: свободна / в работе / на обслуживании
- Журнал работы (смен): моточасы, пробег, обработанная площадь, расход топлива
- Расчёт реальной производительности (га/час) и фактического расхода (л/га)
    """,
    'category': 'Agriculture',
    'author': 'Practice module',
    'license': 'LGPL-3',
    'depends': ['base', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'views/farm_equipment_log_views.xml',
        'views/farm_equipment_views.xml',
        'views/farm_equipment_menus.xml',
    ],
    'installable': True,
    'application': True,
}
