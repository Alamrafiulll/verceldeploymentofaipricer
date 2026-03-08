from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db.models import PriceBook, PriceBookChannel, Quote


CHANNEL_LABELS: dict[PriceBookChannel, str] = {
    PriceBookChannel.lsp: "LSP",
    PriceBookChannel.wm: "WM",
    PriceBookChannel.em: "EM",
}


def _normalize_datetime(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


def is_effective(
    now: datetime,
    effective_start: datetime | None,
    effective_end: datetime | None,
) -> bool:
    start = _normalize_datetime(effective_start)
    end = _normalize_datetime(effective_end)
    if start and now < start:
        return False
    if end and now > end:
        return False
    return True


def map_quote_channel_to_pricebook_channel(channel: str) -> PriceBookChannel | None:
    normalized = channel.strip().lower()
    mapping = {
        "lsp": PriceBookChannel.lsp,
        "wm": PriceBookChannel.wm,
        "em": PriceBookChannel.em,
        "direct": PriceBookChannel.lsp,
        "distributor": PriceBookChannel.wm,
        "project": PriceBookChannel.em,
    }
    return mapping.get(normalized)


def _serialize_datetime(value: datetime | None) -> str | None:
    normalized = _normalize_datetime(value)
    return normalized.isoformat() if normalized else None


def _build_effective_window_message(book: PriceBook | None, now: datetime) -> tuple[str, str]:
    if book is None:
        return (
            "No active pricebook is available for this sales channel.",
            "Upload or activate a pricebook for the required channel before finalizing the quote.",
        )

    start = _normalize_datetime(book.effective_start)
    end = _normalize_datetime(book.effective_end)
    if start and now < start:
        return (
            f"Pricebook {book.name} is configured but starts on {start.date().isoformat()}.",
            "Use the current active pricebook or update the effective dates before quoting.",
        )
    if end and now > end:
        return (
            f"Pricebook {book.name} expired on {end.date().isoformat()}.",
            "Upload or activate a current pricebook for this channel before quoting.",
        )
    return (
        f"Pricebook {book.name} is active for this channel.",
        "Use the active channel reference price when reviewing the quote.",
    )


def evaluate_pricebook_compliance(
    db: Session,
    quote: Quote,
    price_override: float | None = None,
) -> dict:
    now = datetime.now(timezone.utc)
    item = quote.items[0]
    product = item.product
    evaluated_price = (
        float(price_override)
        if price_override is not None
        else float(item.final_price or item.requested_price or item.recommended_price or product.list_price)
    )

    channel = map_quote_channel_to_pricebook_channel(quote.channel)
    if channel is None:
        return {
            "reference_channel": None,
            "reference_label": None,
            "status": "channel_unmapped",
            "matched_pricebook_id": None,
            "matched_pricebook_name": None,
            "effective_start": None,
            "effective_end": None,
            "reference_price": None,
            "evaluated_price": evaluated_price,
            "price_gap_amount": None,
            "price_gap_percent": None,
            "source_document_id": None,
            "message": f"Quote channel '{quote.channel}' is not mapped to an LSP, WM, or EM reference.",
            "next_action": "Map the quote channel to an approved pricebook channel before finalizing the quote.",
        }

    books = list(
        db.scalars(
            select(PriceBook)
            .where(PriceBook.channel == channel)
            .options(selectinload(PriceBook.items))
            .order_by(PriceBook.effective_start.desc(), PriceBook.created_at.desc())
        ).all()
    )
    active_books = [book for book in books if is_effective(now, book.effective_start, book.effective_end)]
    fallback_book = books[0] if books else None

    if not active_books:
        message, next_action = _build_effective_window_message(fallback_book, now)
        return {
            "reference_channel": channel.value,
            "reference_label": CHANNEL_LABELS[channel],
            "status": "no_active_pricebook",
            "matched_pricebook_id": str(fallback_book.id) if fallback_book else None,
            "matched_pricebook_name": fallback_book.name if fallback_book else None,
            "effective_start": _serialize_datetime(fallback_book.effective_start if fallback_book else None),
            "effective_end": _serialize_datetime(fallback_book.effective_end if fallback_book else None),
            "reference_price": None,
            "evaluated_price": evaluated_price,
            "price_gap_amount": None,
            "price_gap_percent": None,
            "source_document_id": str(fallback_book.source_document_id) if fallback_book and fallback_book.source_document_id else None,
            "message": message,
            "next_action": next_action,
        }

    active_book = active_books[0]
    matched_item = next((pricebook_item for pricebook_item in active_book.items if pricebook_item.product_id == product.id), None)
    if matched_item is None:
        return {
            "reference_channel": channel.value,
            "reference_label": CHANNEL_LABELS[channel],
            "status": "product_missing",
            "matched_pricebook_id": str(active_book.id),
            "matched_pricebook_name": active_book.name,
            "effective_start": _serialize_datetime(active_book.effective_start),
            "effective_end": _serialize_datetime(active_book.effective_end),
            "reference_price": None,
            "evaluated_price": evaluated_price,
            "price_gap_amount": None,
            "price_gap_percent": None,
            "source_document_id": str(active_book.source_document_id) if active_book.source_document_id else None,
            "message": f"Product {product.sku} is not present in the active {CHANNEL_LABELS[channel]} pricebook.",
            "next_action": "Update the active pricebook or use a product that has a channel reference price.",
        }

    reference_price = float(matched_item.list_price)
    gap_amount = round(evaluated_price - reference_price, 2)
    gap_percent = round((gap_amount / reference_price) * 100, 2) if reference_price else None

    if evaluated_price < reference_price:
        status = "below_reference_price"
        message = (
            f"Quoted price RM {evaluated_price:.2f} is below the {CHANNEL_LABELS[channel]} reference price "
            f"RM {reference_price:.2f}."
        )
        next_action = "Raise the quoted price to the reference level or request approval."
    elif evaluated_price > reference_price:
        status = "premium_to_reference"
        message = (
            f"Quoted price RM {evaluated_price:.2f} is above the {CHANNEL_LABELS[channel]} reference price "
            f"RM {reference_price:.2f}."
        )
        next_action = "Confirm the premium positioning with the customer and keep the reference justification ready."
    else:
        status = "within_reference_price"
        message = (
            f"Quoted price matches the active {CHANNEL_LABELS[channel]} reference price "
            f"of RM {reference_price:.2f}."
        )
        next_action = "You can proceed with the current reference price position."

    return {
        "reference_channel": channel.value,
        "reference_label": CHANNEL_LABELS[channel],
        "status": status,
        "matched_pricebook_id": str(active_book.id),
        "matched_pricebook_name": active_book.name,
        "effective_start": _serialize_datetime(active_book.effective_start),
        "effective_end": _serialize_datetime(active_book.effective_end),
        "reference_price": reference_price,
        "evaluated_price": evaluated_price,
        "price_gap_amount": gap_amount,
        "price_gap_percent": gap_percent,
        "source_document_id": str(active_book.source_document_id) if active_book.source_document_id else None,
        "message": message,
        "next_action": next_action,
    }
