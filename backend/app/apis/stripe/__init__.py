import stripe
import databutton as db
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List

# Initialize Stripe
stripe.api_key = db.secrets.get("STRIPE_SECRET_KEY")

router = APIRouter(prefix="/stripe", tags=["Stripe"])

class CartItem(BaseModel):
    name: str
    price: str  # e.g., "€45,00"
    quantity: int
    imageUrl: str

class CheckoutRequest(BaseModel):
    items: List[CartItem]
    # In a real app, you'd also pass success_url and cancel_url from frontend
    # to handle different environments (dev/prod) correctly.
    # For now, we hardcode them for simplicity.
    success_url: str
    cancel_url: str


@router.post("/create-checkout-session")
def create_checkout_session(body: CheckoutRequest):
    """
    Creates a Stripe Checkout session.
    """
    try:
        line_items = []
        for item in body.items:
            # Convert price from "€XX,XX" format to cents
            price_in_eur = float(item.price.replace("€", "").replace(",", "."))
            price_in_cents = int(price_in_eur * 100)

            line_items.append({
                "price_data": {
                    "currency": "eur",
                    "product_data": {
                        "name": item.name,
                        "images": [item.imageUrl],
                    },
                    "unit_amount": price_in_cents,
                },
                "quantity": item.quantity,
            })

        checkout_session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=line_items,
            mode="payment",
            success_url=body.success_url,
            cancel_url=body.cancel_url,
        )
        return {"sessionId": checkout_session.id, "url": checkout_session.url}
    except Exception as e:
        print(f"Error creating Stripe session: {e}")
        raise HTTPException(status_code=500, detail=str(e))
