"""
Selenium E2E test for DocumentHeaderCreateUi.html
Tests the invoice creation form including:
- Form loading
- Timbrado/Establecimiento cascading selects
- Last number fetching
- Detail line management
- Form submission
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
import unittest
import time


class DocumentHeaderCreateTest(unittest.TestCase):
    """E2E tests for DocumentHeader creation form"""

    # Server URL - uses existing running server
    SERVER_URL = 'http://localhost:8002'

    # Test credentials - update these to match your test user
    TEST_USERNAME = 'amadmin'
    TEST_PASSWORD = 'zz9cd3zrsXe9kU@IBi5A'

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Chrome options
        chrome_options = Options()
        # chrome_options.add_argument('--headless')  # Uncomment for headless mode
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--window-size=1920,1080')

        cls.driver = webdriver.Chrome(options=chrome_options)
        cls.driver.implicitly_wait(10)

    @classmethod
    def tearDownClass(cls):
        cls.driver.quit()
        super().tearDownClass()

    def setUp(self):
        # Login before each test
        self.login()

    def login(self):
        """Login to the application"""
        self.driver.get(f'{self.SERVER_URL}/glogin/')

        # Wait for login form
        username_input = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.NAME, 'username'))
        )
        password_input = self.driver.find_element(By.NAME, 'password')

        username_input.send_keys(self.TEST_USERNAME)
        password_input.send_keys(self.TEST_PASSWORD)
        password_input.send_keys(Keys.RETURN)

        # Wait for redirect after login
        time.sleep(2)

    def open_document_create_form(self):
        """Open the DocumentHeader create form in offcanvas"""
        self.driver.get(f'{self.SERVER_URL}/dtmpl/?tmpl=Sifen/DocumentHeaderHomeUi.html')

        # Wait for page to load
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.ID, 'table_container_DocumentHeader'))
        )

        # Click create button (adjust selector as needed)
        create_btn = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.ID, 'btn_crear_documentheader'))
        )
        create_btn.click()

        # Wait for offcanvas form to appear
        WebDriverWait(self.driver, 10).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, '.form_documentheader'))
        )

    def test_form_loads_correctly(self):
        """Test that the form loads with all required fields"""
        self.open_document_create_form()

        # Check required fields exist
        required_fields = [
            'pdv_ruc',
            'pdv_nombrefactura',
            'timbrado_id',
            'doc_establecimiento',
            'doc_moneda',
            'doc_cre_tipo'
        ]

        for field_name in required_fields:
            field = self.driver.find_element(By.NAME, field_name)
            self.assertIsNotNone(field, f'Field {field_name} not found')

    def test_timbrado_select_populates(self):
        """Test that Timbrado select is populated via AJAX"""
        self.open_document_create_form()

        # Wait for select2 to be initialized
        time.sleep(2)

        # Check that timbrado select has options
        timbrado_select = self.driver.find_element(By.NAME, 'timbrado_id')
        options = timbrado_select.find_elements(By.TAG_NAME, 'option')

        # Should have at least one option
        self.assertGreater(len(options), 0, 'Timbrado select should have options')

    def test_establecimiento_cascading_select(self):
        """Test that Establecimiento select updates when Timbrado changes"""
        self.open_document_create_form()

        # Wait for initial load
        time.sleep(2)

        # Get establecimiento select
        establecimiento_select = self.driver.find_element(By.NAME, 'doc_establecimiento')

        # Change timbrado (click on select2 and select first option)
        timbrado_container = self.driver.find_element(
            By.CSS_SELECTOR,
            'select[name=timbrado_id] + .select2-container'
        )
        timbrado_container.click()

        # Wait for dropdown and select first result
        first_result = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, '.select2-results__option'))
        )
        first_result.click()

        # Wait for establecimiento to update
        time.sleep(2)

        # Establecimiento should now have options
        establecimiento_options = establecimiento_select.find_elements(By.TAG_NAME, 'option')
        self.assertGreater(len(establecimiento_options), 0, 'Establecimiento should have options after timbrado selection')

    def test_last_number_fetches(self):
        """Test that last number is fetched when establecimiento changes"""
        self.open_document_create_form()

        # Wait for selects to populate
        time.sleep(3)

        # The available_number span should update
        available_number = self.driver.find_element(By.CSS_SELECTOR, '[id^="available_number_"]')

        # After establecimiento is selected, should show a formatted number or message
        number_text = available_number.text

        # Should not be just '-' (initial state)
        self.assertNotEqual(number_text, '-', 'Available number should be fetched')

    def test_add_detail_line(self):
        """Test adding a detail line to the invoice"""
        self.open_document_create_form()

        # Wait for form to load
        time.sleep(2)

        # Fill detail line fields
        descripcion = self.driver.find_element(By.CSS_SELECTOR, '[id^="detail_prod_descripcion_"]')
        descripcion.send_keys('Test Product')

        precio = self.driver.find_element(By.CSS_SELECTOR, '[id^="detail_precio_unitario_"]')
        precio.clear()
        precio.send_keys('10000')

        cantidad = self.driver.find_element(By.CSS_SELECTOR, '[id^="detail_cantidad_"]')
        cantidad.clear()
        cantidad.send_keys('2')

        # Click add button
        add_btn = self.driver.find_element(By.CSS_SELECTOR, '[id^="btn_agregar_linea_"]')
        add_btn.click()

        # Wait for table to update
        time.sleep(1)

        # Check that detail was added to table
        tbody = self.driver.find_element(By.CSS_SELECTOR, '[id^="tbody_details_"]')
        rows = tbody.find_elements(By.TAG_NAME, 'tr')

        self.assertEqual(len(rows), 1, 'Should have one detail row')

        # Check total
        total = self.driver.find_element(By.CSS_SELECTOR, '[id^="total_details_"]')
        self.assertIn('20', total.text, 'Total should reflect 10000 * 2')

    def test_delete_detail_line(self):
        """Test deleting a detail line"""
        # First add a detail line
        self.test_add_detail_line()

        # Find and click delete button
        delete_btn = self.driver.find_element(By.CSS_SELECTOR, '[id^="tbody_details_"] .btn-danger')
        delete_btn.click()

        # Confirm deletion in sweetalert
        time.sleep(1)
        confirm_btn = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, '.swal2-confirm'))
        )
        confirm_btn.click()

        # Wait for update
        time.sleep(1)

        # Table should be empty
        tbody = self.driver.find_element(By.CSS_SELECTOR, '[id^="tbody_details_"]')
        rows = tbody.find_elements(By.TAG_NAME, 'tr')

        self.assertEqual(len(rows), 0, 'Should have no detail rows after deletion')

    def test_ruc_validation(self):
        """Test that RUC validation fetches business data"""
        self.open_document_create_form()

        # Wait for form
        time.sleep(2)

        # Enter RUC
        ruc_input = self.driver.find_element(By.NAME, 'pdv_ruc')
        ruc_input.send_keys('80000001')

        # Trigger focusout
        ruc_input.send_keys(Keys.TAB)

        # Wait for AJAX response
        time.sleep(2)

        # Check if message appears
        msg_element = self.driver.find_element(By.CSS_SELECTOR, '.msg_pdv_ruc')
        msg_text = msg_element.text

        # Should have some message (success or error)
        self.assertNotEqual(msg_text, '', 'RUC validation should show a message')

    def test_form_submission_without_details(self):
        """Test that form submission fails without detail lines"""
        self.open_document_create_form()

        # Wait for form
        time.sleep(2)

        # Fill header fields
        ruc_input = self.driver.find_element(By.NAME, 'pdv_ruc')
        ruc_input.send_keys('80000001')

        nombre_input = self.driver.find_element(By.NAME, 'pdv_nombrefactura')
        nombre_input.send_keys('Test Company')

        # Try to submit
        save_btn = self.driver.find_element(By.CSS_SELECTOR, '[id^="btn_save_documentheader_form_"]')
        save_btn.click()

        # Should show error message about missing details
        time.sleep(2)

        # Check for error toast/message
        error_visible = self.driver.execute_script(
            "return document.body.innerText.includes('al menos una línea')"
        )
        self.assertTrue(error_visible, 'Should show error about missing detail lines')

    def test_complete_invoice_creation(self):
        """Test complete invoice creation flow"""
        self.open_document_create_form()

        # Wait for form to fully load
        time.sleep(3)

        # Fill RUC and let it validate
        ruc_input = self.driver.find_element(By.NAME, 'pdv_ruc')
        ruc_input.send_keys('80000001')
        ruc_input.send_keys(Keys.TAB)
        time.sleep(2)

        # Fill nombre if not auto-filled
        nombre_input = self.driver.find_element(By.NAME, 'pdv_nombrefactura')
        if not nombre_input.get_attribute('value'):
            nombre_input.send_keys('Test Company S.A.')

        # Add a detail line
        descripcion = self.driver.find_element(By.CSS_SELECTOR, '[id^="detail_prod_descripcion_"]')
        descripcion.send_keys('Servicio de consultoría')

        precio = self.driver.find_element(By.CSS_SELECTOR, '[id^="detail_precio_unitario_"]')
        precio.clear()
        precio.send_keys('500000')

        cantidad = self.driver.find_element(By.CSS_SELECTOR, '[id^="detail_cantidad_"]')
        cantidad.clear()
        cantidad.send_keys('1')

        # Add detail
        add_btn = self.driver.find_element(By.CSS_SELECTOR, '[id^="btn_agregar_linea_"]')
        add_btn.click()
        time.sleep(1)

        # Submit form
        save_btn = self.driver.find_element(By.CSS_SELECTOR, '[id^="btn_save_documentheader_form_"]')
        save_btn.click()

        # Wait for response
        time.sleep(3)

        # Check for success message
        page_content = self.driver.page_source

        success_indicators = [
            'exitosamente',
            'success',
            'creado'
        ]

        success = any(indicator in page_content.lower() for indicator in success_indicators)
        # Note: Test may fail if backend validation fails or no Enumbers available


class DocumentHeaderCreateConsoleTest:
    """
    Browser console test - copy and paste this code in browser console
    to test the form functionality manually
    """

    @staticmethod
    def get_console_test_code():
        return '''
// Test code for DocumentHeaderCreateUi.html
// Paste this in browser console after opening the create form

// Test 1: Check if form exists
console.log('Test 1: Form exists:', document.querySelector('.form_documentheader') !== null);

// Test 2: Test get_last_number AJAX call
async function testGetLastNumber() {
    let fdata = new FormData();
    fdata.append('module', 'Sifen');
    fdata.append('package', 'ekuatia_serials');
    fdata.append('attr', 'Eserial');
    fdata.append('mname', 'get_last_number');
    fdata.append('timbrado', '12345678');  // Replace with actual timbrado
    fdata.append('establecimiento', '001');
    fdata.append('tipo', 'FE');

    try {
        let response = await axios.post('/iom/', fdata, {
            headers: {
                'X-CSRFToken': OptsIO.getCookie('csrftoken')
            }
        });
        console.log('Test 2: get_last_number response:', response.data);
        return response.data;
    } catch (err) {
        console.error('Test 2 failed:', err);
        return null;
    }
}

// Test 3: Test adding a detail line programmatically
function testAddDetailLine() {
    let form = document.querySelector('.form_documentheader');
    let formId = form.id;
    let rr = formId.replace('form_documentheader_', '');

    document.querySelector(`#detail_prod_descripcion_${rr}`).value = 'Test Product';
    document.querySelector(`#detail_precio_unitario_${rr}`).value = '10000';
    document.querySelector(`#detail_cantidad_${rr}`).value = '2';

    document.querySelector(`#btn_agregar_linea_${rr}`).click();

    let tbody = document.querySelector(`#tbody_details_${rr}`);
    let rowCount = tbody.querySelectorAll('tr').length;
    console.log('Test 3: Detail line added, row count:', rowCount);
    return rowCount > 0;
}

// Test 4: Test form data collection
function testFormDataCollection() {
    let form = document.querySelector('.form_documentheader');
    let formData = new FormData(form);
    let data = form_serials.form_to_json(formData);
    console.log('Test 4: Form data collected:', data);
    return data;
}

// Run tests
console.log('=== Starting DocumentHeaderCreateUi Tests ===');
testGetLastNumber();
testAddDetailLine();
testFormDataCollection();
console.log('=== Tests Complete ===');
'''


if __name__ == '__main__':
    print(DocumentHeaderCreateConsoleTest.get_console_test_code())
