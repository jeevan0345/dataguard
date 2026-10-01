"""
Test Suite: Phase 4 Security Hardening, Production Configuration, and RBAC Guardrails
"""

import os
import unittest
from unittest.mock import patch
from uuid import uuid4
from fastapi.testclient import TestClient

from app.main import app
from app.database.session import SessionLocal
from app.models.user import User
from app.core.security import create_access_token, hash_password


class TestPhase4SecurityHardening(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.db = SessionLocal()

        cls.user = User(
            id=uuid4(),
            email=f"phase4_eng_{uuid4().hex[:6]}@dataguard.ai",
            full_name="Phase 4 Engineer",
            hashed_password=hash_password("ValidPassword123!"),
            role="DATA_ENGINEER",
            is_active=True,
        )
        cls.db.add(cls.user)
        cls.db.commit()

        cls.token = create_access_token({"sub": str(cls.user.id), "role": "DATA_ENGINEER", "email": cls.user.email})

    @classmethod
    def tearDownClass(cls):
        cls.db.close()

    def test_prevent_self_elevation_to_admin_on_register(self):
        """
        Public registration attempting role='ADMIN' must be demoted to DATA_ENGINEER.
        """
        email = f"elevate_{uuid4().hex[:6]}@dataguard.ai"
        payload = {
            "email": email,
            "full_name": "Wannabe Admin",
            "password": "Password123!",
            "role": "ADMIN",
        }
        resp = self.client.post("/auth/register", json=payload)
        self.assertEqual(resp.status_code, 201)
        data = resp.json()
        self.assertEqual(data["user"]["role"], "DATA_ENGINEER")
        self.assertFalse(data["user"]["is_superuser"])

    def test_seed_demo_users_blocked_in_production(self):
        """
        /auth/seed-demo-users must return 403 Forbidden when ENV=production.
        """
        with patch.dict(os.environ, {"ENV": "production"}):
            resp = self.client.post("/auth/seed-demo-users")
            self.assertEqual(resp.status_code, 403)
            self.assertIn("disabled in production", resp.json()["detail"])

    def test_login_rate_limiting_enforced(self):
        """
        Exceeding 10 consecutive failed logins must trigger HTTP 429 Too Many Requests.
        """
        target_email = f"victim_{uuid4().hex[:6]}@dataguard.ai"
        for _ in range(10):
            resp = self.client.post("/auth/login", json={"email": target_email, "password": "BadPassword"})
            self.assertEqual(resp.status_code, 401)

        # 11th attempt must be rejected by rate limiter
        resp_blocked = self.client.post("/auth/login", json={"email": target_email, "password": "BadPassword"})
        self.assertEqual(resp_blocked.status_code, 429)
        self.assertIn("Too many failed login attempts", resp_blocked.json()["detail"])

    def test_report_download_path_traversal_blocked(self):
        """
        Attempting directory traversal via /agents/reports/download/ must be blocked.
        """
        resp = self.client.get(
            "/agents/reports/download/../../../../windows/system32/cmd.exe",
            headers={"Authorization": f"Bearer {self.token}"},
        )
        # Should be rejected with 404 or 403
        self.assertIn(resp.status_code, [403, 404])


if __name__ == "__main__":
    unittest.main()
