from odoo import models, fields, api

class ProjectTaskTimerWizard(models.TransientModel):
    _name = 'project.task.timer.wizard'
    _description = 'Project Task Timer Wizard'

    user_id = fields.Many2one(
        'res.users',
        string='Employee',
        default=lambda self: self.env.user,
        required=True,
        readonly=True
    )
    project_id = fields.Many2one('project.project', string='Project', required=True)
    task_id = fields.Many2one('project.task', string='Task', domain="[('project_id', '=', project_id)]", required=True)
    start_date = fields.Datetime(
        string='Start Date',
        default=fields.Datetime.now,
        required=True
    )
    def action_start_task(self):
        self.ensure_one()
           
        self.env['project.task.timer'].search([
            ('user_id', '=', self.env.user.id),
            ('is_running', '=', True)
        ]).write({'is_running': False})
        
       
        self.env['project.task.timer'].create({
            'user_id': self.user_id.id,
            'project_id': self.project_id.id,
            'task_id': self.task_id.id,
            'start_time': self.start_date,
            'is_running': True,
        })
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    
        
