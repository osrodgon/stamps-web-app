#!/bin/bash
python backend/manage.py dumpdata --exclude=auth.permission --exclude=contenttypes --exclude=sessions --exclude=admin.logentry config_api stamp_types_api locations_api print_types_api countries_api colors_api stamps_api issues_api years_api collections_api collection_items_api condition_types_api users_api artists_api paper_types_api printers_api --indent 2 > backend_data.json
echo "Database backup saved to backend_data.json"
