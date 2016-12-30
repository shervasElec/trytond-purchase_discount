# This file is part of purchase_discount module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
from decimal import Decimal
from trytond.model import fields
from trytond.pool import PoolMeta
from trytond.pyson import Eval
from trytond.modules.purchase.purchase import PurchaseReport
from trytond.config import config as config_

__all__ = ['PurchaseLine', 'PurchaseDiscountReport']

STATES = {
    'invisible': Eval('type') != 'line',
    'required': Eval('type') == 'line',
    }
DIGITS = config_.getint('product', 'price_decimal', default=4)
DISCOUNT_DIGITS = config_.getint('product', 'discount_decimal', default=4)


class PurchaseLine:
    __metaclass__ = PoolMeta
    __name__ = 'purchase.line'

    gross_unit_price = fields.Numeric('Gross Price', digits=(16, DIGITS),
        states=STATES)
    gross_unit_price_wo_round = fields.Numeric('Gross Price without rounding',
        digits=(16, DIGITS + DISCOUNT_DIGITS), readonly=True)
    discount = fields.Numeric('Discount', digits=(16, DISCOUNT_DIGITS),
        states=STATES)

    @classmethod
    def __setup__(cls):
        super(PurchaseLine, cls).__setup__()
        cls.unit_price.states['readonly'] = True
        cls.unit_price.digits = (20, DIGITS + DISCOUNT_DIGITS)
        if 'discount' not in cls.product.on_change:
            cls.product.on_change.add('discount')
        if 'discount' not in cls.unit.on_change:
            cls.unit.on_change.add('discount')
        if 'discount' not in cls.amount.on_change_with:
            cls.amount.on_change_with.add('discount')
        if 'gross_unit_price' not in cls.amount.on_change_with:
            cls.amount.on_change_with.add('gross_unit_price')
        if 'discount' not in cls.quantity.on_change:
            cls.quantity.on_change.add('discount')

    @staticmethod
    def default_discount():
        return Decimal(0)

    def update_prices(self):
        unit_price = None
        gross_unit_price = gross_unit_price_wo_round = self.gross_unit_price
        if self.gross_unit_price is not None and self.discount is not None:
            unit_price = self.gross_unit_price * (1 - self.discount)
            digits = self.__class__.unit_price.digits[1]
            unit_price = unit_price.quantize(Decimal(str(10.0 ** -digits)))

            if self.discount != 1:
                gross_unit_price_wo_round = unit_price / (1 - self.discount)
            digits = self.__class__.gross_unit_price.digits[1]
            gross_unit_price = gross_unit_price_wo_round.quantize(
                Decimal(str(10.0 ** -digits)))

        self.gross_unit_price = gross_unit_price
        self.gross_unit_price_wo_round = gross_unit_price_wo_round
        self.unit_price = unit_price

    @fields.depends('gross_unit_price', 'discount')
    def on_change_gross_unit_price(self):
        return self.update_prices()

    @fields.depends('gross_unit_price', 'discount')
    def on_change_discount(self):
        return self.update_prices()

    @fields.depends('unit_price', 'discount')
    def on_change_product(self):
        super(PurchaseLine, self).on_change_product()
        self.gross_unit_price = self.unit_price
        self.discount = Decimal(0)

        if self.unit_price:
            self.update_prices()

    @fields.depends('unit_price', 'discount')
    def on_change_quantity(self):
        super(PurchaseLine, self).on_change_quantity()
        self.gross_unit_price = self.unit_price
        self.discount = Decimal(0)

        if self.unit_price:
            self.update_prices()

    def get_invoice_line(self):
        lines = super(PurchaseLine, self).get_invoice_line()
        for line in lines:
            line.gross_unit_price = self.gross_unit_price
            line.discount = self.discount
        return lines

    @classmethod
    def create(cls, vlist):
        vlist = [x.copy() for x in vlist]
        for vals in vlist:
            if vals.get('type', 'line') != 'line':
                continue
            gross_unit_price = (vals.get('unit_price', Decimal('0.0'))
                or Decimal('0.0'))
            if 'discount' in vals and vals['discount'] != 1:
                gross_unit_price = gross_unit_price / (1 - vals['discount'])
                digits = cls.gross_unit_price.digits[1]
                gross_unit_price = gross_unit_price.quantize(
                    Decimal(str(10.0 ** -digits)))
            vals['gross_unit_price'] = gross_unit_price
            if not vals.get('discount'):
                vals['discount'] = Decimal(0)
        return super(PurchaseLine, cls).create(vlist)


class PurchaseDiscountReport(PurchaseReport):
    __name__ = 'purchase.purchase.discount'
