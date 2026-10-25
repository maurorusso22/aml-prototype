"""Customer master data (KYC profile) for individuals and businesses."""

from datetime import date
from typing import Annotated, Literal, Self

from pydantic import Field, model_validator

from .base import DomainModel
from .enums import CustomerKind, RiskRating
from .formats import CountryCode, CustomerId, NonEmptyStr, NonNegativeMoney, TaxCode, VatNumber


class Address(DomainModel):
    """Postal address."""

    street: NonEmptyStr = Field(description="Street name and number.")
    city: NonEmptyStr = Field(description="City or municipality.")
    postal_code: NonEmptyStr = Field(description="Postal code.")
    country: CountryCode = Field(description="ISO 3166-1 alpha-2 country code.")


class CustomerBase(DomainModel):
    """Fields shared by every kind of customer."""

    customer_id: CustomerId = Field(description="Customer identifier.")
    residence: Address = Field(description="Residence, or registered office for businesses.")
    risk_rating: RiskRating = Field(description="Rating assigned by customer due diligence.")
    onboarding_date: date = Field(description="Start of the customer relationship.")


class IndividualCustomer(CustomerBase):
    """A customer who is a natural person."""

    kind: Literal[CustomerKind.INDIVIDUAL] = Field(description="Customer kind discriminator.")
    first_name: NonEmptyStr = Field(description="Given name.")
    last_name: NonEmptyStr = Field(description="Family name.")
    birth_date: date = Field(description="Date of birth.")
    nationality: CountryCode = Field(description="ISO 3166-1 alpha-2 country code.")
    tax_code: TaxCode = Field(description="Personal tax code (codice fiscale).")
    occupation: NonEmptyStr = Field(description="Declared occupation.")
    declared_annual_income: NonNegativeMoney = Field(
        description="Annual income declared at onboarding, in EUR."
    )

    @model_validator(mode="after")
    def check_dates(self) -> Self:
        """Reject customers onboarded before they were born.

        Returns:
            The validated customer.
        """
        if self.birth_date >= self.onboarding_date:
            raise ValueError("birth_date must precede onboarding_date")
        return self


class BusinessCustomer(CustomerBase):
    """A customer that is a company or a sole trader."""

    kind: Literal[CustomerKind.BUSINESS] = Field(description="Customer kind discriminator.")
    legal_name: NonEmptyStr = Field(description="Registered business name.")
    legal_form: NonEmptyStr = Field(description="Legal form, e.g. SRL, SPA, sole trader.")
    sector: NonEmptyStr = Field(description="Main economic activity.")
    vat_number: VatNumber = Field(description="VAT number (partita IVA).")
    incorporation_date: date = Field(description="Date the business was registered.")
    declared_annual_turnover: NonNegativeMoney = Field(
        description="Annual turnover declared at onboarding, in EUR."
    )

    @model_validator(mode="after")
    def check_dates(self) -> Self:
        """Reject businesses onboarded before they were incorporated.

        Returns:
            The validated customer.
        """
        if self.incorporation_date > self.onboarding_date:
            raise ValueError("incorporation_date must not follow onboarding_date")
        return self


Customer = Annotated[IndividualCustomer | BusinessCustomer, Field(discriminator="kind")]
