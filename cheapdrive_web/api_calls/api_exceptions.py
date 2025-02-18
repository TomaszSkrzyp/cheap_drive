class CoordsFetchError(Exception):
    """
    Exception raised when geographic coordinates cannot be retrieved for a given address.
    
    Example:
        Raises CoordsFetchError("Coordinates could not be retrieved for: 123 Main St")
    """
    def __init__(self, address: str = None):
        self.message = (
            f"Coordinates could not be retrieved for: {address}"
            if address
            else "Coordinates could not be retrieved."
        )
        super().__init__(self.message)


class AddressError(Exception):
    """
    Exception raised when address validation fails (e.g., if the address is invalid or no route is found).
    """
    pass