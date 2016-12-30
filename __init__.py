# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.pool import Pool
from .purchase import *
from .move import *

def register():
    Pool.register(
        PurchaseLine,
        Move,
        module='purchase_discount', type_='model')
    Pool.register(
        PurchaseDiscountReport,
        module='purchase_discount', type_='report')
