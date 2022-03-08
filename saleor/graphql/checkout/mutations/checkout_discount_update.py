import graphene

from ....core.permissions import CheckoutPermissions
from ...core.mutations import BaseMutation
from ...core.types.common import CheckoutError

# TODO: Move this DiscountCommonInput to discount model
from ...order.mutations.discount_order import DiscountCommonInput
from ..types import Checkout


class CheckoutDiscountUpdate(BaseMutation):
    checkout = graphene.Field(
        Checkout, description="Checkout which has been discounted."
    )

    class Arguments:
        discount_id = graphene.ID(
            description="ID of a discount to update.", required=True
        )
        input = DiscountCommonInput(
            required=True,
            description="Fields required to update a discount for the checkout.",
        )

    class Meta:
        description = "Update discount to the checkout."
        permissions = (CheckoutPermissions.MANAGE_CHECKOUTS,)
        error_type_class = CheckoutError
