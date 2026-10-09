"""Generate a SIMULATED, messy complaint dataset (fictional companies) -> data/complaints.csv
Run: python generate_data.py
"""
import random
from datetime import date, timedelta
import pandas as pd

random.seed(7)
TODAY = date(2026, 10, 9)
STATES = ["Maharashtra", "Delhi", "Karnataka", "Rajasthan", "Gujarat", "Tamil Nadu",
          "Uttar Pradesh", "West Bengal", "Telangana", "Kerala"]
COMPANIES = {
    "QuickKart": ("E-commerce", "Online marketplace order"),
    "ShopEase": ("E-commerce", "Electronics"),
    "StreamNova": ("OTT / Subscription", "Video streaming plan"),
    "FreshBasket": ("Quick commerce", "Grocery delivery"),
    "CabGo": ("Ride hailing", "Cab booking"),
    "PayEasy": ("Fintech", "Wallet / UPI app"),
    "FitLife": ("Health & fitness", "Gym membership app"),
    "TravelNest": ("Travel", "Flight / hotel booking"),
}
TEXTS = {
    "Delayed refund": [
        "I returned the product 5 weeks ago but my refund has not been credited yet.",
        "Refund promised in 7 days, still pending after a month. Support keeps giving new dates.",
        "Order cancelled, money deducted but refund never received.",
        "Paise cut gaye lekin refund abhi tak nahi aaya, 3 weeks ho gaye.",
    ],
    "Hidden charges": [
        "Final bill had extra handling and platform fees that were not shown at checkout.",
        "I was charged a hidden convenience fee added at the last step.",
        "Surprise additional charges appeared on my invoice, the price shown earlier was lower.",
        "Checkout pe alag se extra fee laga diya, pehle nahi bataya tha.",
    ],
    "Subscription trap": [
        "My subscription auto-renewed without any reminder and the cancel option is hidden.",
        "Unable to cancel the plan, it keeps auto renewing every month.",
        "Free trial converted to paid automatically. No easy way to unsubscribe.",
        "Subscription band nahi ho raha, har mahine renew ho jata hai.",
    ],
    "Misleading advertisement": [
        "The advertisement claimed 50% off but the actual price was higher. Misleading offer.",
        "Product description said original brand, what arrived is different from advertised.",
        "Ad promised guaranteed delivery in 1 day, this was false.",
        "Advertisement mein jo dikhaya woh product alag nikla, misleading claim.",
    ],
    "Defective product": [
        "Product arrived damaged and stopped working in two days.",
        "Received a defective item, seller refuses replacement.",
        "Device is faulty and broken right out of the box.",
        "Product kharab nikla, defective piece mila aur replacement nahi de rahe.",
    ],
    "Data misuse": [
        "I started getting spam calls right after sharing my phone number with this app.",
        "My personal data was shared with third parties without my consent.",
        "App collected my contacts and location without permission, privacy violated.",
        "Mera personal data bina consent ke share kiya gaya, spam calls aa rahe hain.",
    ],
    "Other": [
        "Very bad service, nobody is responding to me.",
        "Customer care is rude and unhelpful. Please look into it.",
        "Poor experience overall, want someone senior to call me.",
    ],
}
PREFIX = ["", "", "", "Sir/Madam, ", "Very disappointed. ", "Pls help. ", "URGENT: ", "Bahut bura experience: "]
SUFFIX = ["", "", "", " Please take action.", " Kindly resolve.", " Need response asap.", " Paisa wapas chahiye."]
TYPOS = {"refund": "refnd", "charges": "chrges", "subscription": "subcription", "advertisement": "advertisment",
         "personal": "persnal", "defective": "defectve", "cancel": "cancle", "received": "recieved"}

def messy(text):
    for k, v in TYPOS.items():
        if k in text.lower() and random.random() < 0.2:
            text = text.replace(k, v).replace(k.capitalize(), v.capitalize())
    return random.choice(PREFIX) + text + random.choice(SUFFIX)

rows = []
def add(company, category, day, state=None, amount=None):
    sector, product = COMPANIES[company]
    rows.append({"date": day, "company": company, "sector": sector, "product": product,
                 "state": state or random.choice(STATES),
                 "amount_inr": amount if amount is not None else random.choice([199, 499, 799, 1299, 2499, 4999, 9999]),
                 "complaint_text": messy(random.choice(TEXTS[category])),
                 "_true_category": category})  # kept only to measure classifier accuracy

def day(a, b):
    return TODAY - timedelta(days=random.randint(a, b))

cats = list(TEXTS)
for _ in range(800):                                   # background noise
    add(random.choice(list(COMPANIES)), random.choice(cats), day(0, 364))
for _ in range(180):                                   # PLANTED: QuickKart refund spike (last 60 days)
    add("QuickKart", "Delayed refund", day(0, 60))
for _ in range(120):                                   # PLANTED: StreamNova rising subscription trap
    add("StreamNova", "Subscription trap", TODAY - timedelta(days=int(120 * random.random() ** 2)))
for _ in range(90):                                    # PLANTED: FreshBasket regional hidden charges
    add("FreshBasket", "Hidden charges", day(0, 45), state=random.choice(["Maharashtra", "Gujarat"]),
        amount=random.choice([49, 99, 149, 199]))
for _ in range(60):                                    # PLANTED: ShopEase chronic misleading ads (steady)
    add("ShopEase", "Misleading advertisement", day(0, 364))
for _ in range(45):                                    # PLANTED: PayEasy data misuse, small but severe
    add("PayEasy", "Data misuse", day(0, 40))

df = pd.DataFrame(rows).sample(frac=1, random_state=1).reset_index(drop=True)
df.insert(0, "complaint_id", [f"C{i:05d}" for i in range(1, len(df) + 1)])
df.to_csv("data/complaints.csv", index=False)
print(f"Saved data/complaints.csv with {len(df)} complaints")
