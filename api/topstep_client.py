from api.http_base import HttpBase
from api.orders import OrdersService
from api.accounts import AccountsService
from api.flatten import FlattenService


class TopstepXClient:
    """
    Façade simple & stable pour le reste du bot.
    - conserve execute_trade(...)
    - délègue aux services spécialisés (Orders/Accounts/Flatten)
    """
    def __init__(
        self,
        api_key,
        base_url,
        username,
        account_id,
        endpoints=None,
        logging_enabled=True,
        contract_id=None,
        default_order_type=2
    ):
        self.http = HttpBase(
            api_key=api_key,
            base_url=base_url,
            username=username,
            account_id=account_id,
            endpoints=endpoints,
            logging_enabled=logging_enabled
        )
        self.orders = OrdersService(
            http_base=self.http,
            contract_id=contract_id,
            default_order_type=default_order_type
        )
        self.accounts = AccountsService(http_base=self.http)
        self.flatten_service = FlattenService(
            accounts_service=self.accounts,
            orders_service=self.orders,
            contract_id=contract_id,
            logging_enabled=logging_enabled
        )

    # --- Interface utilisée par l’executor ---
    def execute_trade(self, instrument: str, position: int, size: int = 1):
        # instrument non utilisé par l’API (contractId depuis la config)
        return self.orders.place_order(position=position, size=size)

    def flatten_all(self):
        return self.flatten_service.flatten_all()

    # --- Pass-through utiles ---
    def place_order(self, **kwargs):
        return self.orders.place_order(**kwargs)

    def cancel_order(self, order_id: int):
        return self.orders.cancel_order(order_id)

    def get_open_positions(self):
        return self.accounts.get_open_positions()

    def get_working_orders(self):
        return self.accounts.get_working_orders()
