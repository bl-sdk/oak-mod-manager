def draw(msg: str, indent: int = 0) -> None:
    """
    Draws a message to console for the interactive mod menu.

    Args:
        msg: The message to write.
        indent: How much to indent the message.
    """
    prefix = "Mod Menu | " + ("  " * indent)
    for line in msg.split("\n"):
        print(prefix, line)
