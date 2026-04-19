from __future__ import annotations

from typing import Any, Dict, List

from breeze_connect import BreezeConnect


class BreezeClient:
    """
    Thin wrapper around BreezeConnect.
    This layer should only do API/session/fetching.
    """

    def __init__(self, api_key: str, api_secret: str, session_token: str) -> None:
        self.client = BreezeConnect(api_key=api_key)
        self.client.generate_session(
            api_secret=api_secret,
            session_token=session_token,
        )

    def get_positions(self) -> List[Dict[str, Any]]:
        """
        Returns the raw positions payload list.
        """
        response = self.client.get_portfolio_positions()
        return response.get("Success", []) or []

    def get_trades(self, from_date: str, to_date: str) -> List[Dict[str, Any]]:
        """
        Returns the raw trade list payload.
        Date format depends on Breeze expectations for your account setup.
        """
        response = self.client.get_trade_list(
            from_date=from_date,
            to_date=to_date,
        )
        return response.get("Success", []) or []
