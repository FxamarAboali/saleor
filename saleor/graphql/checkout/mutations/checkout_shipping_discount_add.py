import graphene

from ....core.permissions import CheckoutPermissions
from ...core.mutations import BaseMutation
from ...core.scalars import UUID
from ...core.types.common import CheckoutError

# TODO: Move this DiscountCommonInput to discount model
from ...order.mutations.discount_order import DiscountCommonInput
from ..types import Checkout


class CheckoutShippingDiscountAdd(BaseMutation):
    checkout = graphene.Field(
        Checkout, description="Checkout which has discounted shipping."
    )

    class Arguments:
        token = UUID(description="Checkout token.", required=True)
        input = DiscountCommonInput(
            required=True,
            description="Fields required to create a discount for the checkout.",
        )

    class Meta:
        description = "Adds discount to the checkout shipping."
        permissions = (CheckoutPermissions.MANAGE_CHECKOUTS,)
        error_type_class = CheckoutError
