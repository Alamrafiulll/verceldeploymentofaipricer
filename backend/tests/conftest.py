import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.deps import get_db
from app.core.security import get_password_hash
from app.db.models import Customer, CustomerTier, RoleEnum, User, UserAccountStatus, UserApprovalStatus
from app.db.session import Base
from app.main import app


@pytest.fixture()
def db_session() -> Session:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)

    db = TestingSessionLocal()
    yield db
    db.close()


@pytest.fixture()
def client(db_session: Session) -> TestClient:
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture()
def seeded_users(db_session: Session) -> dict[str, User]:
    sales = User(
        name="Sales",
        email="salesmanager@gmail.com",
        password_hash=get_password_hash("123456"),
        role=RoleEnum.sales,
        approval_status=UserApprovalStatus.approved,
        account_status=UserAccountStatus.active,
    )
    approver = User(
        name="Approver",
        email="salesdirector@gmail.com",
        password_hash=get_password_hash("123456"),
        role=RoleEnum.approver,
        approval_status=UserApprovalStatus.approved,
        account_status=UserAccountStatus.active,
    )
    executive = User(
        name="Executive",
        email="executiveviewer@gmail.com",
        password_hash=get_password_hash("123456"),
        role=RoleEnum.executive,
        approval_status=UserApprovalStatus.approved,
        account_status=UserAccountStatus.active,
    )
    admin = User(
        name="Admin",
        email="admin@gmail.com",
        password_hash=get_password_hash("123456"),
        role=RoleEnum.admin,
        approval_status=UserApprovalStatus.approved,
        account_status=UserAccountStatus.active,
    )
    customer = Customer(name="Cust", tier=CustomerTier.core, region="North")

    db_session.add_all([sales, approver, executive, admin, customer])
    db_session.commit()

    return {
        "sales": sales,
        "approver": approver,
        "executive": executive,
        "admin": admin,
        "customer": customer,
    }


def login(client: TestClient, email: str, password: str) -> str:
    response = client.post("/api/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    return response.json()["access_token"]

