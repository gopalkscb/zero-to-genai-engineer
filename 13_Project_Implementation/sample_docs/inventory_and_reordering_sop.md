# Inventory and Reordering SOP

## Reorder levels (v1.0)

Each ingredient has a `reorder_level` in the stock system. When `stock <= reorder_level`, the item appears on the low-stock report. Kitchen managers review this report at 10:00 daily and again before dinner prep. Do not wait until stock reaches zero for proteins (chicken, mutton, fish, prawns).

## Supplier lead times (v1.0)

Chicken and mutton: next-morning delivery if ordered before 18:00. Fresh fish and prawns: same-day from the market by 11:00 — order by 08:00. Dry goods (rice, flour, lentils): 48-hour lead time. Dairy (cream, paneer, yogurt): daily delivery except Friday (order extra on Thursday).

## Waste logging (v1.1)

Any discarded prepared food must be weighed and logged with reason (overproduction, quality fail, return). Target waste below 3% of food cost weekly. Spoilage in the walk-in must be photographed and signed by the shift manager for supplier credit claims where applicable.

## Menu impact (v1.0)

If a key ingredient is unavailable, mark affected menu items as **86'd** on the POS before service starts. Do not substitute proteins without updating the guest — e.g. do not serve chicken in a mutton dish without explicit consent. Recipe quantities in `menu_item_ingredients` are the source of truth for theoretical usage reports.
