# This file is part of Tryton.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.
from decimal import Decimal

from trytond.pool import PoolMeta, Pool
from trytond.config import config
from trytond.transaction import Transaction
from trytond.modules.account_invoice_discount.invoice import DiscountMixin


__all__ = ['Product', 'ProductSupplierPrice']

DISCOUNT_DIGITS = config.getint('product', 'discount_decimal', default=4)


class ProductSupplierPrice(DiscountMixin):
    __metaclass__ = PoolMeta
    __name__ = 'purchase.product_supplier.price'

    @classmethod
    def default_unit_price(cls):
        return Decimal(0)


class Product:
    __metaclass__ = PoolMeta
    __name__ = 'product.product'

    @classmethod
    def get_purchase_discount(cls, products, quantity):
        pool = Pool()
        ProductSupplier = pool.get('purchase.product_supplier')
        ProductSupplierPrice = pool.get('purchase.product_supplier.price')
        Uom = pool.get('product.uom')
        context = Transaction().context

        discounts = {}

        uom = None
        if context.get('uom'):
            uom = Uom(context['uom'])

        for product in products:
            discounts[product.id] = Decimal(0)

            default_uom = product.default_uom
            if not uom:
                uom = default_uom
            pattern = ProductSupplier.get_pattern()
            for product_supplier in product.product_suppliers:
                if product_supplier.match(pattern):
                    pattern = ProductSupplierPrice.get_pattern()
                    for price in product_supplier.prices:
                        if (price.match(quantity, uom, pattern)
                                and price.discount):
                            discounts[product.id] = price.discount
                    break
        return discounts
