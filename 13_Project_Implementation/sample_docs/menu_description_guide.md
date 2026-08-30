# Menu Description Guide

## Signature dishes (v1.1)

Butter Chicken is the restaurant's signature dish, made with overnight-marinated tandoori chicken in a tomato and butter gravy. Chicken Biryani follows the Hyderabadi dum style where rice and meat are sealed and slow-cooked together. These two items should always appear in the top three on printed menus and delivery apps.

## Writing standards (v1.2)

Descriptions are two sentences maximum: first sentence = what it is; second = key ingredient or cooking method. Mention spice level for dishes marked hot (Chicken 65, Mutton Rogan Josh). Use **Main Course**, **Starters**, **Breads**, **Rice**, **Desserts**, and **Beverages** exactly — do not invent new categories without owner approval.

## Vegetarian and vegan labelling (v1.2)

Items with paneer, dairy, or ghee are vegetarian but not vegan. Dal Makhani and Chana Masala are vegetarian. There are no fully vegan mains on the standard menu; guests asking for vegan options should be offered Veg Biryani without ghee (kitchen confirmation required). Always sync `is_veg` in the POS when adding new items.

## Pricing bands (v1.2)

Starters: AED 18–35. Main Course: AED 24–55. Breads: AED 6–12. Rice sides: AED 12–18. Desserts: AED 14–20. Beverages: AED 8–15. Any new item priced more than 20% above its category band needs manager sign-off before publishing.

## Seasonal and inactive items (v1.1)

Seasonal specials must have a planned end date. When an item is discontinued, set `active = 0` in the menu system — do not delete historical records. Mushroom Pepper Fry and Kulfi Falooda are examples of inactive items kept for order history integrity.
