import graphene
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from ...core.permissions import AppPermission, AuthorizationFilters
from ...webhook import models
from ...webhook.error_codes import WebhookDryRunErrorCode, WebhookErrorCode
from ...webhook.event_types import WebhookEventAsyncType
from ..app.dataloaders import get_app_promise
from ..core.descriptions import ADDED_IN_32, DEPRECATED_IN_3X_INPUT, PREVIEW_FEATURE
from ..core.fields import JSONString
from ..core.mutations import BaseMutation, ModelDeleteMutation, ModelMutation
from ..core.types import NonNullList, WebhookDryRunError, WebhookError
from ..core.utils import raise_validation_error
from ..plugins.dataloaders import get_plugin_manager_promise
from . import enums
from .subscription_payload import (
    generate_payload_from_subscription,
    initialize_request,
    validate_query,
)
from .types import EventDelivery, Webhook
from .utils import get_event_type_from_subscription


class WebhookCreateInput(graphene.InputObjectType):
    name = graphene.String(description="The name of the webhook.", required=False)
    target_url = graphene.String(description="The url to receive the payload.")
    events = NonNullList(
        enums.WebhookEventTypeEnum,
        description=(
            f"The events that webhook wants to subscribe. {DEPRECATED_IN_3X_INPUT} "
            "Use `asyncEvents` or `syncEvents` instead."
        ),
    )
    async_events = NonNullList(
        enums.WebhookEventTypeAsyncEnum,
        description="The asynchronous events that webhook wants to subscribe.",
    )
    sync_events = NonNullList(
        enums.WebhookEventTypeSyncEnum,
        description="The synchronous events that webhook wants to subscribe.",
    )
    app = graphene.ID(
        required=False,
        description="ID of the app to which webhook belongs.",
    )
    is_active = graphene.Boolean(
        description="Determine if webhook will be set active or not.", required=False
    )
    secret_key = graphene.String(
        description="The secret key used to create a hash signature with each payload."
        f"{DEPRECATED_IN_3X_INPUT} As of Saleor 3.5, webhook payloads default to "
        "signing using a verifiable JWS.",
        required=False,
    )
    query = graphene.String(
        description="Subscription query used to define a webhook payload."
        + ADDED_IN_32
        + PREVIEW_FEATURE,
        required=False,
    )


def clean_webhook_events(_info, _instance, data):
    # if `events` field is not empty, use this field. Otherwise get event types
    # from `async_events` and `sync_events`.
    events = data.get("events", [])
    if not events:
        events += data.pop("async_events", [])
        events += data.pop("sync_events", [])
    data["events"] = events
    return data


class WebhookCreate(ModelMutation):
    class Arguments:
        input = WebhookCreateInput(
            description="Fields required to create a webhook.", required=True
        )

    class Meta:
        description = "Creates a new webhook subscription."
        model = models.Webhook
        object_type = Webhook
        permissions = (
            AppPermission.MANAGE_APPS,
            AuthorizationFilters.AUTHENTICATED_APP,
        )
        error_type_class = WebhookError
        error_type_field = "webhook_errors"

    @classmethod
    def clean_input(cls, info, instance, data):
        cleaned_data = super().clean_input(info, instance, data)
        app = cleaned_data.get("app")

        # We are not able to check it in `check_permission`.
        # We need to confirm that cleaned_data has app_id or
        # context has assigned app instance
        if not instance.app_id and not app:
            raise ValidationError("Missing token or app", code=WebhookErrorCode.INVALID)

        if instance.app_id:
            # Let's skip app id in case when context has
            # app instance
            app = instance.app
            cleaned_data.pop("app", None)

        if not app or not app.is_active:
            raise ValidationError(
                "App doesn't exist or is disabled",
                code=WebhookErrorCode.NOT_FOUND,
            )
        clean_webhook_events(info, instance, cleaned_data)
        if query := cleaned_data.get("query"):
            validate_query(query)
            instance.subscription_query = query
        return cleaned_data

    @classmethod
    def get_instance(cls, info, **data):
        instance = super().get_instance(info, **data)
        app = get_app_promise(info.context).get()
        instance.app = app
        return instance

    @classmethod
    def save(cls, info, instance, cleaned_input):
        instance.save()
        events = set(cleaned_input.get("events", []))
        models.WebhookEvent.objects.bulk_create(
            [
                models.WebhookEvent(webhook=instance, event_type=event)
                for event in events
            ]
        )


class WebhookUpdateInput(graphene.InputObjectType):
    name = graphene.String(description="The new name of the webhook.", required=False)
    target_url = graphene.String(
        description="The url to receive the payload.", required=False
    )
    events = NonNullList(
        enums.WebhookEventTypeEnum,
        description=(
            f"The events that webhook wants to subscribe. {DEPRECATED_IN_3X_INPUT} "
            "Use `asyncEvents` or `syncEvents` instead."
        ),
        required=False,
    )
    async_events = NonNullList(
        enums.WebhookEventTypeAsyncEnum,
        description="The asynchronous events that webhook wants to subscribe.",
        required=False,
    )
    sync_events = NonNullList(
        enums.WebhookEventTypeSyncEnum,
        description="The synchronous events that webhook wants to subscribe.",
        required=False,
    )
    app = graphene.ID(
        required=False,
        description="ID of the app to which webhook belongs.",
    )
    is_active = graphene.Boolean(
        description="Determine if webhook will be set active or not.", required=False
    )
    secret_key = graphene.String(
        description="Use to create a hash signature with each payload."
        f"{DEPRECATED_IN_3X_INPUT} As of Saleor 3.5, webhook payloads default to "
        "signing using a verifiable JWS.",
        required=False,
    )
    query = graphene.String(
        description="Subscription query used to define a webhook payload."
        + ADDED_IN_32
        + PREVIEW_FEATURE,
        required=False,
    )


class WebhookUpdate(ModelMutation):
    class Arguments:
        id = graphene.ID(required=True, description="ID of a webhook to update.")
        input = WebhookUpdateInput(
            description="Fields required to update a webhook.", required=True
        )

    class Meta:
        description = "Updates a webhook subscription."
        model = models.Webhook
        object_type = Webhook
        permissions = (AppPermission.MANAGE_APPS,)
        error_type_class = WebhookError
        error_type_field = "webhook_errors"

    @classmethod
    def clean_input(cls, info, instance, data):
        cleaned_data = super().clean_input(info, instance, data)
        app = cleaned_data.get("app")

        if not instance.app_id and not app:
            raise ValidationError("Missing token or app", code=WebhookErrorCode.INVALID)

        if instance.app_id:
            # Let's skip app id in case when context has
            # app instance
            app = instance.app
            cleaned_data.pop("app", None)

        if not app or not app.is_active:
            raise ValidationError(
                "App doesn't exist or is disabled",
                code=WebhookErrorCode.NOT_FOUND,
            )
        clean_webhook_events(info, instance, cleaned_data)

        if query := cleaned_data.get("query"):
            validate_query(query)
            instance.subscription_query = query
        return cleaned_data

    @classmethod
    def save(cls, info, instance, cleaned_input):
        instance.save()
        events = set(cleaned_input.get("events", []))
        if events:
            instance.events.all().delete()
            models.WebhookEvent.objects.bulk_create(
                [
                    models.WebhookEvent(webhook=instance, event_type=event)
                    for event in events
                ]
            )


class WebhookDelete(ModelDeleteMutation):
    class Arguments:
        id = graphene.ID(required=True, description="ID of a webhook to delete.")

    class Meta:
        description = (
            "Delete a webhook. Before the deletion, the webhook is deactivated to "
            "pause any deliveries that are already scheduled. The deletion might fail "
            "if delivery is in progress. In such a case, the webhook is not deleted "
            "but remains deactivated."
        )
        model = models.Webhook
        object_type = Webhook
        permissions = (
            AppPermission.MANAGE_APPS,
            AuthorizationFilters.AUTHENTICATED_APP,
        )
        error_type_class = WebhookError
        error_type_field = "webhook_errors"

    @classmethod
    def perform_mutation(cls, _root, info, **data):
        app = get_app_promise(info.context).get()
        node_id = data.get("id")
        if app and not app.is_active:
            raise ValidationError(
                "App needs to be active to delete webhook",
                code=WebhookErrorCode.INVALID,
            )
        webhook = cls.get_node_or_error(info, node_id, only_type=Webhook)
        if app and webhook.app_id != app.id:
            raise ValidationError(
                f"Couldn't resolve to a node: {node_id}",
                code=WebhookErrorCode.GRAPHQL_ERROR,
            )
        webhook.is_active = False
        webhook.save(update_fields=["is_active"])

        try:
            response = super().perform_mutation(_root, info, **data)
        except IntegrityError:
            raise ValidationError(
                "Webhook couldn't be deleted at this time due to running task."
                "Webhook deactivated. Try deleting Webhook later",
                code=WebhookErrorCode.DELETE_FAILED,
            )

        return response


class EventDeliveryRetry(BaseMutation):
    delivery = graphene.Field(EventDelivery, description="Event delivery.")

    class Arguments:
        id = graphene.ID(
            required=True, description="ID of the event delivery to retry."
        )

    class Meta:
        description = "Retries event delivery."
        permissions = (AppPermission.MANAGE_APPS,)
        error_type_class = WebhookError

    @classmethod
    def perform_mutation(cls, _root, info, **data):
        delivery = cls.get_node_or_error(
            info,
            data["id"],
            only_type=EventDelivery,
        )
        manager = get_plugin_manager_promise(info.context).get()
        manager.event_delivery_retry(delivery)
        return EventDeliveryRetry(delivery=delivery)


class WebhookDryRunInput(graphene.InputObjectType):
    object_id = graphene.ID(
        description="The ID of an object to serialize.", required=True
    )
    query = graphene.String(
        description="The subscription query that defines the webhook event and its "
        "payload.",
        required=True,
    )


class WebhookDryRun(BaseMutation):
    payload = JSONString(
        description="JSON payload, that would be sent out to webhook's target URL."
    )

    class Arguments:
        id = graphene.ID(description="The ID of the webhook.", required=True)
        input = WebhookDryRunInput(
            description="Fields required to perform dry run of a webhook event.",
            required=True,
        )

    class Meta:
        description = "Performs a dry run of a webhook event."
        permissions = (AppPermission.MANAGE_APPS,)
        error_type_class = WebhookDryRunError

    @classmethod
    def validate_input(cls, info, **data):
        query = data.get("input", {}).get("query")
        object_id = data.get("input", {}).get("object_id")
        webhook_id = data.get("id")

        event_type = get_event_type_from_subscription(query)
        if not event_type:
            raise_validation_error(
                field="query",
                message="Can't parse an event type from query.",
                code=WebhookDryRunErrorCode.GRAPHQL_ERROR,
            )

        # TODO check if object_id match event_type
        # if ... :
        #     raise_validation_error(
        #         field="objectId",
        #         message="ObjectId doesn't match event type.",
        #         code=WebhookDryRunErrorCode.INVALID_ID,
        #     )

        object = cls.get_node_or_error(info, object_id, field="objectId")
        webhook = cls.get_node_or_error(info, webhook_id, field="id")
        app = webhook.app

        if permission := WebhookEventAsyncType.PERMISSIONS.get(event_type):
            codename = permission.value.split(".")[1]
            app_permissions = [perm.codename for perm in app.permissions.all()]
            if codename not in app_permissions:
                raise_validation_error(
                    message=f"The app doesn't have required permission: {codename}.",
                    code=WebhookDryRunErrorCode.MISSING_APP_PERMISSION,
                )

        return event_type, object, app, query

    @classmethod
    def perform_mutation(cls, _root, info, **data):
        event_type, object, app, query = cls.validate_input(info, **data)

        payload = None
        if all([event_type, object, app, query]):
            request = initialize_request()
            payload = generate_payload_from_subscription(
                event_type, object, query, request, app
            )

        return WebhookDryRun(payload=payload)
