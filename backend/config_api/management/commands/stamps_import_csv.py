import os
import re
from datetime import datetime
from turtle import st, stamp

import pandas as pd
from pyparsing import col
from printers_api.models import Printer
from colors_api.models import Color
from countries_api.models import Country
from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from issues_api.models import Issue
from artists_api.models import Artist
from print_types_api.models import PrintType
from stamp_types_api.models import StampType
from paper_types_api.models import PaperType
from stamps_api.models import Stamp
from years_api.models import Year


class Command(BaseCommand):
    help = 'Imports data from csv file.'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--csv-file',
            type=str,
            required=True,
            help='Path to the CSV file (e.g., /path/to/stamps.csv)'
        )
    
    def clean_and_get_colors(self,color_string):
        if pd.isna(color_string) or str(color_string).strip() == "":
            return []
        
        if  str(color_string).find('Multicolor (') != -1 or \
            str(color_string).find('Policromía (') != -1 or \
            str(color_string).find('Policromático (') != -1: 
                colors_names = [color_string]
        else: 
            colors_names = [c.strip() for c in re.split(r',| y | Y ', color_string) if c.strip()]
        
        color_objects = []
        for name in colors_names:
            final_name = name.strip(' ').strip(',')
            final_name = self.clean_string(final_name).capitalize()
            if final_name and final_name.lower() != 'nan': 
                color_obj, _ = Color.objects.get_or_create(name=final_name)
                color_objects.append(color_obj)
        
        return color_objects
    
    def clean_number(self, value):
        if pd.isna(value) or str(value).strip() == "":
            return None
        
        # If it's already a number (int or float), return it directly.
        # This prevents the bug where a parsed float like 10.0 is converted 
        # to string "10.0" and then cleaned to "100" by removing the dot.
        if isinstance(value, (int, float)):
            return value
            
        value_str = str(value).strip()
        if value_str.lower() in ['n/a', 'nan']:
            return None
            
        # Handle Spanish formatting if it's a string: 1.234,56 -> 1234.56
        if ',' in value_str:
            # Assume . is thousands and , is decimal
            value_str = value_str.replace('.', '').replace(',', '.')
        else:
            # If it has only dots, decide if they are thousands or decimal.
            # Multiple dots means they are thousands separators (e.g., 1.234.567)
            if value_str.count('.') > 1:
                value_str = value_str.replace('.', '')
            # If it has exactly one dot, we treat it as a decimal point (e.g., 10.50)
            # to be safe and avoid the common "multiply by 10" error.

        try:
            # Try parsing as float first to preserve potential decimals
            result = float(value_str)
            # If it's exactly equivalent to an integer, return it as one
            if result.is_integer():
                return int(result)
            return result
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
    
    # def get_edifil_code(self, text):
    #     val = self.clean_string(text)
        
    #     if val:
    #         match = re.search(r"Edi:,\s*(.*?)(?=\s*,,|$)", val)
            
    #         if match:
    #             return match.group(1).strip()
                    
    #     return None
    
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
        csv_file_path = options['csv_file']
        
        # Validate file exists before processing
        if not os.path.exists(csv_file_path):
            raise CommandError(f"CSV file not found: {csv_file_path}")
            
        df = pd.read_csv(csv_file_path, sep='|')
        df = df.dropna(how='all')
        
        country_row, _ = Country.objects.get_or_create(name="España")
        
        with transaction.atomic():
            for index, row in df.iterrows():
                try:
                    # Clean and prepare data.
                    # - date
                    date_cleaned = self.clean_date(row.get('issue_date'))
                    
                    # Create or get related objects
                    # - year
                    # - color
                    # - stamp type
                    # - paper type
                    # - print type
                    # - artist
                    # - printer
                    if date_cleaned:
                        year_row, _ = Year.objects.get_or_create(year=date_cleaned[0:4])
                    else:
                        year_row = None
                    color_rows = self.clean_and_get_colors(row.get('color'))
                    stamp_type = self.clean_string(row.get('stamp_type'))
                    if stamp_type:
                        stamp_type_row, _ = StampType.objects.get_or_create(name=self.clean_string(row.get('stamp_type')))
                    paper_type = self.clean_string(row.get('paper_type'))
                    if paper_type:
                        paper_type_row, _ = PaperType.objects.get_or_create(name=paper_type)
                    print_type = self.clean_string(row.get('print_type'))
                    if print_type:
                        print_type_row, _ = PrintType.objects.get_or_create(name=print_type)
                    artist_name = self.clean_string(row.get('artist'))
                    if artist_name:
                        artist_row, _ = Artist.objects.get_or_create(name=artist_name)
                    printer_name = self.clean_string(row.get('printer'))
                    if printer_name:
                        printer_row, _ = Printer.objects.get_or_create(name=printer_name)
                        
                    # Create the issue object
                    total_printed = self.clean_number(row.get('total_printed_issue'))
                    market_value_mnh = self.clean_number(row.get('market_value_mnh_issue'))
                    market_value_used = self.clean_number(row.get('market_value_used_issue'))
                    description = self.clean_string(row.get('description_issue'))
                    note = self.clean_string(row.get('note_issue'))
                    perforation = self.clean_string(row.get('perforation'))
                    issue_row, _ = Issue.objects.get_or_create(
                        name=self.clean_string(row.get('issue_name')),
                        country=country_row,
                        year=year_row,
                        date=date_cleaned,
                        stamp_type=stamp_type_row if stamp_type else None,
                        paper_type=paper_type_row if paper_type else None,
                        print_type=print_type_row if print_type else None,
                        artist=artist_row if artist_name else None,
                        printer=printer_row if printer_name else None,
                        total_printed=total_printed if total_printed else None,
                        market_value_mnh=market_value_mnh if market_value_mnh else None,
                        market_value_used=market_value_used if market_value_used else None,
                        description=description if description else None,
                        note=note if note else None,
                        perforation=perforation if perforation else None
                    )
                    
                    # Create the stamp object
                    edifil_code = self.clean_string(row.get('edifil_code'))
                    fesofi_code = self.clean_string(row.get('fesofi_code'))
                    name = self.clean_string(row.get('motive'))
                    face_value = self.clean_string(row.get('face_value'))
                    description = self.clean_string(row.get('description_stamp'))
                    market_value_mnh = self.clean_number(row.get('market_value_mnh_stamp'))
                    market_value_used = self.clean_number(row.get('market_value_used_stamp'))
                    total_printed = self.clean_number(row.get('total_printed_stamp'))
                    stamp_row = Stamp.objects.create(
                        issue=issue_row,
                        edifil_code=edifil_code if edifil_code else None,
                        fesofi_code=fesofi_code if fesofi_code else None,
                        name=name if name else "Falta nombre del sello",
                        face_value=face_value if face_value else "Falta valor facial",
                        description=description if description else None,
                        market_value_mnh=market_value_mnh if market_value_mnh else None,
                        market_value_used=market_value_used if market_value_used else None,
                        total_printed=total_printed if total_printed else None
                    )
                    stamp_row.colors.set(color_rows)
                    
                    if (index + 1) % 100 == 0:
                        self.stdout.write(f"{index +1} rows processed...")
                    
                    # if index == 100:
                    #     break
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"❌ Error in row {index + 2} ({row.get('issue_name')} - {row.get('motive')} ): {e}"))
                    print(color_rows)
                    break
            
        self.stdout.write(self.style.SUCCESS(f"Migration completed. {index} rows processed.\n"))
        transaction.commit()
        
        # self.stdout.write("Exporting data to json...")
        # self.export_to_json()