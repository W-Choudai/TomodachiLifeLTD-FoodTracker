from django.db import models


PREFERENCE_WEIGHTS = {
    "Absolutely Love":    5,
    "Really Like":        2,
    "Like (Jump)":        1,
    "Like":               0,
    "Didn't Like":       -1,
    "Really Didn't Like": -2,
    "Loathes":           -5,
}

PREFERENCE_CHOICES = [(k, k) for k in PREFERENCE_WEIGHTS]


class FoodCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "Food Categories"


class Food(models.Model):
    name             = models.CharField(max_length=100, unique=True)
    icon             = models.CharField(max_length=100, blank=True, null=True)
    food_type        = models.CharField(max_length=100, blank=True, null=True)
    food_category    = models.ForeignKey(FoodCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name="foods")
    flavor_type      = models.CharField(max_length=100, blank=True, null=True)
    buying_price     = models.FloatField(blank=True, null=True)
    appears_at_resto = models.BooleanField(default=False)
    smell            = models.CharField(max_length=100, blank=True, null=True)
    tastes_bad       = models.BooleanField(default=False)
    quantity         = models.CharField(max_length=100, blank=True, null=True)
    temperature      = models.CharField(max_length=100, blank=True, null=True)

    america_availability = models.BooleanField(default=False)
    asia_availability    = models.BooleanField(default=False)
    europe_availability  = models.BooleanField(default=False)
    japan_availability   = models.BooleanField(default=False)

    description   = models.TextField(blank=True, null=True)
    internal_name = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ["name"]


class Mii(models.Model):
    name       = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    def happiness_score(self):
        prefs = self.preferences.all()
        total = prefs.count()
        if total == 0:
            return None
        score = sum(PREFERENCE_WEIGHTS[p.preference] for p in prefs)
        return round(score / total, 2)

    class Meta:
        ordering = ["name"]


class FoodPreference(models.Model):
    mii        = models.ForeignKey(Mii, on_delete=models.CASCADE, related_name="preferences")
    food       = models.ForeignKey(Food, on_delete=models.CASCADE, related_name="preferences")
    preference = models.CharField(max_length=20, choices=PREFERENCE_CHOICES)

    class Meta:
        unique_together = ("mii", "food")

    def __str__(self):
        return f"{self.mii.name} - {self.food.name}: {self.preference}"