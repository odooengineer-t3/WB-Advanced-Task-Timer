# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) Wan Buffer Solution (<https://wanbuffer.com/>).
#
#    For Module Support : info@wanbuffer.com  or Call : +91 9638442270
#
##############################################################################
# -*- coding: utf-8 -*-
{
    'name': 'Advanced Task Timer',
    'version': '19.0',
    'category': 'Project',
    'author': 'Wan Buffer Services',
    'summary': 'Task time tracking with timer',
    'description': 'Advanced task time tracking with popup-based timer and real-time visibility.',
    'depends': [
        'web',
        'project',
        'hr_timesheet',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/kanban_view_task.xml',
        'wizard/timer_wizard_view.xml',
        'wizard/end_timer_wizard_view.xml',
    ],
    'post_init_hook': 'post_init_hook',
    'assets': {
        'web.assets_backend': [
            'wb_advance_task_timer/static/src/xml/timer_button_popup.xml',
            'wb_advance_task_timer/static/src/js/timer_button_popup.js',
            'wb_advance_task_timer/static/src/js/kanban_view.js',
        ],
    },
    'images': [
        'static/description/Task Timer - 19.png',   # App Store banner
        'static/description/icon.png',     # App icon
    ],
    'website': 'https://wanbuffer.com',
    'maintainer': 'Wan Buffer Services',
    'support': 'info@wanbuffer.com',
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
