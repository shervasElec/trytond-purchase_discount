# This file is part of the purchase_discount module for Tryton.
# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
import unittest
import doctest
from decimal import Decimal

import trytond.tests.test_tryton
from trytond.tests.test_tryton import ModuleTestCase, with_transaction
from trytond.tests.test_tryton import doctest_teardown
from trytond.tests.test_tryton import doctest_checker
from trytond.pool import Pool
from trytond.transaction import Transaction

from trytond.modules.company.tests import create_company, set_company
from trytond.modules.account.tests import create_chart


class PurchaseDiscountTestCase(ModuleTestCase):
    'Test Purchase Discount module'
    module = 'purchase_discount'

    @with_transaction()
    def test_purchase_discount(self):
        'Test purchase discount'
        pool = Pool()
        Template = pool.get('product.template')
        Product = pool.get('product.product')
        Uom = pool.get('product.uom')
        ProductSupplier = pool.get('purchase.product_supplier')
        Party = pool.get('party.party')

        company = create_company()
        with set_company(company):
            create_chart(company)

            kg, = Uom.search([('name', '=', 'Kilogram')])

            template, = Template.create([{
                        'name': 'Product',
                        'default_uom': kg.id,
                        'purchase_uom': kg.id,
                        'list_price': Decimal(5),
                        'cost_price': Decimal(2),
                        'products': [('create', [{}])],
                        }])
            product, = template.products

            supplier, = Party.create([{
                        'name': 'Supplier',
                        }])
            product_supplier, = ProductSupplier.create([{
                        'product': template.id,
                        'party': supplier.id,
                        'prices': [('create', [{
                                        'sequence': 1,
                                        'discount': Decimal('0.3'),
                                        'quantity': 5,
                                        'unit_price': Decimal(3),
                                        }, {
                                        'sequence': 2,
                                        'discount': Decimal('0.5'),
                                        'quantity': 10,
                                        'unit_price': Decimal(2),
                                        }])],
                        }])

            with Transaction().set_context(supplier=supplier.id, uom=kg):
                discount = Product.get_purchase_discount([product],
                    quantity=2)
                self.assertEqual(discount, {product.id: Decimal('0')})
                discount = Product.get_purchase_discount([product],
                    quantity=5)
                self.assertEqual(discount, {product.id: Decimal('0.3')})
                discount = Product.get_purchase_discount([product],
                    quantity=10)
                self.assertEqual(discount, {product.id: Decimal('0.5')})


def suite():
    suite = trytond.tests.test_tryton.suite()
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(
        PurchaseDiscountTestCase))
    suite.addTests(doctest.DocFileSuite('scenario_purchase.rst',
            tearDown=doctest_teardown, encoding='utf-8',
            checker=doctest_checker,
            optionflags=doctest.REPORT_ONLY_FIRST_FAILURE))
    return suite
