// Lifetime Premium price in naira. Mirrors PREMIUM_LIFETIME_PRICE_KOBO in
// backend/app/core/config.py (the backend amount is what Paystack actually charges).
export const PREMIUM_LIFETIME_PRICE_NAIRA = 3000;
export const PREMIUM_LIFETIME_PRICE_LABEL = `₦${PREMIUM_LIFETIME_PRICE_NAIRA.toLocaleString("en-NG")}`;
