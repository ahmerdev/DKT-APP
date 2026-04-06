from zeep import Client

WSDL_URL = "http://cbs.zong.com.pk/reachcwsv2/corporatesms.svc?wsdl"
USERNAME = "923711095755"
PASSWORD = "Pa$$word786"
MASK = "DKT PAK"

def send_sms(number, message):
    try:
        if number.startswith("+"):
            number = number[1:]
        client = Client(WSDL_URL)
        request_type = client.get_type(
            "{http://schemas.datacontract.org/2004/07/CBSCustomerAPI}QuickSMSResquest"
        )
        request_obj = request_type(
            loginId=USERNAME,
            loginPassword=PASSWORD,
            Destination=number,
            Mask=MASK,
            Message=message,
            UniCode="0",
            ShortCodePrefered="n"
        )
        response = client.service.QuickSMS(request_obj)
        print("✅ SMS Response:", response)
        return response
    except Exception as e:
        print("❌ SMS Error:", e)
        return None
