from datetime import datetime, timezone
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db.models import Contract, ContractStatus, Product, Quote


def _is_active(as_of: datetime, effective_start: datetime | None, effective_end: datetime | None) -> bool:
    start = effective_start
    end = effective_end
    if start and start.tzinfo is None:
        start = start.replace(tzinfo=timezone.utc)
    if end and end.tzinfo is None:
        end = end.replace(tzinfo=timezone.utc)
    if start and as_of < start:
        return False
    if end and as_of > end:
        return False
    return True


def resolve_applicable_contracts(
    db: Session,
    customer_id: str,
    as_of: datetime | None = None,
) -> list[Contract]:
    try:
        customer_uuid = uuid.UUID(customer_id)
    except ValueError:
        return []
    check_time = as_of or datetime.now(timezone.utc)
    contracts = list(
        db.scalars(
            select(Contract)
            .where(Contract.customer_id == customer_uuid, Contract.status == ContractStatus.active)
            .options(selectinload(Contract.lines))
        ).all()
    )
    return [contract for contract in contracts if _is_active(check_time, contract.effective_start, contract.effective_end)]


def apply_contract_pricing(
    contracts: list[Contract],
    product_id: str,
) -> dict | None:
    matched_lines = []
    for contract in contracts:
        for line in contract.lines:
            if str(line.product_id) == str(product_id):
                matched_lines.append(line)

    if not matched_lines:
        return None

    floor_price = max(float(line.floor_price) for line in matched_lines)
    ceiling_price = min(float(line.ceiling_price) for line in matched_lines)
    discount_caps = [float(line.discount_cap_percent) for line in matched_lines if line.discount_cap_percent is not None]
    discount_cap_percent = min(discount_caps) if discount_caps else None

    return {
        "floor_price": floor_price,
        "ceiling_price": ceiling_price,
        "discount_cap_percent": discount_cap_percent,
    }


def evaluate_contract_pricing(
    db: Session,
    quote: Quote,
    price_override: float | None = None,
    as_of: datetime | None = None,
) -> dict:
    check_time = as_of or datetime.now(timezone.utc)
    item = quote.items[0]
    product = item.product or db.get(Product, item.product_id)
    if product is None:
        return {
            "status": "product_missing",
            "active_contract_count": 0,
            "matched_contract_count": 0,
            "contract_ids": [],
            "contract_names": [],
            "source_document_ids": [],
            "source_uploaded_file_ids": [],
            "source_references": [],
            "evaluated_price": None,
            "discount_percent": None,
            "floor_price": None,
            "ceiling_price": None,
            "discount_cap_percent": None,
            "message": "Product details are not available for contract validation.",
            "next_action": "Reload the quote before reviewing customer-specific contract pricing rules.",
        }

    evaluated_price = float(
        price_override
        or item.final_price
        or item.requested_price
        or item.recommended_price
        or product.list_price
    )
    contracts = resolve_applicable_contracts(db=db, customer_id=str(quote.customer_id), as_of=check_time)
    if not contracts:
        return {
            "status": "no_contract",
            "active_contract_count": 0,
            "matched_contract_count": 0,
            "contract_ids": [],
            "contract_names": [],
            "source_document_ids": [],
            "source_uploaded_file_ids": [],
            "source_references": [],
            "evaluated_price": evaluated_price,
            "discount_percent": round(((float(product.list_price) - evaluated_price) / float(product.list_price)) * 100, 2)
            if float(product.list_price) > 0
            else None,
            "floor_price": None,
            "ceiling_price": None,
            "discount_cap_percent": None,
            "message": "No active customer-specific contract pricing rule applies to this customer.",
            "next_action": "Proceed with standard pricebook and policy checks unless a contract needs to be uploaded.",
        }

    matched_contracts: list[tuple[Contract, list]] = []
    for contract in contracts:
        lines = [line for line in contract.lines if str(line.product_id) == str(product.id)]
        if lines:
            matched_contracts.append((contract, lines))

    if not matched_contracts:
        return {
            "status": "product_not_covered",
            "active_contract_count": len(contracts),
            "matched_contract_count": 0,
            "contract_ids": [str(contract.id) for contract in contracts],
            "contract_names": [contract.name for contract in contracts],
            "source_document_ids": [
                str(contract.source_document_id) for contract in contracts if contract.source_document_id
            ],
            "source_uploaded_file_ids": [
                str(contract.source_uploaded_file_id) for contract in contracts if contract.source_uploaded_file_id
            ],
            "source_references": [contract.contract_source_reference for contract in contracts],
            "evaluated_price": evaluated_price,
            "discount_percent": round(((float(product.list_price) - evaluated_price) / float(product.list_price)) * 100, 2)
            if float(product.list_price) > 0
            else None,
            "floor_price": None,
            "ceiling_price": None,
            "discount_cap_percent": None,
            "message": "This customer has an active contract, but the current product is not covered by a contract line.",
            "next_action": "Use standard pricing controls or upload a contract addendum for this product if required.",
        }

    matched_lines = [line for _, lines in matched_contracts for line in lines]
    floor_price = max(float(line.floor_price) for line in matched_lines)
    ceiling_price = min(float(line.ceiling_price) for line in matched_lines)
    discount_caps = [float(line.discount_cap_percent) for line in matched_lines if line.discount_cap_percent is not None]
    discount_cap_percent = min(discount_caps) if discount_caps else None
    discount_percent = (
        round(((float(product.list_price) - evaluated_price) / float(product.list_price)) * 100, 2)
        if float(product.list_price) > 0
        else None
    )

    if floor_price > ceiling_price:
        status = "conflicting_contract_bounds"
        message = "Active contract lines contain conflicting floor and ceiling values for this product."
        next_action = "Review the overlapping contract documents before approving or finalizing this quote."
    elif evaluated_price < floor_price:
        status = "below_contract_floor"
        message = f"Quoted price RM {evaluated_price:.2f} is below the customer contract floor of RM {floor_price:.2f}."
        next_action = "Raise the price to the contract floor or request an exception approval."
    elif evaluated_price > ceiling_price:
        status = "above_contract_ceiling"
        message = f"Quoted price RM {evaluated_price:.2f} is above the customer contract ceiling of RM {ceiling_price:.2f}."
        next_action = "Confirm the contract terms with the customer before proceeding."
    elif discount_cap_percent is not None and discount_percent is not None and discount_percent > discount_cap_percent:
        status = "exceeds_contract_discount_cap"
        message = (
            f"Quote discount of {discount_percent:.2f}% exceeds the contract discount cap of "
            f"{discount_cap_percent:.2f}%."
        )
        next_action = "Keep the discount within the agreed cap or obtain formal approval to override the contract."
    else:
        status = "within_contract_bounds"
        message = "Quoted price is within the active customer-specific contract pricing boundaries."
        next_action = "Use the contract source reference in the approval or negotiation discussion if needed."

    matched_contract_list = [contract for contract, _ in matched_contracts]
    return {
        "status": status,
        "active_contract_count": len(contracts),
        "matched_contract_count": len(matched_contract_list),
        "contract_ids": [str(contract.id) for contract in matched_contract_list],
        "contract_names": [contract.name for contract in matched_contract_list],
        "source_document_ids": [
            str(contract.source_document_id) for contract in matched_contract_list if contract.source_document_id
        ],
        "source_uploaded_file_ids": [
            str(contract.source_uploaded_file_id) for contract in matched_contract_list if contract.source_uploaded_file_id
        ],
        "source_references": [contract.contract_source_reference for contract in matched_contract_list],
        "evaluated_price": evaluated_price,
        "discount_percent": discount_percent,
        "floor_price": floor_price,
        "ceiling_price": ceiling_price,
        "discount_cap_percent": discount_cap_percent,
        "message": message,
        "next_action": next_action,
    }
