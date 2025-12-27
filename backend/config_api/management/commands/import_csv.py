from datetime import datetime
import os
import re
from django.core.management.base import BaseCommand
from django.db import transaction
import pandas as pd

from years_api.models import Year
from print_types_api.models import PrintType
from colors_api.models import Color
from issues_api.models import Issue
from stamps_api.models import Stamp
from countries_api.models import Country
from stamp_types_api.models import StampType

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
        
        for formato in ["%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d"]:
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

    def handle(self, *args, **options):
        df = pd.read_csv("dataset/sellos_espana.csv")
        
        country_obj, _ = Country.objects.get_or_create(name="España")
        
        with transaction.atomic():
            for index, row in df.iterrows():
                try:
                    total_printed = self.clean_number(row['tirada'])
                    date = self.clean_date(row['fecha_emision'])
                    stamp_name = self.clean_string(row['nombre_sello'])
                    issue_raw = self.clean_string(row['serie'])
                    issue_name = issue_raw if issue_raw else stamp_name
                    perforation = self.clean_string(row['perforacion'])
                    description = self.clean_string(row['descripcion'])
                    face_value = self.clean_string(row['valor_facial'])
                    print_type = self.clean_string(row['impresion'])
                    colors_raw = self.clean_string(row['colores'])
                    stamp_type = self.clean_string(row['formato'])
                    edifil_code = self.get_edifil_code(row['codigos'])
                    
                    year_val = row['año']
                    year_obj = None
                    if pd.notna(year_val):
                        year_obj, _ = Year.objects.get_or_create(year=int(year_val))
                        
                    print_obj = None
                    if pd.notna(row['impresion']):
                        print_obj, _ = PrintType.objects.get_or_create(name=print_type)
                        
                    stamp_type_obj = None
                    if pd.notna(stamp_type):
                        stamp_type_obj, _ = StampType.objects.get_or_create(name=stamp_type)
                        
                        
                    issue_obj, created = Issue.objects.get_or_create(
                        name=issue_name,
                        date=date,
                        total_printed=total_printed,
                        defaults={
                            'year': year_obj,
                            'perforation': perforation,
                            'description': description,
                            'country': country_obj,
                            'stamp_type': stamp_type_obj
                        }
                    )

                    if edifil_code:
                        image = f"{year_val}/{edifil_code}.jpg"
                    else:
                        image = f"{year_val}/{stamp_name.replace(' ','-')}.jpg"
                    stamp_obj, _ = Stamp.objects.get_or_create(
                        issue = issue_obj,
                        name = stamp_name,
                        face_value = face_value,
                        image = image,
                        edifil_code = edifil_code
                    )
                        
                    if colors_raw:
                        colors = self.clean_and_get_colors(colors_raw)
                        
                        color_objects = []
                        for color in colors:
                            color_obj, _ = Color.objects.get_or_create(name=color)
                            color_objects.append(color_obj)
                            
                        stamp_obj.colors.set(color_objects)

                    if index % 500 == 0 and index:
                        print(f"{index} rows processed...")
                    
                except Exception as e:
                    print(f"❌ Error in row {index} ({row.get('nombre_sello')}): {e}")
            
        print(f"Migration completed. {index} rows processed.")