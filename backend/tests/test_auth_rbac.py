"""
Test Suite: DataGuard Authentication & Role-Based Access Control (RBAC)
"""

import unittest
from uuid import uuid4
from app.core.security import hash_password, verify_password, create_access_token, decode_access_token
from app.database.session import SessionLocal
from app.models.user import User
from app.auth.service import AuthService
from app.auth.schemas import UserRegister


class TestAuthRBAC(unittest.TestCase):

    def setUp(self):
        self.db = SessionLocal()

    def tearDown(self):
        self.db.close()

    def test_password_hashing(self):
        raw_password = "SecurePassword2026!"
        hashed = hash_password(raw_password)
        self.assertNotEqual(raw_password, hashed)
        self.assertTrue(verify_password(raw_password, hashed))
        self.assertFalse(verify_password("WrongPassword", hashed))

    def test_jwt_token_flow(self):
        payload = {"sub": str(uuid4()), "role": "DATA_ENGINEER", "email": "test@dataguard.ai"}
        token = create_access_token(payload)
        decoded = decode_access_token(token)
        self.assertIsNotNone(decoded)
        self.assertEqual(decoded["role"], "DATA_ENGINEER")
        self.assertEqual(decoded["email"], "test@dataguard.ai")

    def test_user_rbac_roles(self):
        roles = ["ADMIN", "DATA_ENGINEER", "VIEWER"]
        for role in roles:
            test_email = f"test_{role.lower()}_{uuid4().hex[:6]}@dataguard.ai"
            user = AuthService.register_user(
                self.db,
                UserRegister(
                    email=test_email,
                    full_name=f"Test {role}",
                    password="Password123!",
                    role=role,
                ),
            )
            self.assertEqual(user.role, role)
            self.assertTrue(user.is_active)
            if role == "ADMIN":
                self.assertTrue(user.is_superuser)
            else:
                self.assertFalse(user.is_superuser)


if __name__ == "__main__":
    unittest.main()
