def write(msg: str) -> None:
    """
    Writes a message for the interactive mod menu.

    Args:
        msg: The message to write.
    """
    for line in msg.split("\n"):
        print("Mod Menu |", line)
