from django.db.models import Sum, F, ExpressionWrapper, DecimalField
from .models import Order, OrderItem, Product, AppUser


# -----------------------------
# 🧾 SALES REPORT
# -----------------------------
def get_sales_report():
    items = (
        OrderItem.objects
        .select_related('product', 'order')
        .filter(order__status__iexact="delivered", order__type__iexact="normal", product__isnull=False)
    )

    # Total Sales
    total_sales = items.aggregate(
        total_sales=Sum(ExpressionWrapper(F('price') * F('quantity'), output_field=DecimalField()))
    )["total_sales"] or 0

    # Total Cost
    total_cost = items.aggregate(
        total_cost=Sum(ExpressionWrapper(F('product__cost_price') * F('quantity'), output_field=DecimalField()))
    )["total_cost"] or 0

    # Profit
    total_profit = total_sales - total_cost

    # Extra metrics
    total_orders = items.values('order').distinct().count()
    total_quantity = items.aggregate(total_qty=Sum('quantity'))["total_qty"] or 0

    return {
        "total_orders": total_orders,
        "total_sales": total_sales,
        "total_cost": total_cost,
        "total_profit": total_profit,
        "total_quantity": total_quantity,
    }


# -----------------------------
# 💰 PROFIT REPORT (Overall)
# -----------------------------
def get_profit_report():
    items = (
        OrderItem.objects
        .select_related('product', 'order')
        .filter(order__status__iexact="delivered", product__isnull=False)
    )

    profit_expr = ExpressionWrapper(
        (F('price') - F('product__cost_price')) * F('quantity'),
        output_field=DecimalField(),
    )

    total_profit = items.aggregate(total_profit=Sum(profit_expr))["total_profit"] or 0

    return {"total_profit": total_profit}


# -----------------------------
# 👥 CUSTOMER POTENTIAL REPORT
# -----------------------------
def get_customer_potentials(top_n=5):
    qs = (
        Order.objects
        .filter(status__iexact="delivered")
        .values('user__name')
        .annotate(
            total_spent=Sum(
                ExpressionWrapper(F('items__price') * F('items__quantity'), output_field=DecimalField())
            )
        )
        .order_by('-total_spent')[:top_n]
    )

    return list(qs)


# -----------------------------
# 📦 PRODUCT PERFORMANCE REPORT
# -----------------------------
def get_product_report():
    qs = (
        OrderItem.objects
        .select_related('product', 'order')
        .filter(order__status__iexact="delivered", order__type__iexact="normal", product__isnull=False)
        .values('product__name')
        .annotate(
            total_quantity=Sum('quantity'),
            total_sales=Sum(
                ExpressionWrapper(F('price') * F('quantity'), output_field=DecimalField())
            ),
            total_cost=Sum(
                ExpressionWrapper(F('product__cost_price') * F('quantity'), output_field=DecimalField())
            ),
        )
        .annotate(total_profit=F('total_sales') - F('total_cost'))
        .order_by('-total_quantity')
    )

    # Clean up keys for template
    return [
        {
            "name": item["product__name"],
            "total_quantity": item["total_quantity"] or 0,
            "total_sales": item["total_sales"] or 0,
            "total_cost": item["total_cost"] or 0,
            "total_profit": item["total_profit"] or 0,
        }
        for item in qs
    ]


# -----------------------------
# 📊 DETAILED PRODUCT PROFIT REPORT
# -----------------------------
def get_product_profit_report():
    items = (
        OrderItem.objects
        .select_related('order', 'product')
        .filter(order__status__iexact="delivered", product__isnull=False)
        .values(
            'product__name',
            'price',
            'quantity',
            'order__id',
            'order__user__name'
        )
        .annotate(
            total_sales=Sum(ExpressionWrapper(F('price') * F('quantity'), output_field=DecimalField())),
            total_cost=Sum(ExpressionWrapper(F('product__cost_price') * F('quantity'), output_field=DecimalField())),
        )
        .annotate(total_profit=F('total_sales') - F('total_cost'))
        .order_by('-total_profit')
    )

    return list(items)
