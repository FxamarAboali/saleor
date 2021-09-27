from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any, List, Optional, Union

from pydantic import BaseModel


class BaseWebhookModel(BaseModel):
    class Config:
        extra = "forbid"


class Address(BaseWebhookModel):
    type: str
    id: str
    first_name: str
    last_name: str
    company_name: Optional[str]
    street_address_1: str
    street_address_2: Optional[str]
    city: str
    city_area: Optional[str]
    postal_code: str
    country: str
    country_area: Optional[str]
    phone: Optional[str]


class Customer(BaseWebhookModel):
    id: str
    default_shipping_address: Optional[Address]
    default_billing_address: Optional[Address]
    addresses: List[Address]
    private_metadata: Any
    metadata: Any
    email: str
    first_name: Optional[str]
    last_name: Optional[str]
    is_active: bool
    date_joined: datetime


class Channel(BaseWebhookModel):
    type: str
    id: str
    slug: str
    currency_code: str


class ShippingMethod(BaseWebhookModel):
    type: str
    id: str
    name: str


class Payment(BaseWebhookModel):
    type: str
    id: str
    gateway: str
    is_active: bool
    created: datetime
    modified: datetime
    charge_status: str
    total: Decimal
    captured_amount: Decimal
    currency: str
    billing_email: str
    billing_first_name: str
    billing_last_name: str
    billing_company_name: Optional[str]
    billing_address_1: str
    billing_address_2: Optional[str]
    billing_city: str
    billing_city_area: Optional[str]
    billing_postal_code: str
    billing_country_code: str
    billing_country_area: Optional[str]
    cc_brand: Optional[str]
    payment_method_type: Optional[str]
    psp_reference: Optional[str]


class OrderLineAllocation(BaseWebhookModel):
    quantity_allocated: int
    warehouse_id: str


class OrderLine(BaseWebhookModel):
    type: str
    id: str
    total_price_net_amount: Decimal
    total_price_gross_amount: Decimal
    allocations: List[OrderLineAllocation]
    product_name: str
    variant_name: str
    translated_product_name: str
    translated_variant_name: str
    product_sku: str
    quantity: int
    currency: str
    unit_discount_amount: Optional[Decimal]
    unit_discount_type: Decimal
    unit_discount_reason: Optional[str]
    unit_price_net_amount: Decimal
    unit_price_gross_amount: Decimal
    undiscounted_unit_price_gross_amount: Decimal
    undiscounted_unit_price_net_amount: Decimal
    undiscounted_total_price_gross_amount: Decimal
    undiscounted_total_price_net_amount: Decimal
    tax_rate: Decimal


class OrderDiscount(BaseWebhookModel):
    type: str
    id: str
    value_type: str
    value: Decimal
    amount_value: Decimal
    name: Optional[str]
    translated_name: Optional[str]
    reason: Optional[str]


class FulfillmentLine(BaseWebhookModel):
    type: str
    id: str
    product_name: str
    variant_name: str
    product_sku: str
    weight: int
    weight_unit: str
    product_type: str
    unit_price_net: Decimal
    unit_price_gross: Decimal
    undiscounted_unit_price_net: Decimal
    undiscounted_unit_price_gross: Decimal
    total_price_net_amount: Decimal
    total_price_gross_amount: Decimal
    currency: str
    warehouse_id: str
    quantity: int


class OrderFulfillment(BaseWebhookModel):
    type: str
    id: str
    lines: List[FulfillmentLine]
    status: str
    tracking_number: Optional[str]
    created: datetime
    shipping_refund_amount: Optional[Decimal]
    total_refund_amount: Optional[Decimal]


class BaseOrder(BaseWebhookModel):
    type: str
    id: str
    private_metadata: Any
    metadata: Any
    created: datetime
    status: str
    user_email: str
    origin: str
    shipping_method_name: str
    shipping_price_net_amount: Decimal
    shipping_price_gross_amount: Decimal
    shipping_tax_rate: Decimal
    total_net_amount: Decimal
    total_gross_amount: Decimal
    undiscounted_total_net_amount: Decimal
    undiscounted_total_gross_amount: Decimal
    weight: str


class Order(BaseOrder):
    channel: Channel
    shipping_method: ShippingMethod
    payments: List[Payment]
    shipping_address: Address
    billing_address: Address
    discounts: List[OrderDiscount]
    original: str
    lines: List[OrderLine]
    fulfillments: List[OrderFulfillment]


class CheckoutUser(BaseWebhookModel):
    type: str
    id: str
    email: str
    first_name: str
    last_name: str


class CheckoutLine(BaseWebhookModel):
    sku: str
    quantity: int
    base_price: str
    currency: str
    full_name: str
    product_name: str
    variant_name: str


class Checkout(BaseWebhookModel):
    type: str
    token: str
    user: CheckoutUser
    billing_address: Address
    shipping_address: Address
    shipping_method: ShippingMethod
    lines: List[CheckoutLine]
    private_metadata: Any
    metadata: Any
    created: datetime
    last_change: datetime
    email: str
    currency: str
    discount_amount: Decimal
    discount_name: Optional[str]


class ProductCollection(BaseWebhookModel):
    type: str
    id: str
    name: str
    slug: str


class ProductCategory(BaseWebhookModel):
    type: str
    id: str
    name: str
    slug: str


class ProductMedia(BaseWebhookModel):
    alt: str
    url: str


class ProductChannelListing(BaseWebhookModel):
    type: str
    id: str
    channel_slug: str
    publication_date: str
    visible_in_listings: bool
    available_for_purchase: str


class ProductAttributeValue(BaseWebhookModel):
    name: str
    slug: str
    value: str
    rich_text: Any
    boolean: Any
    date_time: Any
    date: Any
    reference: Any
    file: Any


class ProductAttribute(BaseWebhookModel):
    name: str
    input_type: str
    slug: str
    entity_type: Any
    unit: Any
    id: str
    values: List[ProductAttributeValue]


class ProductVariantChannelListing(BaseWebhookModel):
    type: str
    id: str
    channel_slug: str
    currency: str
    price_amount: str
    cost_price_amount: str


class ProductVariant(BaseWebhookModel):
    type: str
    id: str
    attributes: List[ProductAttribute]
    product_id: str
    media: List[ProductMedia]
    channel_listings: List[ProductVariantChannelListing]
    private_metadata: Any
    metadata: Any
    sku: str
    name: str
    track_inventory: bool


class Block(BaseWebhookModel):
    data: Any
    type: str


class Content(BaseWebhookModel):
    time: int
    blocks: List[Block]
    version: str


class ProductDeleted(BaseWebhookModel):
    type: str
    id: str
    variants: List[str]
    private_metadata: Any
    metadata: Any
    name: str
    description: Content
    updated_at: datetime
    charge_taxes: bool
    weight: str


class Product(BaseWebhookModel):
    type: str
    id: str
    category: ProductCategory
    collections: List[ProductCollection]
    attributes: List[ProductAttribute]
    media: List[ProductMedia]
    channel_listings: List[ProductChannelListing]
    variants: List[ProductVariant]
    private_metadata: Any
    metadata: Any
    name: str
    description: Content
    updated_at: datetime
    charge_taxes: bool
    weight: str


class FulfillmentCreated(BaseWebhookModel):
    type: str
    id: str
    warehouse_address: Address
    order: Order
    lines: List[FulfillmentLine]
    status: str
    shipping_refund_amount: Optional[Decimal]
    total_refund_amount: Optional[Decimal]


class Page(BaseWebhookModel):
    type: str
    id: str
    publication_date: str
    is_published: bool
    private_metadata: Any
    metadata: Any
    title: str
    content: Content


class TranslationKey(BaseWebhookModel):
    key: str
    value: Union[str, Content]


class Translation(BaseWebhookModel):
    id: str
    language_code: str
    type: str
    keys: List[TranslationKey]


class Invoice(BaseWebhookModel):
    type: str
    id: str
    order: BaseOrder
    number: Optional[str]
    created: Optional[datetime]
    external_url: Optional[str]


class SyncPayment(BaseWebhookModel):
    gateway: str
    amount: str
    currency: str
    billing: Address
    shipping: Address
    payment_id: int
    graphql_payment_id: str
    order_id: int
    customer_ip_address: str
    customer_email: str
    token: Optional[str]
    customer_id: Optional[str]
    reuse_source: bool
    data: Any
    graphql_customer_id: Optional[str]
    payment_method: str


class CustomerCreated(Customer):
    ...


class CustomerUpdated(Customer):
    ...


class OrderCreated(Order):
    ...


class OrderConfirmed(Order):
    ...


class OrderFullyPaid(Order):
    ...


class OrderUpdated(Order):
    ...


class OrderCancelled(Order):
    ...


class OrderFulfilled(Order):
    ...


class CheckoutCreated(Checkout):
    ...


class CheckoutUpdated(Checkout):
    ...


class ProductCreated(Product):
    ...


class ProductUpdated(Product):
    ...


class ProductVariantCreated(ProductVariant):
    ...


class ProductVariantUpdated(ProductVariant):
    ...


class ProductVariantDeleted(ProductVariant):
    ...


class PageCreated(Page):
    ...


class PageUpdated(Page):
    ...


class PageDeleted(Page):
    ...


class TranslationCreated(Translation):
    ...


class TranslationUpdated(Translation):
    ...


class InvoiceRequested(Invoice):
    ...


class InvoiceDeleted(Invoice):
    ...


class InvoiceSent(Invoice):
    ...


class PaymentListGateways(BaseWebhookModel):
    checkout: Checkout
    currency: str


class PaymentAuthorize(SyncPayment):
    ...


class PaymentCapture(SyncPayment):
    ...


class PaymentRefund(SyncPayment):
    ...


class PaymentVoid(SyncPayment):
    ...


class PaymentConfirm(SyncPayment):
    ...


class PaymentProcess(SyncPayment):
    ...


class WebhookSchema(BaseModel):
    __root__: Union[
        List[
            Union[
                FulfillmentCreated,
                CheckoutCreated,
                CheckoutUpdated,
                CustomerCreated,
                CustomerUpdated,
                InvoiceDeleted,
                InvoiceRequested,
                InvoiceSent,
                PageCreated,
                PageDeleted,
                PageUpdated,
                ProductCreated,
                ProductDeleted,
                ProductUpdated,
                ProductVariantCreated,
                ProductVariantDeleted,
                ProductVariantUpdated,
                OrderCancelled,
                OrderConfirmed,
                OrderCreated,
                OrderFulfilled,
                OrderFullyPaid,
                OrderUpdated,
            ]
        ],
        PaymentAuthorize,
        PaymentCapture,
        PaymentConfirm,
        PaymentListGateways,
        PaymentProcess,
        PaymentRefund,
        PaymentVoid,
        TranslationCreated,
        TranslationUpdated,
    ]
