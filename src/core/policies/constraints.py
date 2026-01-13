class TradingConstraints:
    ALLOW_AUTO_TRADING = False
    ALLOW_REAL_MONEY = False

    @staticmethod
    def validate_action(action: str) -> None:
        action_upper = action.upper()
        if action_upper not in ["CALL", "PUT", "WAIT"]:
            raise ValueError(f"Invalid action: {action}. Only CALL, PUT, or WAIT are allowed.")
