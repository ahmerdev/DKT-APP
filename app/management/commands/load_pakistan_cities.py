from django.core.management.base import BaseCommand
import requests
from app.models import City


class Command(BaseCommand):
    help = "Load Pakistan cities from GitHub JSON"

    def handle(self, *args, **kwargs):

        url = "https://gist.githubusercontent.com/ahmedali5530/a4f090da89989ca9e0ca04e202036c48/raw/ae6c77c2a83b15681f07431fc58b50d0563d4b47/pakistan_cities.json"

        response = requests.get(url)
        cities = response.json()

        count = 0

        for city in cities:
            obj, created = City.objects.get_or_create(name=city.strip())

            if created:
                count += 1

        self.stdout.write(self.style.SUCCESS(
            f"{count} Pakistan cities loaded successfully!"
        ))
