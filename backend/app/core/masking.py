"""Data masking utilities for sensitive information."""


def mask_phone(phone: str | None) -> str | None:
    """
    Mask phone number for consultant role.
    Example: 13812345678 -> 138****5678
    """
    if not phone:
        return phone
    if len(phone) < 7:
        return phone
    return phone[:3] + "****" + phone[-4:]


def mask_wechat(wechat: str | None) -> str | None:
    """
    Mask WeChat ID for consultant role.
    Example: wechat123 -> we****23
    """
    if not wechat:
        return wechat
    if len(wechat) < 4:
        return wechat
    return wechat[:2] + "****" + wechat[-2:]
