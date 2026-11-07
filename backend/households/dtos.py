"""JSON response shapes for household data."""

from collections.abc import Iterable
from typing import TypedDict

from .models import Household, HouseholdMember


class HouseholdMemberDTO(TypedDict):
    member_id: int
    household_id: int
    first_name: str
    last_name: str
    date_of_birth: str
    phone_number: str | None
    is_account_holder: bool


class HouseholdDTO(TypedDict):
    household_id: int
    street: str
    city: str
    province: str
    postal_code: str
    zone_id: int
    zone_name: str
    members: list[HouseholdMemberDTO]


def member_to_dto(member: HouseholdMember) -> HouseholdMemberDTO:
    return {
        "member_id": member.pk,
        "household_id": member.household.pk,
        "first_name": member.first_name,
        "last_name": member.last_name,
        "date_of_birth": member.date_of_birth.isoformat(),
        "phone_number": member.phone_number,
        "is_account_holder": hasattr(member, "account_holder"),
    }


def household_to_dto(
    household: Household,
    members: Iterable[HouseholdMember],
) -> HouseholdDTO:
    return {
        "household_id": household.pk,
        "street": household.street,
        "city": household.city,
        "province": household.province,
        "postal_code": household.postal_code,
        "zone_id": household.zone.pk,
        "zone_name": household.zone.zone_name,
        "members": [member_to_dto(member) for member in members],
    }
