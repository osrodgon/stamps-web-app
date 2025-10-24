import itertools
from tkinter import ALL
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from faker import Faker
from faker.providers.color.en_US import Provider as ColorProvider
import random

from colors_api.models import Color
from condition_types_api.models import ConditionType
from config_api.models import Config
from countries_api.models import Country

NUM_ENTRIES = 5

ALL_COLORS = [color.capitalize() for color in ColorProvider.safe_colors]

CONDITION_TERMS = [
    'Mint (Sealed)',
    'Like New (Open Box)',
    'Excellent',
    'Good',
    'Used (Visible Wear)',
    'Fair (Needs Repair)',
    'For Parts Only'
]

class Command(BaseCommand):
    help = f'Seeds the database with fake entries.'

    def handle(self, *args, **options):
        fake = Faker()
        
        self.stdout.write(self.style.WARNING('Starting loading database with fake data...'))
        
        self.stdout.write("Creating colors...")
        color_list = list(itertools.islice(itertools.cycle(ALL_COLORS), NUM_ENTRIES))
        random.shuffle(color_list)
        color_iterator = iter(color_list)
        for _ in range(NUM_ENTRIES):
            Color.objects.create(name=next(color_iterator))
            
        self.stdout.write("Creating condition types...")
        condition_list = list(itertools.islice(itertools.cycle(CONDITION_TERMS), NUM_ENTRIES))
        random.shuffle(condition_list)
        condition_iterator = iter(condition_list)
        for _ in range(NUM_ENTRIES):
            ConditionType.objects.create(name=next(condition_iterator))
            
        self.stdout.write("Creating countries...")
        for _ in range(NUM_ENTRIES):
            Country.objects.create(name=fake.country())
            
        self.stdout.write("Creating config...")
        for _ in range(NUM_ENTRIES):
            Config.objects.create(
                property=fake.user_name(),
                value=fake.user_name()
            )
            
        self.stdout.write(self.style.SUCCESS('\nDatabase load with fake data completed. 🌱'))