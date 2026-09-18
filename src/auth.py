"""Framework-free authentication foundation; no HTTP or cookie handling."""
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import hashlib
import secrets
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, InvalidHash

_hasher = PasswordHasher()
ROLES = {"owner", "admin", "member", "viewer"}

def normalize_email(email):
    value = email.strip().casefold() if isinstance(email, str) else ""
    if "@" not in value or len(value) > 254: raise ValueError("valid email is required")
    return value
def hash_password(password):
    if not isinstance(password, str) or len(password) < 12: raise ValueError("password must be at least 12 characters")
    return _hasher.hash(password)
def verify_password(password, password_hash):
    try: return isinstance(password, str) and _hasher.verify(password_hash, password)
    except (VerifyMismatchError, InvalidHash): return False
def token_hash(token): return hashlib.sha256(token.encode("utf-8")).hexdigest()
def now(): return datetime.now(timezone.utc).isoformat()
@dataclass(frozen=True)
class User:
    user_id: str; email: str; password_hash: str; display_name: str; is_active: bool; created_at: str; last_login_at: str = None
    def public(self): return {"user_id":self.user_id,"email":self.email,"display_name":self.display_name,"is_active":self.is_active,"created_at":self.created_at,"last_login_at":self.last_login_at}
@dataclass(frozen=True)
class Organisation: organisation_id:str; name:str; description:str; created_at:str
@dataclass(frozen=True)
class Membership: organisation_id:str; user_id:str; role:str; created_at:str
@dataclass(frozen=True)
class AuthSession: session_id:str; user_id:str; token_hash:str; created_at:str; expires_at:str; revoked_at:str=None

class AuthService:
    def __init__(self, repository): self.repository=repository
    def create_user(self,email,password,display_name): return self.repository.create_user(User("user-"+secrets.token_hex(16),normalize_email(email),hash_password(password),display_name.strip(),True,now()))
    def authenticate(self,email,password):
        user=self.repository.get_user_by_email(normalize_email(email))
        if not user or not user.is_active or not verify_password(password,user.password_hash): self.repository.audit("login_failed","authentication","login","Authentication failed.",{}); return None
        self.repository.update_login(user.user_id); self.repository.audit("login_succeeded","user",user.user_id,"User authenticated.",{}); return user
    def create_session(self,user_id,hours=24):
        token=secrets.token_urlsafe(32); session=AuthSession("session-"+secrets.token_hex(16),user_id,token_hash(token),now(),(datetime.now(timezone.utc)+timedelta(hours=hours)).isoformat()); self.repository.create_session(session); return session,token
    def resolve_session(self,token): return self.repository.resolve_session(token_hash(token))
    def logout(self,session_id): self.repository.revoke_session(session_id); self.repository.audit("logout","session",session_id,"Session was revoked.",{})
    def change_password(self,user,password): self.repository.update_password(user.user_id,hash_password(password)); self.repository.audit("password_changed","user",user.user_id,"Password was changed.",{})
    def bootstrap(self,email,password,display_name,organisation_name):
        if self.repository.has_owner(): raise ValueError("bootstrap owner already exists")
        user=self.create_user(email,password,display_name); organisation=self.repository.create_organisation(Organisation("organisation-"+secrets.token_hex(16),organisation_name,"Bootstrap organisation",now())); self.repository.add_membership(Membership(organisation.organisation_id,user.user_id,"owner",now())); return user,organisation
