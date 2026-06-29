from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from hospitalapp.models import Supplier, InventoryItem

User = get_user_model()

class InventoryDashboardTestCase(TestCase):
    def setUp(self):
        self.admin_user = User.objects.create_user(
            username='admin_user', password='password', role='admin'
        )
        self.supplier = Supplier.objects.create(
            name='Test Supplier',
            phone='1234567890'
        )
        self.item = InventoryItem.objects.create(
            item_code='TEST-ITEM-1',
            name='Surgical Mask',
            category='Surgical Items',
            uom='Box',
            purchase_price=10.00,
            selling_price=15.00,
            current_stock=100,
            supplier=self.supplier
        )

    def test_inventory_dashboard_access(self):
        self.client.login(username='admin_user', password='password')
        url = reverse('admin_inventory_dashboard')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Advanced Inventory Portal')

    def test_add_item_post(self):
        self.client.login(username='admin_user', password='password')
        url = reverse('inventory_items')
        post_data = {
            'action': 'add_item',
            'item_code': 'TEST-ITEM-2',
            'name': 'Gloves',
            'category': 'Surgical Items',
            'uom': 'Box',
            'purchase_price': '12.00',
            'selling_price': '20.00',
            'current_stock': '50',
            'supplier': self.supplier.id
        }
        response = self.client.post(url, post_data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(InventoryItem.objects.filter(item_code='TEST-ITEM-2').exists())

    def test_split_inventory_pages_access(self):
        self.client.login(username='admin_user', password='password')
        sub_routes = [
            'inventory_items', 'inventory_suppliers', 'inventory_purchase',
            'inventory_grn', 'inventory_expiry', 'inventory_issue',
            'inventory_biomedical', 'inventory_emergency', 'inventory_reports'
        ]
        for route in sub_routes:
            url = reverse(route)
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200, f"Failed to load route: {route}")
            if route == 'inventory_items':
                self.assertContains(response, 'Surgical Mask')
            elif route == 'inventory_suppliers':
                self.assertContains(response, 'Test Supplier')

    def test_store_keeper_access_restrictions(self):
        sk_user = User.objects.create_user(
            username='sk_user', password='password', role='store_keeper'
        )
        self.client.login(username='sk_user', password='password')
        
        # Should be able to access the main dashboard
        response = self.client.get(reverse('admin_inventory_dashboard'))
        self.assertEqual(response.status_code, 200)
        
        # Should be able to access sub-modules (should return 200 OK)
        response = self.client.get(reverse('inventory_items'))
        self.assertEqual(response.status_code, 200)
        
        response = self.client.get(reverse('inventory_suppliers'))
        self.assertEqual(response.status_code, 200)

    def test_add_store_keeper_post(self):
        self.client.login(username='admin_user', password='password')
        url = reverse('add_store_keeper')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        post_data = {
            'username': 'storekeeper1',
            'email': 'sk@example.com',
            'password': 'password123',
            'confirm_password': 'password123',
        }
        response = self.client.post(url, post_data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(username='storekeeper1', role='store_keeper').exists())

    def test_supplier_duplicate_prevention(self):
        self.client.login(username='admin_user', password='password')
        url = reverse('inventory_suppliers')
        post_data = {
            'action': 'add_supplier',
            'name': 'Test Supplier', # Matches self.supplier.name case insensitively
            'phone': '0987654321'
        }
        # Verify it redirects, but doesn't add another supplier to the database
        initial_count = Supplier.objects.filter(name__iexact='Test Supplier').count()
        response = self.client.post(url, post_data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Supplier.objects.filter(name__iexact='Test Supplier').count(), initial_count)

    def test_supplier_update_and_delete(self):
        self.client.login(username='admin_user', password='password')
        # Test Update GET
        update_url = reverse('update_supplier', args=[self.supplier.id])
        response = self.client.get(update_url)
        self.assertEqual(response.status_code, 200)

        # Test Update POST
        post_data = {
            'name': 'Updated Supplier',
            'phone': '1112223333',
            'is_active': 'on'
        }
        response = self.client.post(update_url, post_data)
        self.assertEqual(response.status_code, 302)
        self.supplier.refresh_from_db()
        self.assertEqual(self.supplier.name, 'Updated Supplier')

        # Test Delete
        delete_url = reverse('delete_supplier', args=[self.supplier.id])
        response = self.client.post(delete_url)
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Supplier.objects.filter(id=self.supplier.id).exists())

    def test_report_exports(self):
        self.client.login(username='admin_user', password='password')
        for report in ['movement', 'valuation', 'expiry']:
            for fmt in ['csv', 'pdf']:
                url = reverse('export_inventory_report', args=[report, fmt])
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)
                if fmt == 'csv':
                    self.assertEqual(response['Content-Type'], 'text/csv')
                elif fmt == 'pdf':
                    self.assertEqual(response['Content-Type'], 'application/pdf')

    def test_request_inventory_item(self):
        lab_user = User.objects.create_user(
            username='lab_user', password='password', role='laboratoryist'
        )
        self.client.login(username='lab_user', password='password')
        
        url = reverse('request_inventory_item')
        
        # Test GET access
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        
        # Test POST requisition submission
        from hospitalapp.models import PurchaseRequisition
        post_data = {
            'item': self.item.id,
            'quantity': 10,
            'department': 'Laboratory'
        }
        response = self.client.post(url, post_data)
        self.assertEqual(response.status_code, 302)
        
        # Verify requisition was created in database
        self.assertTrue(PurchaseRequisition.objects.filter(
            requested_by=lab_user,
            item=self.item,
            quantity=10,
            department='Laboratory'
        ).exists())

    def test_approve_requisition(self):
        from hospitalapp.models import PurchaseRequisition
        self.client.login(username='admin_user', password='password')
        # Create a pending requisition first
        req = PurchaseRequisition.objects.create(
            req_number='REQ-99901',
            department='Laboratory',
            requested_by=self.admin_user,
            item=self.item,
            quantity=5,
            status='Pending'
        )
        url = reverse('approve_requisition', args=[req.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        req.refresh_from_db()
        self.assertEqual(req.status, 'Approved')

    def test_reject_requisition(self):
        from hospitalapp.models import PurchaseRequisition
        self.client.login(username='admin_user', password='password')
        req = PurchaseRequisition.objects.create(
            req_number='REQ-99902',
            department='Radiology',
            requested_by=self.admin_user,
            item=self.item,
            quantity=3,
            status='Pending'
        )
        url = reverse('reject_requisition', args=[req.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        req.refresh_from_db()
        self.assertEqual(req.status, 'Rejected')

    def test_receptionist_can_request_inventory(self):
        from hospitalapp.models import PurchaseRequisition
        receptionist = User.objects.create_user(
            username='receptionist1', password='password', role='receptionist'
        )
        self.client.login(username='receptionist1', password='password')
        url = reverse('request_inventory_item')

        # GET should succeed
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        # POST should create requisition with Casualty department
        post_data = {
            'item': self.item.id,
            'quantity': 2,
            'department': 'Casualty'
        }
        response = self.client.post(url, post_data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(PurchaseRequisition.objects.filter(
            requested_by=receptionist,
            department='Casualty'
        ).exists())

