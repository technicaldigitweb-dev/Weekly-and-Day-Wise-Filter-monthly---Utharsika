-- UAWSO: resolve Utharsika's assigned Amazon ASINs.
-- Never filters order_transaction.user_name - assignment is via this
-- category chain only (04_DESIGN/UAWSO_BUSINESS_RULES_SPEC.md Section 1).
-- Parameters: %(assigned_user)s e.g. 'utharsika', %(channel_code)s e.g. 1

WITH target_user AS (
    SELECT "user" AS user_id
    FROM public."user"
    WHERE lower(user_name) = lower(%(assigned_user)s)
),
target_categories AS (
    SELECT c.id AS category_id
    FROM public.ph_categories c
    JOIN target_user u ON u.user_id = c.user_id
)
SELECT DISTINCT p.ref_id AS asin
FROM public.ph_cate_products p
JOIN target_categories c ON c.category_id = p.ass_cate_id
WHERE p.which_channel = %(channel_code)s;
