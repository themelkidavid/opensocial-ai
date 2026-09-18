import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from src.auth import AuthService, AuthSession, Membership, Organisation, hash_password, normalize_email, verify_password
from src.persistence import SQLitePersistenceStore

class TestAuthFoundation(unittest.TestCase):
    def setUp(self): self.store=SQLitePersistenceStore(); self.auth=AuthService(self.store.auth)
    def tearDown(self): self.store.close()
    def test_email_password_and_public_user_safety(self):
        self.assertEqual(normalize_email(" A@Example.COM "),"a@example.com")
        with self.assertRaises(ValueError): normalize_email(" ")
        digest=hash_password("correct horse battery staple")
        self.assertNotEqual(digest,"correct horse battery staple"); self.assertTrue(verify_password("correct horse battery staple",digest)); self.assertFalse(verify_password("wrong password here",digest))
        with self.assertRaises(ValueError): hash_password("short")
        user=self.auth.create_user(" A@Example.COM ","correct horse battery staple","Alice")
        self.assertNotIn("password",user.public()); self.assertEqual(self.store.auth.get_user(user.user_id).email,"a@example.com")
        with self.assertRaises(ValueError): self.auth.create_user("a@example.com","another correct password","Other")
    def test_memberships_sessions_service_audits_and_reopen(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/"auth.sqlite3"; store=SQLitePersistenceStore(path); auth=AuthService(store.auth)
            user,organisation=auth.bootstrap("owner@example.com","correct horse battery staple","Owner","Fictional Org")
            self.assertEqual(store.auth.get_organisation(organisation.organisation_id).name,"Fictional Org")
            self.assertEqual(store.auth.list_memberships(organisation.organisation_id)[0].role,"owner")
            with self.assertRaises(ValueError): auth.bootstrap("next@example.com","another correct password","Next","Other")
            session,token=auth.create_session(user.user_id); self.assertNotEqual(session.token_hash,token); self.assertEqual(auth.resolve_session(token).user_id,user.user_id)
            self.assertIsNone(auth.authenticate("missing@example.com","correct horse battery staple")); self.assertIsNone(auth.authenticate("owner@example.com","wrong password here")); self.assertIsNotNone(auth.authenticate("owner@example.com","correct horse battery staple"))
            auth.change_password(user,"another correct password"); self.assertIsNone(auth.authenticate("owner@example.com","correct horse battery staple")); self.assertIsNotNone(auth.authenticate("owner@example.com","another correct password"))
            events=store.audit_events.list_events(); serialized=str([event.to_dict() for event in events]); self.assertNotIn("correct horse",serialized); self.assertNotIn(token,serialized); self.assertNotIn(session.token_hash,serialized)
            store.close(); reopened=SQLitePersistenceStore(path); reopened_auth=AuthService(reopened.auth); self.assertEqual(reopened.auth.get_user(user.user_id).email,"owner@example.com"); self.assertEqual(reopened_auth.resolve_session(token).user_id,user.user_id); reopened_auth.logout(session.session_id); reopened.close()
            final=SQLitePersistenceStore(path); self.assertIsNone(AuthService(final.auth).resolve_session(token)); final.close()
    def test_role_and_expiration_validation(self):
        user=self.auth.create_user("member@example.com","correct horse battery staple","Member")
        organisation=self.store.auth.create_organisation(Organisation("organisation-test","Test",None,datetime.now(timezone.utc).isoformat()))
        for index, role in enumerate(("owner","admin","member","viewer")):
            org=self.store.auth.create_organisation(Organisation(f"organisation-{index}",role,None,datetime.now(timezone.utc).isoformat()))
            self.assertEqual(self.store.auth.add_membership(Membership(org.organisation_id,user.user_id,role,datetime.now(timezone.utc).isoformat())).role,role)
        with self.assertRaises(ValueError): self.store.auth.add_membership(Membership(organisation.organisation_id,user.user_id,"invalid",datetime.now(timezone.utc).isoformat()))
        expired=AuthSession("expired",user.user_id,"expired-hash",datetime.now(timezone.utc).isoformat(),(datetime.now(timezone.utc)-timedelta(seconds=1)).isoformat()); self.store.auth.create_session(expired); self.assertIsNone(self.store.auth.resolve_session("expired-hash"))

if __name__ == "__main__": unittest.main()
