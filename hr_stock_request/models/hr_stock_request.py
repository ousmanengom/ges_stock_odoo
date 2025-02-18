from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError


class HRStockRequest(models.Model):
    _name = 'hr.stock.request'
    _description = 'Demande de Matériel'

    @api.depends('picking_ids')
    def _compute_picking_count(self):
        for order in self:
            order.picking_count = len(order.picking_ids)

    name = fields.Char(string='Référence', required=True, copy=False, readonly=True, default=lambda self: self.env['ir.sequence'].next_by_code('hr.stock.request'))
    employee_id = fields.Many2one(
        'hr.employee',
        string='Employé',
        required=True,
        default=lambda self: self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
    )
    user_id = fields.Many2one('res.users', string='Utilisateur', default=lambda self: self.env.user, readonly=True)
    department_id = fields.Many2one('hr.department', string='Service', related='employee_id.department_id')
    #rang_hierarchique_id = fields.Many2one('rang.hierarchique', string='Rang Hierarchique', related='employee_id.rang_hierarchique_id')
    date_request = fields.Date(string='Date', default=fields.Date.today)
    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('dep_valid', 'Chef de Département'),
        ('pole_valid', 'Chef de Pôle'),
        ('dex_valid', 'DEX'),
        ('logistics_valid', 'Logistique'),
        ('done', 'Fait'),
        ('cancel', 'Annulé')
    ], string='État', default='draft')
    request_line_ids = fields.One2many('hr.stock.request.line', 'request_id', string='Lignes de demande')
    picking_ids = fields.One2many('stock.picking', 'request_id', string='Transfert Stock', readonly=True)
    picking_count = fields.Integer("Shipment count", compute='_compute_picking_count')

    def action_validate_department(self):
        self.write({'state': 'dep_valid'})

    def action_validate_pole(self):
        self.write({'state': 'pole_valid'})

    def action_validate_dex(self):
        self.write({'state': 'dex_valid'})


    def action_validate_logistics(self):
        self.ensure_one()  # S'assure que l'action est exécutée sur un seul enregistrement

        # Récupérer le picking type avec code 'ATT'
        picking_type_id = self.env['stock.picking.type'].search([('sequence_code', '=', 'ATT')], limit=1)
        if not picking_type_id:
            raise ValueError("Aucun type de transfert avec le code 'ATT' trouvé.")

        # Déterminer location_dest_id : premier dans location_ids ou valeur par défaut
        location_dest = self.employee_id.location_ids[:1] or self.env.ref('stock.stock_location_customers')

        picking_vals = {
            'picking_type_id': picking_type_id.id,
            'origin': self.name,
            'location_dest_id': location_dest.id,  # Utilise la méthode pour obtenir l'emplacement de destination
            'location_id': self.env.ref('stock.stock_location_stock').id,
            'request_id': self.id,
            'employee_id': self.employee_id.id,
        }

        # Crée le picking
        picking = self.env['stock.picking'].create(picking_vals)

        # Crée les mouvements de stock pour chaque ligne de commande
        for line in self.request_line_ids:
            if line.product_id:
                move_vals = {
                    'product_id': line.product_id.id,
                    'product_uom_qty': line.quantity,
                    'product_uom': line.product_id.uom_id.id,
                    'name': f"Attribution {self.name}",
                    'picking_id': picking.id,
                    'location_id': picking.location_id.id,
                    'location_dest_id': picking.location_dest_id.id,
                }
                self.env['stock.move'].create(move_vals)

        #picking.action_confirm()

        # Met à jour la requete avec le picking créé
        self.picking_ids = [(4, picking.id)]
        self.write({'state': 'logistics_valid'})


    def action_cancel(self):
        self.write({'state': 'cancel'})

    def action_view_picking(self):
        return self._get_action_view_picking(self.picking_ids)

    def _get_action_view_picking(self, pickings):
        ctx = self._context.copy()

        action = {
            "name": "Attribution",
            "type": "ir.actions.act_window",
            "view_mode": "form",
            "res_model": "stock.picking",
            "context": ctx,
        }
        if len(pickings) == 1:
            action.update({"view_mode": "form", "res_id": pickings.id})
        elif len(pickings) > 1:
            action.update(
                {"view_mode": "tree,form", "domain": [("id", "in", pickings.ids)]}
            )
        else:
            raise ValidationError(
                "Il y'a pas encore de mouvement veuillez vérifier au niveau"
                " des validation."
            )
        return action


class HRStockRequestLine(models.Model):
    _name = 'hr.stock.request.line'
    _description = 'Ligne de Demande de Matériel'

    request_id = fields.Many2one('hr.stock.request', string='Demande', required=True, ondelete='cascade')
    product_id = fields.Many2one('product.product', string='Produit', required=True)
    description = fields.Char(string='Description')
    quantity = fields.Float(string='Quantité', required=True, default=1.0)



class StockLocation(models.Model):
    _inherit = "stock.location"

    employee_id = fields.Many2one('hr.employee')


class HrEmployeeBase(models.AbstractModel):
    _inherit = "hr.employee.base"

    location_ids = fields.Many2many('stock.location', string='Bureau')

class StockPickingType(models.Model):
    _inherit = "stock.picking.type"

    is_desk = fields.Boolean(string="Est un type pour rangement bureau")


class StockPicking(models.Model):
    _inherit = "stock.picking"

    type_is_desk = fields.Boolean(string="Est un type pour rangement bureau", related='picking_type_id.is_desk')
    employee_id = fields.Many2one('hr.employee')
    location_domain = fields.Many2many(
        'stock.location', compute='_compute_location_domain', store=False
    )
    request_id = fields.Many2one('hr.stock.request', string='Request')

    @api.depends('employee_id')
    def _compute_location_domain(self):
        """Met à jour le domaine de location_dest_id selon les locations de l'employé"""
        for record in self:
            if record.employee_id and record.employee_id.location_ids:
                record.location_domain = record.employee_id.location_ids
            else:
                record.location_domain = self.env['stock.location'].search([])  # Toutes les locations

    def action_assign(self):
        """ Check availability of picking moves.
        This has the effect of changing the state and reserve quants on available moves, and may
        also impact the state of the picking as it is computed based on move's states.
        @return: True
        """
        res = super(StockPicking, self).action_assign()
        for move in self.move_line_ids_without_package:
            move.sudo().write({
                'employee_id': self.employee_id.id,
            })
        return res

class StockMove(models.Model):
    _inherit = 'stock.move'

    def _action_done(self,**kwargs):
        res = super(StockMove, self)._action_done()
        for move in self:
            for move_line in move.move_line_ids:
                quants = self.env['stock.quant'].search([
                    #('product_id', '=', move_line.product_id.id),
                    #('location_id', '=', move_line.location_dest_id.id),
                    ('lot_id', '=', move_line.lot_id.id),
                ])
                for quant in quants:
                    quant.sudo().write({
                        'move_line_id': move_line.id,
                    })

        return res