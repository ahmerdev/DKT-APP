from zeep import Client
from django.conf import settings


def normalize_number(number):
    number = str(number).strip()

    if number.startswith("+"):
        number = number[1:]

    if number.startswith("0"):
        number = "92" + number[1:]

    return number


def send_sms(number, otp):
    try:
        number = normalize_number(number)

        message = f"Your OTP code is {otp}. DKT App."

        client = Client(settings.ZONG_WSDL_URL)

        request_type = client.get_type(
            "{http://schemas.datacontract.org/2004/07/CBSCustomerAPI}QuickSMSResquest"
        )

        request_obj = request_type(
            loginId=settings.ZONG_USERNAME,
            loginPassword=settings.ZONG_PASSWORD,
            Destination=number,
            Mask=settings.ZONG_MASK,
            Message=message,
            UniCode=0,
            ShortCodePrefered="n"
        )

        response = client.service.QuickSMS(request_obj)

        print("✅ SMS RESPONSE:", response)

        return response

    except Exception as e:
        print("❌ SMS ERROR:", str(e))
        return None
