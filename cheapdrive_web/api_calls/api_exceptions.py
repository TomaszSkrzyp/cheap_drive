class CoordsFetchError(Exception):
    """
    Exception raised when geographic coordinates cannot be retrieved for a given address.

    Args:
        address (str, optional): The address for which coordinates could not be retrieved.

    Example:
        try:
            raise CoordsFetchError("123 Main St")
        except CoordsFetchError as e:
            print(e)  # Outputs: Coordinates could not be retrieved for: 123 Main St
    """
    def __init__(self, address: str = None):
        error_message = (
            f"Coordinates could not be retrieved for: {address}"
            if address
            else "Coordinates could not be retrieved."
        )
        super().__init__(error_message) 


class AddressError(Exception):
    """
    Exception raised when address validation fails.

    This occurs when the address is invalid or no route is found.

    Args:
        message (str, optional): Custom error message. Defaults to a generic validation failure message.

    Example:
        try:
            raise AddressError("Invalid address format.")
        except AddressError as e:
            print(e)  # Outputs: Invalid address format.
    """
    def __init__(self, message: str = "Address validation failed."):
        super().__init__(message)
