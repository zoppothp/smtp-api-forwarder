from fastapi import FastAPI, Request, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

app = FastAPI()

API_KEY = os.getenv("API_KEY")


# Only allow CORS for www.zoppoth.at
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://www.zoppoth.at", "https://zoppoth.at"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class PriceCalculation(BaseModel):
    nights: int
    pricePerNight: float
    touristTax: float
    adultsCount: int
    cleaningFee: float
    totalPrice: float

class BookingRequest(BaseModel):
    name: str
    email: str
    phone: str = None
    arrival: str
    departure: str
    guests: int
    apartmentType: str
    message: str = None
    priceCalculation: PriceCalculation = None

@app.post("/send-email")
async def send_email(
    booking: BookingRequest,
    request: Request,
    referer: str = Header(None),
    origin: str = Header(None),
    x_api_key: str = Header(None)
):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    allowed_domain = "www.zoppoth.at"
    referer_ok = referer and allowed_domain in referer
    origin_ok = origin and (origin == f"https://{allowed_domain}" or origin == f"http://{allowed_domain}")

    if not referer_ok and not origin_ok:
        raise HTTPException(status_code=403, detail="Forbidden: Request not from allowed domain.")

    arrival_date = datetime.strptime(booking.arrival, "%Y-%m-%d")
    departure_date = datetime.strptime(booking.departure, "%Y-%m-%d")

    price_details = ""
    if booking.priceCalculation:
        pc = booking.priceCalculation
        price_details = f"""
      --- Preisinformationen ---
      Nächte: {pc.nights}
      Preis pro Nacht: €{pc.pricePerNight},-
      Ortstaxe (€{pc.touristTax} für {pc.adultsCount} Erwachsene, {pc.nights} Nächte)
      Reinigungsgebühr: €{pc.cleaningFee},-
      Gesamtpreis: €{pc.totalPrice},-
      """

    mail_content = f"""
      Name: {booking.name}
      Email: {booking.email}
      {"Telefon: " + booking.phone if booking.phone else ""}
      Anreisedatum: {arrival_date.strftime("%d. %B %Y")}
      Abreisedatum: {departure_date.strftime("%d. %B %Y")}
      Gäste: {booking.guests}
      Apartment: {booking.apartmentType}
      {"Nachricht: " + booking.message if booking.message else ""}
      {price_details}
      """

    msg = MIMEMultipart()
    msg["From"] = booking.email
    msg["To"] = "buchungen@zoppoth.at"
    msg["Subject"] = f"Neue Buchungsanfrage von {booking.name}"
    msg.attach(MIMEText(mail_content, "plain"))

    try:
        with smtplib.SMTP_SSL("mx151a.netcup.net", 465) as server:
            server.login(os.getenv("SMTP_USER"), os.getenv("SMTP_PASSWORD"))
            server.sendmail(booking.email, "buchungen@zoppoth.at", msg.as_string())
        return {"status": "Email sent successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error sending email: {str(e)}")

@app.get("/")
def read_root():
    return {"status": "OK"}
