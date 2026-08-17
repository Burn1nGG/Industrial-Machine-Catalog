import unittest
from PySide6.QtCore import Qt
from ui.main_window import MainWindow

class TestEquipmentSorting(unittest.TestCase):
    def setUp(self):
        self.mw = MainWindow.__new__(MainWindow)
        self.mw._active_sort_column = None
        self.mw._active_sort_order = Qt.SortOrder.AscendingOrder

    def test_natural_sort_key_numbers_and_strings(self):
        k1 = MainWindow._natural_sort_key(self.mw, "2")
        k2 = MainWindow._natural_sort_key(self.mw, "10")
        self.assertLess(k1, k2)

        k_inv1 = MainWindow._natural_sort_key(self.mw, "INV-2")
        k_inv2 = MainWindow._natural_sort_key(self.mw, "INV-10")
        self.assertLess(k_inv1, k_inv2)

    def test_natural_sort_key_ip_addresses(self):
        k_ip1 = MainWindow._natural_sort_key(self.mw, "192.168.1.2")
        k_ip2 = MainWindow._natural_sort_key(self.mw, "192.168.1.10")
        self.assertLess(k_ip1, k_ip2)

    def test_natural_sort_key_none_and_empty(self):
        k_none = MainWindow._natural_sort_key(self.mw, None)
        k_empty = MainWindow._natural_sort_key(self.mw, "")
        k_val = MainWindow._natural_sort_key(self.mw, "A")
        self.assertEqual(k_none, k_empty)
        self.assertGreater(k_none, k_val)

    def test_sort_equipment_items_all_columns(self):
        items = [
            {
                'inventory_number': '10',
                'name': 'Станок 1516Ф3',
                'workshop_name': 'Цех 02',
                'cnc_controller': 'NC-210',
                'ip_address': '192.168.1.10',
                'status': 'В работе',
            },
            {
                'inventory_number': '2',
                'name': 'Станок 2А622Ф4',
                'workshop_name': 'Цех 01',
                'cnc_controller': 'Fanuc 0i',
                'ip_address': '192.168.1.2',
                'status': 'В ремонте',
            },
        ]

        # Column 1: name (Станок 2... comes before Станок 1516... in natural sort)
        self.mw._active_sort_order = Qt.SortOrder.AscendingOrder
        res = MainWindow._sort_equipment_items(self.mw, items, 1)
        self.assertEqual([x['name'] for x in res], ['Станок 2А622Ф4', 'Станок 1516Ф3'])

        # Column 2: workshop
        res = MainWindow._sort_equipment_items(self.mw, items, 2)
        self.assertEqual([x['workshop_name'] for x in res], ['Цех 01', 'Цех 02'])

        # Column 3: controller
        res = MainWindow._sort_equipment_items(self.mw, items, 3)
        self.assertEqual([x['cnc_controller'] for x in res], ['Fanuc 0i', 'NC-210'])

        # Column 4: IP address
        res = MainWindow._sort_equipment_items(self.mw, items, 4)
        self.assertEqual([x['ip_address'] for x in res], ['192.168.1.2', '192.168.1.10'])

        # Column 6: Actions column is not sortable
        res = MainWindow._sort_equipment_items(self.mw, items, 6)
        self.assertEqual(res, items)

if __name__ == '__main__':
    unittest.main()
