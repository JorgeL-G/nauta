"""Enums for financial transaction models"""
from enum import Enum


class Currency(str, Enum):
    """Supported currencies for financial transactions"""
    USD = "USD"
    EUR = "EUR"
    MXN = "MXN"
    GBP = "GBP"
    JPY = "JPY"
    CAD = "CAD"
    AUD = "AUD"
    CHF = "CHF"
    CNY = "CNY"
    BRL = "BRL"

