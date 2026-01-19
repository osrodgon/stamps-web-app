import os
import re
from datetime import datetime

import pandas as pd
from colors_api.models import Color
from countries_api.models import Country
from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import transaction
from issues_api.models import Issue
from print_types_api.models import PrintType
from stamp_types_api.models import StampType
from stamps_api.models import Stamp
from years_api.models import Year


class Command(BaseCommand):
    help = 'Imports data from csv file.'
    
    def clean_and_get_colors(self,color_string):
        if pd.isna(color_string) or str(color_string).strip() == "":
            return []
        
        colors_names = [c.strip() for c in str(color_string).split('|')]
        
        color_objects = []
        for name in colors_names:
            final_name = name.strip(' ').strip(',')
            final_name = self.clean_string(final_name).title()
            if final_name and final_name.lower() != 'nan': 
                color_obj, _ = Color.objects.get_or_create(name=final_name)
                color_objects.append(color_obj)
        
        return color_objects
    
    def clean_number(self, value):
        if pd.isna(value) or str(value).strip() == "":
            return None
        
        value_str = str(value).replace('.', '').strip()
        
        try:
            return int(value_str)
        except ValueError:
            try:
                return float(value_str.replace(',', '.'))
            except ValueError:
                return None
            
    def clean_date(self, value):
        if pd.isna(value) or str(value).strip() == "":
            return None
    
        date_str = str(value).strip()
        
        if len(date_str) == 4 and date_str.isdigit():
            return f"{date_str}-01-01"
        
        for formato in ["%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d", "%Y/%m/%d"]:
            try:
                dt = datetime.strptime(date_str, formato)
                return dt.strftime("%Y-%m-%d")
            except ValueError:
                continue
            
        return None
    
    def clean_string(self, value):
        if pd.isna(value):
            return None
        
        val_str = str(value).strip()
        val_str = val_str.replace('"', '').replace('\\', '')
        
        if val_str.lower() == 'nan' or val_str == "":
            return None
            
        return val_str
    
    def get_file_name(self, path):
        val = self.clean_string(path) 
        if val:
            name = os.path.basename(path).replace('/','')
            return name if name else None
        return None
    
    def get_edifil_code(self, text):
        val = self.clean_string(text)
        
        if val:
            match = re.search(r"Edi:,\s*(.*?)(?=\s*,,|$)", val)
            
            if match:
                return match.group(1).strip()
                    
        return None
    
    def export_to_json(self, *args, **options):
        # Define the output file path
        output_file = os.path.join(settings.BASE_DIR, 'resources/full_project_export.json')
        
        # We exclude contenttypes and permissions because they are 
        # recreated automatically by Django and often cause "Duplicate ID" 
        # errors when you try to load the JSON later.
        exclude_apps = ['contenttypes', 'auth.permission']

        self.stdout.write(f"Starting export of all apps to {output_file}...")

        with open(output_file, 'w', encoding='utf-8') as f:
            call_command(
                'dumpdata', 
                format='json', 
                indent=4, 
                exclude=exclude_apps,
                stdout=f
            )

        self.stdout.write(self.style.SUCCESS(f'Successfully exported all data!'))

    def handle(self, *args, **options):
        df = pd.read_csv("backend/resources/stamps.csv", sep='|')
        
        country_obj, _ = Country.objects.get_or_create(name="España")
        
        with transaction.atomic():
            for index, row in df.iterrows():
                try:
                    issue_year = row['issue_year']
                    
                    edifil_code = self.clean_string(row['edifil_code'])
                    issue_date = self.clean_date(row['issue_date'])
                    temp_issue_name = self.clean_string(row['issue_name'])
                    if temp_issue_name:
                        issue_name = temp_issue_name
                    issue_amount_printed = self.clean_number(row['issue_amount_printed'])
                    issue_description = self.clean_string(row['issue_description'])
                    
                    stamp_print_type = self.clean_string(row['stamp_print_type'])
                    stamp_type = self.clean_string(row['stamp_type'])
                    stamp_perforation = self.clean_string(row['stamp_perforation'])
                    stamp_colors_raw = self.clean_string(row['stamp_color'])
                    stamp_name = self.clean_string(row['stamp_name'])
                    stamp_face_value = self.clean_string(row['stamp_face_value'])
                    
                    issue_year_obj = None
                    if pd.notna(issue_year):
                        issue_year_obj, _ = Year.objects.get_or_create(year=int(issue_year))
                        
                    issue_print_type_obj = None
                    if pd.notna(row['stamp_print_type']):
                        issue_print_type_obj, _ = PrintType.objects.get_or_create(name=stamp_print_type)
                        
                    stamp_type_obj = None
                    if pd.notna(stamp_type):
                        stamp_type_obj, _ = StampType.objects.get_or_create(name=stamp_type)
                        
                        
                    issue_obj, created = Issue.objects.get_or_create(
                        name=issue_name,
                        date=issue_date,
                        total_printed=issue_amount_printed,
                        defaults={
                            'year': issue_year_obj,
                            'perforation': stamp_perforation,
                            'print_type': issue_print_type_obj,
                            'description': issue_description,
                            'country': country_obj,
                            'stamp_type': stamp_type_obj
                        }
                    )

                    if edifil_code:
                        image = f"{issue_year}/{edifil_code}.jpg"
                    else:
                        image = f"{issue_year}/{stamp_name.replace(' ','-')}.jpg"
                    stamp_obj, _ = Stamp.objects.get_or_create(
                        issue = issue_obj,
                        name = stamp_name,
                        face_value = stamp_face_value,
                        image = image,
                        edifil_code = edifil_code
                    )
                        
                    if stamp_colors_raw:
                        colors = self.clean_and_get_colors(stamp_colors_raw)
                        
                        color_objects = []
                        for color in colors:
                            color_obj, _ = Color.objects.get_or_create(name=color)
                            color_objects.append(color_obj)
                            
                        stamp_obj.colors.set(color_objects)

                    if index % 500 == 0 and index:
                        print(f"{index} rows processed...")
                    
                except Exception as e:
                    print(f"❌ Error in row {index} ({row.get('nombre_sello')}): {e}")
            
        print(f"Migration completed. {index} rows processed.\n")
        
        print("Exporting data to json...")
        self.export_to_json()