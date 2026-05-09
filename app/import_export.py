# yourapp/import_export.py
import pandas as pd
from django.contrib.auth.hashers import make_password
from .models import Rider, City

def import_riders_from_excel(excel_file):
    df = pd.read_excel(excel_file)
    
    success_count = 0
    errors = []

    for index, row in df.iterrows():
        try:
            email = str(row["email"]).strip()
            
            if Rider.objects.filter(email=email).exists():
                errors.append(f"Row {index+2}: {email} already exists")
                continue

            rider = Rider(
                name=str(row["name"]).strip(),
                phone=str(row["phone"]).strip(),
                email=email,
                password=str(row["password"]).strip(),  
                designation=str(row.get("designation", "Delivery Rider")).strip(),
                is_active=True,
            )
            rider.save()

            # Cities handle
            if "cities" in row and pd.notna(row["cities"]):
                city_names = [c.strip() for c in str(row["cities"]).split(",")]
                for city_name in city_names:
                    city = City.objects.filter(name__iexact=city_name).first()
                    if city:
                        rider.cities.add(city)

            success_count += 1

        except Exception as e:
            errors.append(f"Row {index+2}: {str(e)}")

    return success_count, errors
