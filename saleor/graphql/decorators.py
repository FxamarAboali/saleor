from enum import Enum
from functools import wraps
from typing import Iterable, Union

from graphql.execution.base import ResolveInfo

from .utils import get_user_or_app_from_context
from ..attribute import AttributeType
from ..core.exceptions import PermissionDenied
from ..core.permissions import AccountPermissions, PagePermissions, ProductPermissions, \
    has_one_of_permissions

from ..core.permissions import permission_required as core_permission_required


def context(f):
    def decorator(func):
        def wrapper(*args, **kwargs):
            info = next(arg for arg in args if isinstance(arg, ResolveInfo))
            return func(info.context, *args, **kwargs)

        return wrapper

    return decorator


def account_passes_test(test_func):
    """Determine if user/app has permission to access to content."""

    def decorator(f):
        @wraps(f)
        @context(f)
        def wrapper(context, *args, **kwargs):
            if test_func(context):
                return f(*args, **kwargs)
            raise PermissionDenied()

        return wrapper

    return decorator


def account_passes_test_for_attribute(test_func):
    """Determine if user/app has permission to access to content."""

    def decorator(f):
        @wraps(f)
        @context(f)
        def wrapper(context, *args, **kwargs):
            root = args[0]
            if test_func(context, root):
                return f(*args, **kwargs)
            raise PermissionDenied()

        return wrapper

    return decorator


def _permission_required(perms: Iterable[Enum], context):
    if context.user.has_perms(perms):
        return True
    app = getattr(context, "app", None)
    if app:
        # for now MANAGE_STAFF permission for app is not supported
        if AccountPermissions.MANAGE_STAFF in perms:
            return False
        return app.has_perms(perms)
    return False


# def permission_required(perm: Union[Enum, Iterable[Enum]]):
#     def check_perms(context):
#         if isinstance(perm, Enum):
#             perms = (perm,)
#         else:
#             perms = perm
#
#         requestor = get_user_or_app_from_context(context)
#         return core_permission_required(perms, requestor)
#
#     return account_passes_test(check_perms)

def permission_required(perm: Union[Enum, Iterable[Enum]]):
    def check_perms(context):
        if isinstance(perm, Enum):
            perms = (perm,)
        else:
            perms = perm
        return _permission_required(perms, context)

    return account_passes_test(check_perms)


def one_of_permissions_required(perms: Iterable[Enum]):
    def check_perms(context):
        requestor = get_user_or_app_from_context(context)
        has_one_of_permissions(requestor, perms)

    return account_passes_test(check_perms)


staff_member_required = account_passes_test(
    lambda context: context.user.is_active and context.user.is_staff
)


staff_member_or_app_required = account_passes_test(
    lambda context: context.app or (context.user.is_active and context.user.is_staff)
)


def check_attribute_required_permissions():
    """Check attribute permissions that depend on attribute type.

    As an attribute can belong to the product or to the page,
    different permissions need to be checked.
    """

    def check_perms(context, attribute):
        requestor = get_user_or_app_from_context(context)
        if attribute.type == AttributeType.PAGE_TYPE:
            return core_permission_required((PagePermissions.MANAGE_PAGES,), requestor)
        return core_permission_required((ProductPermissions.MANAGE_PRODUCTS,), requestor)

    return account_passes_test_for_attribute(check_perms)
