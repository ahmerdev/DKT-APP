from django.db.models import Sum, F, ExpressionWrapper, DecimalField
from .models import Order, OrderItem, Product, AppUser
from django.utils import timezone

def get_sales_report():
    items = OrderItem.objects.filter(order__status="delivered", order__type="normal")

    total_sales = items.aggregate(
        total_sales=Sum(
            ExpressionWrapper(F('price') * F('quantity'), output_field=DecimalField())
        )
    )["total_sales"] or 0
    total_cost = Product.objects.aggregate(
        total_cost=Sum(
            ExpressionWrapper(F('cost_price') * F('quantity'), output_field=DecimalField())
        )
    )["total_cost"] or 0

    total_profit = total_sales - total_cost
    total_orders = items.values('order').distinct().count()
    total_quantity = items.aggregate(total_qty=Sum('quantity'))["total_qty"] or 0

    return {
        "total_orders": total_orders,
        "total_sales": total_sales,
        "total_cost": total_cost,
        "total_profit": total_profit,
        "total_quantity": total_quantity,
    }

# PROFIT REPORT
def get_profit_report():
    items = OrderItem.objects.filter(order__status="delivered", product__isnull=False)

    profit_expr = ExpressionWrapper(
        (F('price') - F('product__cost_price')) * F('quantity'),
        output_field=DecimalField()
    )
    total_profit = items.aggregate(total=Sum(profit_expr))["total"] or 0
    return {"total_profit": total_profit}


#  CUSTOMER POTENTIAL REPORT
def get_customer_potentials(top_n=5):
    qs = Order.objects.filter(status="delivered").values('user__name').annotate(
        total_spent=Sum(ExpressionWrapper(F('items__price') * F('items__quantity'), output_field=DecimalField()))
    ).order_by('-total_spent')[:top_n]
    return list(qs)


# PRODUCT REPORT
def get_product_report():
    qs = (
        OrderItem.objects
        .filter(order__status="delivered", order__type="normal")
        .values('name')
        .annotate(
            total_quantity=Sum('quantity'),
            total_sales=Sum(
                ExpressionWrapper(F('price') * F('quantity'), output_field=DecimalField())
            )
        )
        .order_by('-total_quantity')
    )
    return list(qs)



from django.db.models.functions import Coalesce

def get_product_profit_report():
    items = (
        OrderItem.objects
        .filter(order__status="delivered")
        .select_related('product', 'order', 'order__user')
        .values('product__id', 'name', 'order__id', 'order__user__name')
        .annotate(
            total_sales=Sum(ExpressionWrapper(F('price') * F('quantity'), output_field=DecimalField())),
            total_cost=Sum(
                ExpressionWrapper(Coalesce(F('product__cost_price'), 0) * F('quantity'), output_field=DecimalField())
            ),
        )
        .annotate(total_profit=F('total_sales') - F('total_cost'))
        .order_by('-total_profit')
    )

    return list(items)
