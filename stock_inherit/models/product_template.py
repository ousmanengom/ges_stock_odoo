from odoo import models, fields, api

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    brand_id = fields.Many2one('product.brand', string='Marque', domain="[('categ_id', '=', categ_id)])")
    modal_id = fields.Many2one('product.modal', string='Modèle', domain="[('brand_id', '=', brand_id)]")

    @api.onchange('categ_id')
    def _onchange_categ_id(self):
        if self.categ_id:
            self.brand_id = False
            self.modal_id = False

    @api.onchange('brand_id')
    def _onchange_brand_id(self):
        if self.brand_id:
            self.modal_id = False

class ProductCategory(models.Model):
    _inherit = 'product.category'
    brand_ids = fields.One2many(comodel_name='product.brand', inverse_name='categ_id', string='Marques')
    modal_ids = fields.One2many('product.modal', 'categ_id', string='Modèle')


class ProductBrand(models.Model):
    _name = 'product.brand'
    _description = 'Product Brand'

    name = fields.Char('Brand Name', required=True)
    modal_ids = fields.One2many('product.modal', 'brand_id', string='Modèle')
    categ_id = fields.Many2one('product.category', 'Product Category')

class ProductModal(models.Model):
    _name = 'product.modal'
    _description = 'Product Modal'

    name = fields.Char('Modèle', required=True)
    brand_id = fields.Many2one('product.brand', string='Marque')
    categ_id = fields.Many2one('product.category', 'Catégorie')


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    status = fields.Selection(
        [
            ('neuf', 'Neuf'),
            ('reconditionne', 'Reconditionné'),
            ('seconde_main', 'Seconde Main'),
        ],
        string='Etat', )
    employee_id = fields.Many2one('hr.employee', string="Employé")

    year = fields.Selection(
        [
            ('2015', '2015'),
            ('2016', '2016'),
            ('2017', '2017'),
            ('2018', '2018'),
            ('2019', '2019'),
            ('2020', '2020'),
            ('2021', '2021'),
            ('2022', '2022'),
            ('2023', '2023'),
            ('2024', '2024'),
            ('2025', '2025'),
            ('2026', '2026'),
            ('2027', '2027'),
            ('2028', '2028'),
            ('2029', '2029'),
            ('2030', '2030'),

        ],
        string='Année', )

    cartouche = fields.Char(
        string='Cartouche')
    cartouche_readonly = fields.Boolean(
        string="Readonly Cartouche",
        compute="_compute_cartouche_readonly",
        store=True
    )

    @api.depends('product_id')
    def _compute_cartouche_readonly(self):
        for record in self:
            record.cartouche_readonly = record.product_id and record.product_id.name.lower() != 'imprimante'

    @api.onchange('cartouche_readonly')
    def _onchange_cartouche_readonly(self):
        if self.cartouche_readonly:
            self.cartouche = False

    os = fields.Selection(
            [
                ('window 11', 'window 11'),
                ('window 10', 'window 10'),
                ('ios', 'ios'),
                ('macOS', 'macOS'),
                ('Android', 'Android'),
            ],
            string='os'
        )
    os_readonly = fields.Boolean(
        string="Readonly Os",
        compute="_compute_os_readonly",
        store=True
    )

    @api.depends('product_id')
    def _compute_os_readonly(self):
        for record in self:
            record.os_readonly = record.product_id and record.product_id.name.lower() != 'ordinateur'

    @api.onchange('os_readonly')
    def _onchange_os_readonly(self):
        if self.os_readonly:
            self.os = False

    description = fields.Char('Description')
    remark = fields.Char('Remarque')

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

class StockQuant(models.Model):
    _inherit = "stock.quant"

    move_line_id = fields.Many2one(
        comodel_name="stock.move.line",
        string="Move Line",
        help="Related stock move line for this quant",
    )
    status = fields.Selection(
        related='move_line_id.status', string="Etat", store=True
    )
    employee_id = fields.Many2one(
        related='move_line_id.employee_id', string="Employé", store=True
    )
    year = fields.Selection(
        related='move_line_id.year', string="Année", store=True
    )
    cartouche = fields.Char(
        related='move_line_id.cartouche', string="Cartouche", store=True
    )
    os = fields.Selection(
        related='move_line_id.os', string="os", store=True
    )
    description = fields.Char(
        related='move_line_id.description', string="Description", store=True
    )
    remark = fields.Char(
        related='move_line_id.remark', string="Remarque", store=True
    )