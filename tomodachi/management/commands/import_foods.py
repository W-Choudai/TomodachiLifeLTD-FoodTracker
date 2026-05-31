import re
import pandas as pd
from django.core.management.base import BaseCommand
from tomodachi.models import Food, FoodCategory


class Command(BaseCommand):
    help = "Import foods from Excel file"

    def add_arguments(self, parser):
        parser.add_argument("file_path", nargs="?", default="data/foods.xlsx")

    def handle(self, *args, **kwargs):
        file_path = kwargs["file_path"]

        try:
            df = pd.read_excel(file_path, sheet_name="Foods")
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Could not read file: {e}"))
            return

        df.columns = df.columns.str.strip()

        if "Food category" in df.columns:
            df["Food category"] = df["Food category"].ffill()

        def safe(row, col, default=None):
            return row[col] if col in row.index and pd.notna(row[col]) else default

        def get_primary_category(raw_name):
            """Split 'Bread and Pastry' or 'Bread, Pastry' → use first part only."""
            parts = re.split(r'\band\b|,', str(raw_name), flags=re.IGNORECASE)
            parts = [p.strip() for p in parts if p.strip()]
            return parts[0] if parts else "Uncategorized"

        created = updated = skipped = 0

        for _, row in df.iterrows():
            name = safe(row, "Name")
            if not name:
                skipped += 1
                continue

            raw_category  = safe(row, "Food category", "Uncategorized")
            category_name = get_primary_category(raw_category)
            category, _   = FoodCategory.objects.get_or_create(name=category_name)

            _, was_created = Food.objects.update_or_create(
                name=str(name).strip(),
                defaults={
                    "icon":                 safe(row, "Icon"),
                    "food_type":            safe(row, "Food type"),
                    "food_category":        category,
                    "flavor_type":          safe(row, "Flavor type"),
                    "buying_price":         safe(row, "Buying price"),
                    "appears_at_resto":     bool(safe(row, "Appears at resto", False)),
                    "smell":               safe(row, "Smell"),
                    "tastes_bad":           bool(safe(row, "Tastes bad", False)),
                    "quantity":             safe(row, "Quantity"),
                    "temperature":          safe(row, "Temperature"),
                    "america_availability": bool(safe(row, "America availability", False)),
                    "asia_availability":    bool(safe(row, "Asia availability", False)),
                    "europe_availability":  bool(safe(row, "Europe availability", False)),
                    "japan_availability":   bool(safe(row, "Japan availability", False)),
                    "description":          safe(row, "Description"),
                    "internal_name":        safe(row, "Internal name"),
                }
            )
            if was_created:
                created += 1
            else:
                updated += 1

        self.stdout.write(self.style.SUCCESS(
            f"Done! {created} created, {updated} updated, {skipped} skipped (blank name rows)."
        ))