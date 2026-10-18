"""Phase 7 source regression tests; no external DB, credentials or server required.

Run: python -m unittest discover -s backend/tests -p test_phase7_ui_lan.py -v
"""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
FRONTEND = (ROOT / 'frontend/src/App.tsx').read_text(encoding='utf8')
BACKEND = (ROOT / 'backend/app/main.py').read_text(encoding='utf8')
AUTH = (ROOT / 'backend/app/auth.py').read_text(encoding='utf8')
LAN = (ROOT / 'Run_LAN.ps1').read_text(encoding='utf8')

class Phase7SourceChecks(unittest.TestCase):
    def test_guest_instructions_have_single_location(self):
        self.assertEqual(FRONTEND.count('id="help"'), 1)
        self.assertIn('!authSession && !sessionChecking', FRONTEND)
        self.assertIn('!authSession && <a className="secondary-button" href="#help">', FRONTEND)
        self.assertIn('How to review land documents', FRONTEND)
        self.assertNotIn('        <section id="help" className="landguard-help-section card">', FRONTEND)

    def test_buyer_does_not_render_admin_registry_sections(self):
        self.assertIn('authSession.user_role === \'admin\' && <section id="admin-review"', FRONTEND)
        self.assertIn('authSession.user_role !== \'buyer\' && <section id="demo-registry"', FRONTEND)
        self.assertIn('<section id="my-documents"', FRONTEND)
        self.assertNotIn('<a href="#demo-registry">', FRONTEND)
        # The existing backend, not only the UI, must enforce admin permissions.
        self.assertIn("@role_required('admin')", BACKEND)
        self.assertIn('def role_required(*roles)', AUTH)

    def test_clear_does_not_delete_persistent_history(self):
        reset_block=FRONTEND.split('  const resetDemoComparison = () => {',1)[1].split('\n  const resetAdminRecord',1)[0]
        self.assertIn('setCurrentDemoResult(null)',reset_block)
        self.assertIn('setShowSavedDemoHistory(false)',reset_block)
        self.assertNotIn('setRegistryHistory([])',reset_block)
        self.assertIn('setCurrentDemoResult(',FRONTEND)
        self.assertIn('await fetchDemoWorkspace();', FRONTEND)
        self.assertIn('Show saved history',FRONTEND)
        self.assertIn('aria-expanded={showSavedDemoHistory}',FRONTEND)

    def test_private_lan_does_not_expose_database_or_backend(self):
        self.assertIn('Get-NetConnectionProfile',LAN)
        self.assertIn("$network.NetworkCategory -ne 'Private'", LAN)
        self.assertIn('-RemoteAddress LocalSubnet', LAN)
        self.assertIn('-Profile Private', LAN)
        self.assertIn('LANDGUARD_ALLOWED_ORIGINS', LAN)
        self.assertIn('http://127.0.0.1:4173', LAN)
        self.assertIn('http://{0}:4173', LAN)
        self.assertNotIn('docker compose down', LAN)
        self.assertNotIn('New-NetFirewallRule -DisplayName $ruleName -Direction Inbound -Action Allow -Protocol TCP `\n            -LocalPort 8000',LAN)
        self.assertIn("app.run(host='127.0.0.1', port=8000", BACKEND)
        self.assertIn('"127.0.0.1:5432:5432"',(ROOT/'docker-compose.yml').read_text())

if __name__ == '__main__':
    unittest.main()
