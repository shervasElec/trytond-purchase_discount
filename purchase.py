# This file is part of purchase_discount module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
from trytond.model import fields
from trytond.pool import PoolMeta, Pool
from trytond.modules.purchase.purchase import PurchaseReport
from trytond.transaction import Transaction
from trytond.modules.account_invoice_discount.invoice import DiscountMixin

__all__ = ['PurchaseLine', 'PurchaseDiscountReport', 'CreatePurchase']


class PurchaseLine(DiscountMixin):
    __metaclass__ = PoolMeta
    __name__ = 'purchase.line'

    def get_purchase_discount(self):
        pool = Pool()
        Product = pool.get('product.product')
        if not self.product:
            return self.discount

        with Transaction().set_context(self._get_context_purchase_price()):
            return Product.get_purchase_discount([self.product],
                abs(self.quantity or 0))[self.product.id]

    @fields.depends('unit_price', 'discount', 'product', 'quantity')
    def on_change_product(self):
        super(PurchaseLine, self).on_change_product()
        self.discount = self.get_purchase_discount()
        self.gross_unit_price = self.on_change_with_gross_unit_price()

    @fields.depends('unit_price', 'discount', 'product', 'quantity', 'unit')
    def on_change_quantity(self):
        super(PurchaseLine, self).on_change_quantity()
        self.discount = self.get_purchase_discount()

    def get_invoice_line(self):
        lines = super(PurchaseLine, self).get_invoice_line()
        for line in lines:
            line.discount = self.discount
        return lines


class PurchaseDiscountReport(PurchaseReport):
    __name__ = 'purchase.purchase.discount'


class CreatePurchase:
    __metaclass__ = PoolMeta
    __name__ = 'purchase.request.create_purchase'

    @classmethod
    def compute_purchase_line(cls, key, requests, purchase):
        pool = Pool()
        Product = pool.get('product.product')
        line = super(CreatePurchase, cls).compute_purchase_line(
            key, requests, purchase)
        if line:
            with Transaction().set_context(uom=line.unit.id,
                    supplier=purchase.party.id,
                    currency=purchase.currency.id):
                line.discount = Product.get_purchase_discount(
                    [line.product], line.quantity)[line.product.id]
        return line
