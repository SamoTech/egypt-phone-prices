"""Admin endpoints: seed data, trigger scrape, view logs."""
from fastapi import APIRouter, Depends, HTTPException, Header, Query
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import get_db

router = APIRouter(prefix="/admin")

BRANDS = [
    ("Samsung", "samsung"), ("Apple", "apple"), ("Xiaomi", "xiaomi"),
    ("Oppo", "oppo"), ("Realme", "realme"), ("Huawei", "huawei"),
    ("Honor", "honor"), ("Vivo", "vivo"), ("OnePlus", "oneplus"),
    ("Tecno", "tecno"), ("Infinix", "infinix"), ("itel", "itel"),
    ("Nokia", "nokia"), ("Motorola", "motorola"), ("Sony", "sony"),
    ("Google", "google"), ("Lenovo", "lenovo"), ("Asus", "asus"),
    ("ZTE", "zte"), ("TCL", "tcl"), ("Alcatel", "alcatel"),
    ("Blackview", "blackview"), ("Umidigi", "umidigi"), ("Doogee", "doogee"),
]

SEED_DEVICES = [
    {"brand":"samsung","name":"Samsung Galaxy S25 Ultra","slug":"samsung-galaxy-s25-ultra","display":"6.9\" QHD+ AMOLED","chipset":"Snapdragon 8 Elite","ram":"12GB","storage":"256GB","camera":"200MP","battery":"5000mAh","os":"Android 15","release_year":2025,"prices":[{"retailer":"jumia","price":89999},{"retailer":"noon","price":91500},{"retailer":"btech","price":88500}]},
    {"brand":"samsung","name":"Samsung Galaxy S25+","slug":"samsung-galaxy-s25-plus","display":"6.7\" QHD+ AMOLED","chipset":"Snapdragon 8 Elite","ram":"12GB","storage":"256GB","camera":"50MP","battery":"4900mAh","os":"Android 15","release_year":2025,"prices":[{"retailer":"jumia","price":72999},{"retailer":"noon","price":74000},{"retailer":"btech","price":71500}]},
    {"brand":"samsung","name":"Samsung Galaxy S25","slug":"samsung-galaxy-s25","display":"6.2\" FHD+ AMOLED","chipset":"Snapdragon 8 Elite","ram":"12GB","storage":"128GB","camera":"50MP","battery":"4000mAh","os":"Android 15","release_year":2025,"prices":[{"retailer":"jumia","price":54999},{"retailer":"noon","price":56000},{"retailer":"btech","price":53999}]},
    {"brand":"samsung","name":"Samsung Galaxy A56","slug":"samsung-galaxy-a56","display":"6.7\" FHD+ AMOLED","chipset":"Exynos 1580","ram":"8GB","storage":"256GB","camera":"50MP","battery":"5000mAh","os":"Android 15","release_year":2025,"prices":[{"retailer":"jumia","price":24999},{"retailer":"btech","price":24500},{"retailer":"amazon_eg","price":25200}]},
    {"brand":"samsung","name":"Samsung Galaxy A36","slug":"samsung-galaxy-a36","display":"6.6\" FHD+ AMOLED","chipset":"Snapdragon 6 Gen 3","ram":"8GB","storage":"128GB","camera":"50MP","battery":"5000mAh","os":"Android 15","release_year":2025,"prices":[{"retailer":"jumia","price":17999},{"retailer":"noon","price":18500}]},
    {"brand":"apple","name":"Apple iPhone 16 Pro Max","slug":"apple-iphone-16-pro-max","display":"6.9\" Super Retina XDR","chipset":"Apple A18 Pro","ram":"8GB","storage":"256GB","camera":"48MP","battery":"4685mAh","os":"iOS 18","release_year":2024,"prices":[{"retailer":"jumia","price":109999},{"retailer":"noon","price":112000},{"retailer":"amazon_eg","price":108500}]},
    {"brand":"apple","name":"Apple iPhone 16 Pro","slug":"apple-iphone-16-pro","display":"6.3\" Super Retina XDR","chipset":"Apple A18 Pro","ram":"8GB","storage":"128GB","camera":"48MP","battery":"3582mAh","os":"iOS 18","release_year":2024,"prices":[{"retailer":"jumia","price":89999},{"retailer":"noon","price":91000}]},
    {"brand":"apple","name":"Apple iPhone 16","slug":"apple-iphone-16","display":"6.1\" Super Retina XDR","chipset":"Apple A18","ram":"8GB","storage":"128GB","camera":"48MP","battery":"3561mAh","os":"iOS 18","release_year":2024,"prices":[{"retailer":"jumia","price":62999},{"retailer":"btech","price":61500},{"retailer":"amazon_eg","price":63500}]},
    {"brand":"apple","name":"Apple iPhone 15","slug":"apple-iphone-15","display":"6.1\" Super Retina XDR","chipset":"Apple A16","ram":"6GB","storage":"128GB","camera":"48MP","battery":"3349mAh","os":"iOS 18","release_year":2023,"prices":[{"retailer":"jumia","price":44999},{"retailer":"noon","price":45500}]},
    {"brand":"xiaomi","name":"Xiaomi 15 Ultra","slug":"xiaomi-15-ultra","display":"6.73\" QHD+ AMOLED","chipset":"Snapdragon 8 Elite","ram":"16GB","storage":"512GB","camera":"200MP Leica","battery":"6000mAh","os":"Android 15","release_year":2025,"prices":[{"retailer":"jumia","price":74999},{"retailer":"noon","price":76000}]},
    {"brand":"xiaomi","name":"Xiaomi Redmi Note 14 Pro+","slug":"xiaomi-redmi-note-14-pro-plus","display":"6.67\" FHD+ AMOLED","chipset":"Dimensity 9300+","ram":"12GB","storage":"256GB","camera":"200MP","battery":"6000mAh","os":"Android 14","release_year":2024,"prices":[{"retailer":"jumia","price":22999},{"retailer":"noon","price":23500},{"retailer":"btech","price":22500}]},
    {"brand":"xiaomi","name":"Xiaomi Redmi 14C","slug":"xiaomi-redmi-14c","display":"6.88\" HD+ LCD","chipset":"Helio G81 Ultra","ram":"8GB","storage":"256GB","camera":"50MP","battery":"5160mAh","os":"Android 14","release_year":2024,"prices":[{"retailer":"jumia","price":7999},{"retailer":"noon","price":8200},{"retailer":"amazon_eg","price":7800}]},
    {"brand":"oppo","name":"Oppo Find X8 Pro","slug":"oppo-find-x8-pro","display":"6.78\" QHD+ AMOLED","chipset":"Dimensity 9400","ram":"12GB","storage":"256GB","camera":"50MP Hasselblad","battery":"5910mAh","os":"Android 15","release_year":2024,"prices":[{"retailer":"jumia","price":69999},{"retailer":"noon","price":71000}]},
    {"brand":"oppo","name":"Oppo Reno 13 Pro","slug":"oppo-reno-13-pro","display":"6.83\" FHD+ AMOLED","chipset":"Dimensity 8350","ram":"12GB","storage":"256GB","camera":"50MP","battery":"5600mAh","os":"Android 15","release_year":2025,"prices":[{"retailer":"jumia","price":29999},{"retailer":"btech","price":29500}]},
    {"brand":"realme","name":"Realme GT 7 Pro","slug":"realme-gt-7-pro","display":"6.78\" QHD+ AMOLED","chipset":"Snapdragon 8 Elite","ram":"12GB","storage":"256GB","camera":"50MP","battery":"6500mAh","os":"Android 15","release_year":2024,"prices":[{"retailer":"jumia","price":44999},{"retailer":"noon","price":45999}]},
    {"brand":"realme","name":"Realme C75","slug":"realme-c75","display":"6.72\" HD+ LCD","chipset":"Helio G92","ram":"8GB","storage":"256GB","camera":"50MP","battery":"6000mAh","os":"Android 14","release_year":2025,"prices":[{"retailer":"jumia","price":8999},{"retailer":"noon","price":9200}]},
    {"brand":"huawei","name":"Huawei Pura 70 Ultra","slug":"huawei-pura-70-ultra","display":"6.8\" LTPO OLED","chipset":"Kirin 9010","ram":"16GB","storage":"512GB","camera":"50MP Leica","battery":"5000mAh","os":"HarmonyOS 4","release_year":2024,"prices":[{"retailer":"noon","price":84999},{"retailer":"amazon_eg","price":86000}]},
    {"brand":"huawei","name":"Huawei Nova 13 Pro","slug":"huawei-nova-13-pro","display":"6.76\" OLED","chipset":"Kirin 8000","ram":"8GB","storage":"256GB","camera":"50MP","battery":"4600mAh","os":"HarmonyOS 4.2","release_year":2024,"prices":[{"retailer":"jumia","price":26999},{"retailer":"btech","price":26500}]},
    {"brand":"honor","name":"Honor Magic 7 Pro","slug":"honor-magic-7-pro","display":"6.8\" QHD+ OLED","chipset":"Snapdragon 8 Elite","ram":"12GB","storage":"512GB","camera":"50MP","battery":"5850mAh","os":"Android 15","release_year":2024,"prices":[{"retailer":"jumia","price":59999},{"retailer":"noon","price":61000}]},
    {"brand":"vivo","name":"Vivo X200 Pro","slug":"vivo-x200-pro","display":"6.78\" QHD+ AMOLED","chipset":"Dimensity 9400","ram":"16GB","storage":"512GB","camera":"200MP Zeiss","battery":"6000mAh","os":"Android 15","release_year":2024,"prices":[{"retailer":"jumia","price":64999},{"retailer":"noon","price":66000}]},
    {"brand":"oneplus","name":"OnePlus 13","slug":"oneplus-13","display":"6.82\" QHD+ AMOLED","chipset":"Snapdragon 8 Elite","ram":"12GB","storage":"256GB","camera":"50MP Hasselblad","battery":"6000mAh","os":"Android 15","release_year":2025,"prices":[{"retailer":"jumia","price":49999},{"retailer":"noon","price":51000},{"retailer":"amazon_eg","price":49500}]},
    {"brand":"tecno","name":"Tecno Phantom X2 Pro","slug":"tecno-phantom-x2-pro","display":"6.8\" FHD+ AMOLED","chipset":"Dimensity 9000","ram":"12GB","storage":"256GB","camera":"50MP","battery":"5160mAh","os":"Android 13","release_year":2023,"prices":[{"retailer":"jumia","price":24999},{"retailer":"noon","price":25500}]},
    {"brand":"infinix","name":"Infinix Zero 40 5G","slug":"infinix-zero-40-5g","display":"6.78\" FHD+ AMOLED","chipset":"Dimensity 8200 Ultimate","ram":"12GB","storage":"256GB","camera":"50MP","battery":"5000mAh","os":"Android 14","release_year":2024,"prices":[{"retailer":"jumia","price":14999},{"retailer":"noon","price":15500}]},
    {"brand":"google","name":"Google Pixel 9 Pro","slug":"google-pixel-9-pro","display":"6.3\" LTPO OLED","chipset":"Google Tensor G4","ram":"16GB","storage":"256GB","camera":"50MP","battery":"4700mAh","os":"Android 15","release_year":2024,"prices":[{"retailer":"noon","price":64999},{"retailer":"amazon_eg","price":63500}]},
    {"brand":"motorola","name":"Motorola Edge 50 Pro","slug":"motorola-edge-50-pro","display":"6.7\" FHD+ pOLED","chipset":"Snapdragon 7 Gen 3","ram":"12GB","storage":"256GB","camera":"50MP","battery":"4500mAh","os":"Android 14","release_year":2024,"prices":[{"retailer":"jumia","price":22999},{"retailer":"noon","price":23500}]},
    {"brand":"sony","name":"Sony Xperia 1 VI","slug":"sony-xperia-1-vi","display":"6.5\" 4K OLED","chipset":"Snapdragon 8 Gen 3","ram":"12GB","storage":"256GB","camera":"52MP Zeiss","battery":"5000mAh","os":"Android 14","release_year":2024,"prices":[{"retailer":"noon","price":79999},{"retailer":"amazon_eg","price":81000}]},
]


async def _do_seed(db: AsyncSession):
    brand_ids = {}
    for name, slug in BRANDS:
        result = await db.execute(
            text("INSERT INTO brands (name, slug) VALUES (:name, :slug) ON CONFLICT (slug) DO UPDATE SET name=EXCLUDED.name RETURNING id"),
            {"name": name, "slug": slug},
        )
        brand_ids[slug] = str(result.scalar_one())
    await db.commit()

    result = await db.execute(text("SELECT slug, id FROM retailers"))
    retailer_ids = {row.slug: str(row.id) for row in result.fetchall()}

    inserted_devices = 0
    inserted_prices = 0

    for d in SEED_DEVICES:
        brand_id = brand_ids.get(d["brand"])
        if not brand_id:
            continue
        result = await db.execute(
            text("""
                INSERT INTO devices (brand_id, name, slug, display, chipset, ram, storage, camera, battery, os, release_year)
                VALUES (:brand_id, :name, :slug, :display, :chipset, :ram, :storage, :camera, :battery, :os, :release_year)
                ON CONFLICT (slug) DO UPDATE SET name=EXCLUDED.name RETURNING id
            """),
            {"brand_id": brand_id, "name": d["name"], "slug": d["slug"],
             "display": d["display"], "chipset": d["chipset"], "ram": d["ram"],
             "storage": d["storage"], "camera": d["camera"], "battery": d["battery"],
             "os": d["os"], "release_year": d["release_year"]},
        )
        device_id = str(result.scalar_one())
        inserted_devices += 1
        for p in d.get("prices", []):
            retailer_id = retailer_ids.get(p["retailer"])
            if not retailer_id:
                continue
            await db.execute(
                text("INSERT INTO prices (device_id, retailer_id, price_egp, product_url) VALUES (:device_id, :retailer_id, :price_egp, :product_url)"),
                {"device_id": device_id, "retailer_id": retailer_id,
                 "price_egp": p["price"], "product_url": f"https://egypt-phone-prices.vercel.app/devices/{d['slug']}"},
            )
            inserted_prices += 1
    await db.commit()
    return {"ok": True, "brands": len(brand_ids), "devices": inserted_devices, "prices": inserted_prices}


@router.get("/seed-now")
async def seed_now(
    token: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """One-time GET seed — token passed as ?token=... query param."""
    if token != settings.ADMIN_TOKEN:
        raise HTTPException(status_code=403, detail="Invalid token")
    return await _do_seed(db)


@router.post("/seed")
async def seed_data(
    db: AsyncSession = Depends(get_db),
    x_admin_token: str = Header(default=""),
):
    if x_admin_token != settings.ADMIN_TOKEN:
        raise HTTPException(status_code=403, detail="Invalid admin token")
    return await _do_seed(db)


@router.get("/stats")
async def stats(db: AsyncSession = Depends(get_db)):
    counts = {}
    for table in ["brands", "devices", "retailers", "prices", "scrape_logs"]:
        r = await db.execute(text(f"SELECT COUNT(*) FROM {table}"))
        counts[table] = r.scalar()
    return counts


@router.get("/logs")
async def logs(db: AsyncSession = Depends(get_db), limit: int = 50):
    r = await db.execute(text("SELECT * FROM scrape_logs ORDER BY started_at DESC LIMIT :limit"), {"limit": limit})
    return [{"id": row.id, "retailer": row.retailer_slug, "status": row.status,
             "devices": row.devices_scraped, "error": row.error_message,
             "started": str(row.started_at)} for row in r.fetchall()]
