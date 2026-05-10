import flet as ft

from components.colors import BLUE_GREY_100, BLUE_700

class TextField(ft.TextField):
    """
    A customized text input field component for Flet applications.

    This component extends the standard Flet TextField with predefined
    styling: underlined border, expanded width, and custom border colors
    for default and focused states. It supports both standard text input
    and password fields with optional reveal toggle.

    Colors are sourced from the centralized color module
    (BLUE_GREY_100, BLUE_700).

    Attributes:
        (Inherited from ft.TextField)
    """
    
    is_focused = False

    def __init__(self, label, password=False, can_reveal_password=False):
        """
        Initializes a TextField with the specified label and behavior.

        Args:
            label (str): The label text displayed above or inside the field.
            password (bool, optional): If True, the field masks input as a
                password field. Defaults to False.
            can_reveal_password (bool, optional): If True and password is True,
                displays a toggle icon to reveal/hide the password. Only
                applicable when password=True. Defaults to False.
        """
        super().__init__()
        self.label = label
        self.password = password
        self.can_reveal_password = can_reveal_password
        self.border_color = BLUE_GREY_100
        self.focused_border_color = BLUE_700
        self.text_size = 14
        self.expand = True
        self.border = ft.InputBorder.UNDERLINE
        self.font_family = "Roboto"
        