import graphene

from ....core.permissions import CheckoutPermissions
from ...core.mutations import BaseMutation
from ...core.types.common import CheckoutError

# TODO: Move this DiscountCommonInput to discount model
from ...order.mutations.discount_order import DiscountCommonInput
from ..types import Checkout


class CheckoutDiscountAdd(BaseMutation):
    checkout = graphene.Field(
        Checkout, description="Checkout which has been discounted."
    )

    class Arguments:
        checkout_id = graphene.ID(required=True, description="The ID of the checkout.")
        input = DiscountCommonInput(
            required=True,
            description="Fields required to create a discount for the checkout.",
        )

    class Meta:
        description = "Adds discount to the checkout."
        permissions = (CheckoutPermissions.MANAGE_CHECKOUTS,)
        error_type_class = CheckoutError
