from __future__ import annotations

import re
import uuid
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db.models import Contract, ContractLine, ContractStatus, Customer, PolicyDocument, Product, UploadedFile, User
from app.services.audit_logger import log_audit


@dataclass
class ParsedContractLine:
    product_id: uuid.UUID
    floor_price: float
    ceiling_price: float
    discount_cap_percent: float | None


def _parse_uuid(value: str | None, field_name: str) -> uuid.UUID | None:
    if not value:
        return None
    try:
        return uuid.UUID(value)
    except ValueError as exc:
        raise ValueError(f"Invalid {field_name}") from exc


def _validate_effective_window(effective_start: datetime | None, effective_end: datetime | None) -> None:
    if effective_start and effective_end and effective_end <= effective_start:
        raise ValueError("effective_end must be later than effective_start")


def _resolve_product(
    db: Session,
    product_id: str | None = None,
    sku: str | None = None,
) -> Product:
    if product_id:
        parsed_product_id = _parse_uuid(product_id, "product_id")
        product = db.get(Product, parsed_product_id)
        if product is None:
            raise ValueError(f"Product not found for id: {product_id}")
        return product
    if sku:
        product = db.scalar(select(Product).where(Product.sku == sku.strip().upper()))
        if product is None:
            raise ValueError(f"SKU not found in contract upload: {sku}")
        return product
    raise ValueError("Each contract line requires product_id or sku")


def parse_contract_lines_from_text(
    db: Session,
    text: str,
) -> list[ParsedContractLine]:
    parsed_lines: list[ParsedContractLine] = []
    seen_product_ids: set[uuid.UUID] = set()
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        sku_match = re.search(r"\b[A-Z0-9]+(?:-[A-Z0-9]+)+\b", line.upper())
        if not sku_match:
            continue
        numeric_values = re.findall(r"(\d+(?:\.\d+)?)", line)
        if len(numeric_values) < 2:
            continue
        product = _resolve_product(db=db, sku=sku_match.group(0))
        if product.id in seen_product_ids:
            raise ValueError(f"Duplicate SKU in contract upload: {product.sku}")
        seen_product_ids.add(product.id)
        floor_price = float(numeric_values[0])
        ceiling_price = float(numeric_values[1])
        discount_cap_percent = float(numeric_values[2]) if len(numeric_values) >= 3 else None
        if floor_price > ceiling_price:
            raise ValueError(f"Contract floor price cannot exceed ceiling price for SKU {product.sku}")
        parsed_lines.append(
            ParsedContractLine(
                product_id=product.id,
                floor_price=floor_price,
                ceiling_price=ceiling_price,
                discount_cap_percent=discount_cap_percent,
            )
        )

    if not parsed_lines:
        raise ValueError("Contract upload did not contain any readable product pricing lines")
    return parsed_lines


def create_contract(
    db: Session,
    *,
    customer_id: str,
    name: str,
    status: ContractStatus,
    effective_start: datetime | None,
    effective_end: datetime | None,
    source_document_id: str | None,
    source_uploaded_file_id: str | None,
    line_payloads: list[dict],
    actor_user_id: str,
) -> Contract:
    customer_uuid = _parse_uuid(customer_id, "customer_id")
    customer = db.get(Customer, customer_uuid)
    if customer is None:
        raise ValueError("Customer not found")

    parsed_source_document_id = _parse_uuid(source_document_id, "source_document_id")
    if parsed_source_document_id:
        policy_document = db.get(PolicyDocument, parsed_source_document_id)
        if policy_document is None:
            raise ValueError("Source policy document not found")

    parsed_source_uploaded_file_id = _parse_uuid(source_uploaded_file_id, "source_uploaded_file_id")
    uploaded_file = None
    if parsed_source_uploaded_file_id:
        uploaded_file = db.get(UploadedFile, parsed_source_uploaded_file_id)
        if uploaded_file is None:
            raise ValueError("Source uploaded file not found")

    _validate_effective_window(effective_start, effective_end)
    if not line_payloads:
        raise ValueError("Contract must include at least one product line")

    parsed_lines: list[ParsedContractLine] = []
    seen_product_ids: set[uuid.UUID] = set()
    for line_payload in line_payloads:
        product = _resolve_product(
            db=db,
            product_id=line_payload.get("product_id"),
            sku=line_payload.get("sku"),
        )
        if product.id in seen_product_ids:
            raise ValueError(f"Duplicate product in contract lines: {product.sku}")
        floor_price = float(line_payload["floor_price"])
        ceiling_price = float(line_payload["ceiling_price"])
        discount_cap_percent = (
            float(line_payload["discount_cap_percent"])
            if line_payload.get("discount_cap_percent") is not None
            else None
        )
        if floor_price > ceiling_price:
            raise ValueError(f"Contract floor price cannot exceed ceiling price for SKU {product.sku}")
        seen_product_ids.add(product.id)
        parsed_lines.append(
            ParsedContractLine(
                product_id=product.id,
                floor_price=floor_price,
                ceiling_price=ceiling_price,
                discount_cap_percent=discount_cap_percent,
            )
        )

    contract = Contract(
        customer_id=customer.id,
        name=name.strip(),
        status=status,
        effective_start=effective_start,
        effective_end=effective_end,
        source_document_id=parsed_source_document_id,
        source_uploaded_file_id=parsed_source_uploaded_file_id,
    )
    db.add(contract)
    db.flush()

    for line in parsed_lines:
        db.add(
            ContractLine(
                contract_id=contract.id,
                product_id=line.product_id,
                floor_price=line.floor_price,
                ceiling_price=line.ceiling_price,
                discount_cap_percent=line.discount_cap_percent,
            )
        )

    if uploaded_file:
        uploaded_file.linked_contract_id = contract.id

    log_audit(
        db=db,
        actor_user_id=actor_user_id,
        action="contract_created",
        entity_type="contract",
        entity_id=str(contract.id),
        new_json={
            "customer_id": customer_id,
            "name": contract.name,
            "line_count": len(parsed_lines),
        },
    )
    db.commit()
    return db.scalar(
        select(Contract)
        .where(Contract.id == contract.id)
        .options(selectinload(Contract.lines), selectinload(Contract.customer))
    )
