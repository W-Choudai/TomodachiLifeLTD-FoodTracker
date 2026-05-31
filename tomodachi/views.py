from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json

from .models import Mii, Food, FoodCategory, FoodPreference, PREFERENCE_WEIGHTS

PREFS = ["All"] + list(PREFERENCE_WEIGHTS.keys())


def category_score(prefs_in_category):
    """
    Sum of (count * weight) / total foods tried in category.
    Returns None if nothing has been tried yet.
    """
    tried = [p for p in prefs_in_category if p is not None]
    if not tried:
        return None
    total = len(tried)
    weighted = sum(PREFERENCE_WEIGHTS[p] for p in tried)
    return round(weighted / total, 2)


def index(request):
    miis = Mii.objects.all()
    return render(request, "tomodachi/index.html", {
        "miis": miis,
        "prefs": PREFS,
    })


def mii_detail(request, mii_id):
    mii   = get_object_or_404(Mii, id=mii_id)
    miis  = Mii.objects.all()
    foods = Food.objects.select_related("food_category").order_by("food_category__name", "name")

    existing_prefs = {p.food_id: p.preference for p in mii.preferences.select_related("food")}

    categories = {}
    for food in foods:
        cat_name = food.food_category.name if food.food_category else "Uncategorized"
        if cat_name not in categories:
            categories[cat_name] = {"foods": [], "prefs_list": []}
        pref = existing_prefs.get(food.id)
        categories[cat_name]["foods"].append({
            "id":         food.id,
            "name":       food.name,
            "icon":       food.icon or "",
            "flavor":     food.flavor_type or "",
            "preference": pref,
            "temperature": food.temperature or "",
        })
        categories[cat_name]["prefs_list"].append(pref)

    for cat_name, data in categories.items():
        tried = [p for p in data["prefs_list"] if p is not None]
        data["score"] = round(sum(PREFERENCE_WEIGHTS[p] for p in tried) / len(tried), 2) if tried else None

    total_set = len(existing_prefs)

    return render(request, "tomodachi/index.html", {
        "miis":       miis,
        "active_mii": mii,
        "categories": categories,
        "prefs":      PREFS,
        "total_set":  total_set,
    })

@require_POST
def add_mii(request):
    name = request.POST.get("name", "").strip()
    if not name:
        return redirect("tomodachi:index")
    mii, _ = Mii.objects.get_or_create(name=name)
    return redirect("tomodachi:mii_detail", mii_id=mii.id)


@require_POST
def delete_mii(request, mii_id):
    mii = get_object_or_404(Mii, id=mii_id)
    mii.delete()
    return redirect("tomodachi:index")


@csrf_exempt
@require_POST
def set_preference(request, mii_id):
    mii  = get_object_or_404(Mii, id=mii_id)
    data = json.loads(request.body)
    food_id    = data.get("food_id")
    preference = data.get("preference")

    food = get_object_or_404(Food, id=food_id)

    if preference is None:
        FoodPreference.objects.filter(mii=mii, food=food).delete()
    else:
        FoodPreference.objects.update_or_create(
            mii=mii, food=food,
            defaults={"preference": preference}
        )

    # Recompute per-category scores for the response
    all_prefs = mii.preferences.select_related("food__food_category").all()
    cat_prefs = {}
    for p in all_prefs:
        cat = p.food.food_category.name if p.food.food_category else "Uncategorized"
        cat_prefs.setdefault(cat, []).append(p.preference)

    # Also include foods with no preference yet in this category (for denominator)
    # We only count tried foods, use what's there
    cat_scores = {}
    for cat, plist in cat_prefs.items():
        tried = [p for p in plist if p]
        if not tried:
            cat_scores[cat] = None
        else:
            cat_scores[cat] = round(sum(PREFERENCE_WEIGHTS[p] for p in tried) / len(tried), 2)

    return JsonResponse({"status": "ok", "category_scores": cat_scores})