import datetime
from decimal import Decimal

import pytest
import pytz

from .....payment import TransactionAction, TransactionEventStatus
from .....payment.error_codes import TransactionRequestCompleteErrorCode
from .....payment.models import TransactionEvent, TransactionItem
from ....tests.utils import get_graphql_content, get_graphql_content_from_response

MUTATION_TRANSACTION_EVENT_REPORT = """
mutation TransactionEventReport(
    $transaction_id: ID,
    $original_psp_reference: String,
    $psp_reference: String!,
    $result: TransactionEventReportResult!,
    $type: TransactionEventActionTypeEnum!,
    $amount: PositiveDecimal!,
    $time: DateTime,
    $external_url: String,
    $name: String,
    $available_actions: [TransactionActionEnum!]
    ){
    transactionEventReport(
            transactionId: $transaction_id,
            originalPspReference: $original_psp_reference,
            pspReference: $psp_reference,
            result: $result,
            type: $type,
            amount: $amount,
            time: $time,
            externalUrl: $external_url,
            name: $name,
            availableActions: $available_actions
        ){
        alreadyProcessed
        transaction{
            id
            actions
            reference
            pspReference
            type
            status
            modifiedAt
            createdAt
            authorizedAmount{
                amount
                currency
            }
            voidedAmount{
                currency
                amount
            }
            chargedAmount{
                currency
                amount
            }
            refundedAmount{
                currency
                amount
            }
        }
        errors{
            field
            message
            code
        }
    }
}
"""


@pytest.fixture
def transaction_item():
    return TransactionItem.objects.create(
        status="Authorized",
        type="Credit card",
        psp_reference="PSP ref",
        currency="USD",
        authorized_value=Decimal("10"),
        charged_value=Decimal("10"),
        pending_refund_value=Decimal("10"),
        refunded_value=Decimal("10"),
    )


@pytest.fixture
def transaction_event_refund(transaction_item):
    return TransactionEvent.objects.create(
        transaction=transaction_item,
        amount_value=10,
        psp_reference="event_ref",
        status=TransactionEventStatus.REQUEST,
        type=TransactionAction.REFUND,
    )


@pytest.mark.parametrize(
    "refund_amount, new_refunded_value, new_charged_value",
    [
        ("0", Decimal("10.00"), Decimal("10.00")),
        ("5", Decimal("15.00"), Decimal("5.00")),
        ("10.00", Decimal("20.00"), Decimal("0.00")),
        ("15.00", Decimal("25.00"), Decimal("-5.00")),
    ],
)
def test_transaction_event_report_refund(
    refund_amount,
    new_charged_value,
    new_refunded_value,
    app_api_client,
    permission_manage_payments,
    transaction_item,
):
    # given
    variables = {
        "original_psp_reference": "PSP ref",
        "psp_reference": "new ref",
        "result": "SUCCESS",
        "type": "REFUND",
        "amount": refund_amount,
    }

    # when
    response = app_api_client.post_graphql(
        MUTATION_TRANSACTION_EVENT_REPORT,
        variables,
        permissions=[permission_manage_payments],
    )

    # then
    content = get_graphql_content(response)
    returned_transaction = content["data"]["transactionEventReport"]["transaction"]

    assert returned_transaction["pspReference"] == "PSP ref"
    assert returned_transaction["chargedAmount"]["amount"] == new_charged_value
    assert returned_transaction["refundedAmount"]["amount"] == new_refunded_value

    new_pending_value = new_charged_value
    assert TransactionItem.objects.get(
        id=transaction_item.id, pending_refund_value=new_pending_value
    )

    assert TransactionEvent.objects.get(
        transaction=transaction_item,
        status=TransactionEventStatus.SUCCESS,
        type=TransactionAction.REFUND,
        amount_value=refund_amount,
    )


@pytest.mark.parametrize(
    "charged_amount, new_charged_value, new_authorized_value",
    [
        ("0", Decimal("10.00"), Decimal("10.00")),
        ("5", Decimal("15.00"), Decimal("5.00")),
        ("10.00", Decimal("20.00"), Decimal("0.00")),
        ("15.00", Decimal("25.00"), Decimal("-5.00")),
    ],
)
def test_transaction_event_report_charge(
    charged_amount,
    new_charged_value,
    new_authorized_value,
    app_api_client,
    permission_manage_payments,
    transaction_item,
):
    # given
    variables = {
        "original_psp_reference": "PSP ref",
        "psp_reference": "new ref",
        "result": "SUCCESS",
        "type": "CHARGE",
        "amount": charged_amount,
    }

    # when
    response = app_api_client.post_graphql(
        MUTATION_TRANSACTION_EVENT_REPORT,
        variables,
        permissions=[permission_manage_payments],
    )

    # then
    content = get_graphql_content(response)
    returned_transaction = content["data"]["transactionEventReport"]["transaction"]

    assert returned_transaction["pspReference"] == "PSP ref"
    assert returned_transaction["chargedAmount"]["amount"] == new_charged_value
    assert returned_transaction["authorizedAmount"]["amount"] == new_authorized_value
    assert TransactionEvent.objects.get(
        transaction=transaction_item,
        status=TransactionEventStatus.SUCCESS,
        type=TransactionAction.CHARGE,
        amount_value=charged_amount,
    )


@pytest.mark.parametrize(
    "voided_amount, new_voided_value",
    [
        ("0", Decimal("0.00")),
        ("5", Decimal("5.00")),
    ],
)
def test_transaction_event_report_cancel(
    voided_amount,
    new_voided_value,
    app_api_client,
    permission_manage_payments,
    transaction_item,
):
    # given
    variables = {
        "original_psp_reference": "PSP ref",
        "psp_reference": "new ref",
        "result": "SUCCESS",
        "type": "CANCEL",
        "amount": voided_amount,
    }

    # when
    response = app_api_client.post_graphql(
        MUTATION_TRANSACTION_EVENT_REPORT,
        variables,
        permissions=[permission_manage_payments],
    )

    # then
    content = get_graphql_content(response)
    returned_transaction = content["data"]["transactionEventReport"]["transaction"]

    assert returned_transaction["pspReference"] == "PSP ref"
    assert returned_transaction["voidedAmount"]["amount"] == new_voided_value
    assert returned_transaction["authorizedAmount"]["amount"] == 0
    assert TransactionEvent.objects.get(
        transaction=transaction_item,
        status=TransactionEventStatus.SUCCESS,
        type=TransactionAction.CANCEL,
        amount_value=voided_amount,
    )


@pytest.mark.parametrize(
    "refund_amount, new_pending_value",
    [
        ("0.00", Decimal("0.00")),
        ("10.00", Decimal("0.00")),
        ("15.00", Decimal("-5.00")),
    ],
)
def test_transaction_event_report_pending_refund_requested(
    refund_amount,
    new_pending_value,
    app_api_client,
    permission_manage_payments,
    transaction_item,
    transaction_event_refund,
):
    # given
    variables = {
        "original_psp_reference": "PSP ref",
        "psp_reference": transaction_event_refund.psp_reference,
        "result": "SUCCESS",
        "type": "REFUND",
        "amount": refund_amount,
    }

    # when
    response = app_api_client.post_graphql(
        MUTATION_TRANSACTION_EVENT_REPORT,
        variables,
        permissions=[permission_manage_payments],
    )

    # then
    get_graphql_content(response)

    assert TransactionItem.objects.get(
        id=transaction_item.id, pending_refund_value=new_pending_value
    )

    assert TransactionEvent.objects.get(
        transaction=transaction_item,
        status=TransactionEventStatus.SUCCESS,
        type=TransactionAction.REFUND,
        amount_value=refund_amount,
    )


def test_transaction_event_correctly_filled_fields(
    app_api_client,
    permission_manage_payments,
    transaction_item,
):
    # given
    variables = {
        "original_psp_reference": "PSP ref",
        "psp_reference": "new ref",
        "result": "SUCCESS",
        "type": "REFUND",
        "amount": 10,
        "time": "2001-01-01T00:00:00+00:00",
        "name": "name",
    }

    # when
    response = app_api_client.post_graphql(
        MUTATION_TRANSACTION_EVENT_REPORT,
        variables,
        permissions=[permission_manage_payments],
    )

    # then
    get_graphql_content(response)
    datetime.datetime(2001, 1, 1, tzinfo=pytz.UTC)

    assert TransactionEvent.objects.get(
        transaction=transaction_item,
        status=TransactionEventStatus.SUCCESS,
        type=TransactionAction.REFUND,
        amount_value=10,
        psp_reference="new ref",
        name="name",
    )


def test_transaction_event_incorrect_data(
    app_api_client,
    permission_manage_payments,
    transaction_item,
):
    # given
    variables1 = {
        "original_psp_reference": "PSP ref",
        "psp_reference": "new ref",
        "result": "SUCCESS",
        "type": "REFUND",
        "amount": 10,
    }

    variables2 = variables1
    variables2["result"] = "FAILURE"

    app_api_client.post_graphql(
        MUTATION_TRANSACTION_EVENT_REPORT,
        variables1,
        permissions=[permission_manage_payments],
    )

    response = app_api_client.post_graphql(
        MUTATION_TRANSACTION_EVENT_REPORT,
        variables2,
        permissions=[permission_manage_payments],
    )

    # then
    content = get_graphql_content_from_response(response)
    assert "errors" in content
    assert (
        content["errors"][0]["code"]
        == TransactionRequestCompleteErrorCode.INCORRECT_DETAILS
    )
