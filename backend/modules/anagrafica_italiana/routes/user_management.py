"""
User Management API for Anagrafica module.

Endpoints to create and manage user accounts linked to soggetti anagrafici.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import Optional, List
import secrets
import string

from app.core.database import get_db
from app.core.auth.dependencies import get_current_user, require_permission
from app.core.auth.models import User, Role
from app.core.auth.security import get_password_hash

# Import anagrafica models
import sys, os
modules_dir = os.path.join(os.path.dirname(__file__), '../../../modules')
if modules_dir not in sys.path:
    sys.path.insert(0, modules_dir)

from anagrafica_italiana.models import SoggettoAnagrafico, TipoSoggetto

router = APIRouter(prefix="/soggetti", tags=["anagrafica-user-management"])


# Schemas
class CreateUserRequest(BaseModel):
    email: Optional[EmailStr] = None  # If None, use soggetto email
    username: Optional[str] = None    # If None, auto-generate from nome/cognome
    password: Optional[str] = None    # If None, generate temporary
    send_welcome_email: bool = False
    roles: List[str] = []             # Role names to assign


class UserInfoResponse(BaseModel):
    has_user: bool
    user: Optional[dict] = None


def generate_username(nome: str, cognome: str, db: Session) -> str:
    """Generate unique username from nome and cognome."""
    # Normalize: lowercase, remove accents, replace spaces with dots
    import unicodedata
    
    def normalize(s):
        s = s.lower().strip()
        s = unicodedata.normalize('NFKD', s).encode('ASCII', 'ignore').decode('ASCII')
        s = s.replace(' ', '.')
        return s
    
    base_username = f"{normalize(nome)}.{normalize(cognome)}"
    username = base_username
    counter = 1
    
    # Ensure uniqueness
    while db.query(User).filter(User.username == username).first():
        username = f"{base_username}{counter}"
        counter += 1
    
    return username


def generate_temp_password(length=12) -> str:
    """Generate a secure temporary password."""
    alphabet = string.ascii_letters + string.digits + "!@#$%&"
    return ''.join(secrets.choice(alphabet) for _ in range(length))


@router.post("/{soggetto_id}/create-user")
def create_user_from_soggetto(
    soggetto_id: int,
    request: CreateUserRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("soggetto.create_user"))
):
    """
    Create a user account linked to a soggetto anagrafico.
    
    Requirements:
    - Soggetto must be PERSONA_FISICA
    - Soggetto must have email (or provide one in request)
    - Soggetto cannot already have a user account
    """
    # Get soggetto
    soggetto = db.query(SoggettoAnagrafico).filter(
        SoggettoAnagrafico.id == soggetto_id
    ).first()
    
    if not soggetto:
        raise HTTPException(status_code=404, detail="Soggetto not found")
    
    # Validation: only PERSONA_FISICA can have accounts
    if soggetto.tipo_soggetto != TipoSoggetto.PERSONA_FISICA:
        raise HTTPException(
            status_code=400,
            detail="Only PERSONA_FISICA can have user accounts. Persone giuridiche cannot login."
        )
    
    # Check if user already exists
    existing_user = db.query(User).filter(
        User.soggetto_anagrafico_id == soggetto_id
    ).first()
    
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail=f"User account already exists for this soggetto (username: {existing_user.username})"
        )
    
    # Get or validate email
    email = request.email or soggetto.email
    if not email:
        raise HTTPException(
            status_code=400,
            detail="Email required. Either provide in request or update soggetto email first."
        )
    
    # Check email uniqueness
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(
            status_code=400,
            detail=f"Email {email} is already in use by another user"
        )
    
    # Generate username if not provided
    username = request.username
    if not username:
        if not soggetto.nome or not soggetto.cognome:
            raise HTTPException(
                status_code=400,
                detail="Cannot auto-generate username: soggetto missing nome or cognome. Provide username explicitly."
            )
        username = generate_username(soggetto.nome, soggetto.cognome, db)
    
    # Check username uniqueness
    if db.query(User).filter(User.username == username).first():
        raise HTTPException(
            status_code=400,
            detail=f"Username {username} is already taken"
        )
    
    # Generate password if not provided
    password = request.password or generate_temp_password()
    temporary_password = request.password is None
    
    # Create user
    new_user = User(
        email=email,
        username=username,
        hashed_password=get_password_hash(password),
        full_name=f"{soggetto.nome} {soggetto.cognome}" if soggetto.nome and soggetto.cognome else None,
        phone=soggetto.telefono,
        soggetto_anagrafico_id=soggetto_id,
        is_active=True,
        is_superuser=False
    )
    
    db.add(new_user)
    db.flush()  # Get user ID
    
    # Assign roles
    if request.roles:
        for role_name in request.roles:
            role = db.query(Role).filter(Role.name == role_name).first()
            if role:
                new_user.roles.append(role)
            else:
                raise HTTPException(
                    status_code=400,
                    detail=f"Role '{role_name}' not found"
                )
    
    db.commit()
    db.refresh(new_user)
    
    # TODO: Send welcome email if requested
    # if request.send_welcome_email:
    #     send_welcome_email(email, username, password)
    
    return {
        "user_id": new_user.id,
        "soggetto_id": soggetto_id,
        "email": email,
        "username": username,
        "temporary_password": temporary_password,
        "password": password if temporary_password else None,  # Only return if auto-generated
        "roles": [r.name for r in new_user.roles],
        "message": "User created successfully." + 
                   (" Email sent with credentials." if request.send_welcome_email else "")
    }


@router.get("/{soggetto_id}/user", response_model=UserInfoResponse)
def get_soggetto_user_info(
    soggetto_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("soggetto.view"))
):
    """
    Get user account information for a soggetto anagrafico.
    """
    # Verify soggetto exists
    soggetto = db.query(SoggettoAnagrafico).filter(
        SoggettoAnagrafico.id == soggetto_id
    ).first()
    
    if not soggetto:
        raise HTTPException(status_code=404, detail="Soggetto not found")
    
    # Find linked user
    user = db.query(User).filter(
        User.soggetto_anagrafico_id == soggetto_id
    ).first()
    
    if not user:
        return {"has_user": False, "user": None}
    
    return {
        "has_user": True,
        "user": {
            "id": user.id,
            "email": user.email,
            "username": user.username,
            "full_name": user.full_name,
            "phone": user.phone,
            "is_active": user.is_active,
            "is_superuser": user.is_superuser,
            "roles": [{"id": r.id, "name": r.name, "description": r.description} for r in user.roles],
            "last_login": user.last_login.isoformat() if user.last_login else None,
            "created_at": user.created_at.isoformat() if user.created_at else None
        }
    }


@router.delete("/{soggetto_id}/user")
def disable_soggetto_user(
    soggetto_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("soggetto.disable_user"))
):
    """
    Disable user account for a soggetto (sets is_active=False).
    Does not delete the user or soggetto.
    """
    user = db.query(User).filter(
        User.soggetto_anagrafico_id == soggetto_id
    ).first()
    
    if not user:
        raise HTTPException(
            status_code=404,
            detail="No user account found for this soggetto"
        )
    
    user.is_active = False
    db.commit()
    
    return {
        "message": f"User '{user.username}' disabled successfully",
        "user_id": user.id,
        "username": user.username
    }
