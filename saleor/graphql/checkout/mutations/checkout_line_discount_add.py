import graphene

from ....core.permissions import CheckoutPermissions
from ...core.mutations import BaseMutation
from ...core.types.common import CheckoutError

# TODO: Move this DiscountCommonInput to discount model
from ...order.mutations.discount_order import DiscountCommonInput
from ..types import Checkout, CheckoutLine


class CheckoutLineDiscountAdd(BaseMutation):
    checkout_line = graphene.Field(
        CheckoutLine, description="Checkout line which has been discounted."
    )
    checkout = graphene.Field(
        Checkout, description="Checkout which has been discounted."
    )

    class Arguments:
        checkout_line_id = graphene.ID(
            description="ID of a checkout line to add discount.", required=True
        )
        input = DiscountCommonInput(
            required=True,
            description="Fields required to create a discount for the checkout line.",
        )

    class Meta:
        description = "Adds discount to the checkout line."
        permissions = (CheckoutPermissions.MANAGE_CHECKOUTS,)
        error_type_class = CheckoutError
